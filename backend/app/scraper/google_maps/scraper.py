from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import AsyncIterator
from urllib.parse import quote_plus

from playwright.async_api import (
    Browser,
    Page,
    async_playwright,
)
from playwright.async_api import (
    TimeoutError as PlaywrightTimeoutError,
)

from app.core.config import Settings, get_settings
from app.scraper.common.models import ScrapedBusiness

PLACE_URL_PATTERN = re.compile(r"https://www\.google\.[^/]+/maps/place/[^\"']+")
PHONE_PATTERN = re.compile(r"(\+?\d[\d\s().-]{6,}\d)")
REVIEW_COUNT_PATTERN = re.compile(r"([\d,]+)\s+reviews?")
RATING_PATTERN = re.compile(r"([0-5](?:\.\d)?)")


class GoogleMapsScraper:
    """Collect business leads from Google Maps using Playwright."""

    def __init__(self, logger: logging.Logger, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._logger = logger

    async def scrape(
        self, *, category: str, city: str, maximum_results: int
    ) -> AsyncIterator[ScrapedBusiness]:
        """Yield Google Maps businesses for a category and city search."""
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True, proxy=self._proxy_settings())
            try:
                context = await browser.new_context(
                    user_agent=self._settings.scraper_user_agent,
                    viewport={"width": 1440, "height": 1100},
                )
                page = await context.new_page()
                place_urls = await self._collect_place_urls(
                    page=page,
                    category=category,
                    city=city,
                    maximum_results=maximum_results,
                )

                semaphore = asyncio.Semaphore(self._settings.scraper_max_concurrency)
                tasks = [
                    self._scrape_with_semaphore(browser, semaphore, url, category, city)
                    for url in place_urls[:maximum_results]
                ]
                for task in asyncio.as_completed(tasks):
                    scraped = await task
                    if scraped is not None:
                        yield scraped
                    await asyncio.sleep(self._settings.scraper_delay_seconds)
            finally:
                await browser.close()

    async def _collect_place_urls(
        self, *, page: Page, category: str, city: str, maximum_results: int
    ) -> list[str]:
        """Collect Google Maps place URLs from search results."""
        query = quote_plus(f"{category} in {city}")
        search_url = f"https://www.google.com/maps/search/{query}"
        self._logger.info("Opening Google Maps search %s", search_url)
        await page.goto(search_url, wait_until="domcontentloaded", timeout=self._timeout_ms)
        await self._accept_google_consent(page)

        urls: list[str] = []
        seen: set[str] = set()
        stagnant_scrolls = 0
        last_count = 0

        while len(urls) < maximum_results and stagnant_scrolls < 8:
            anchors = await page.locator('a[href*="/maps/place/"]').evaluate_all(
                "(elements) => elements.map((element) => element.href)"
            )
            for href in anchors:
                cleaned = str(href).split("&")[0]
                if cleaned not in seen:
                    seen.add(cleaned)
                    urls.append(cleaned)
                    self._logger.info("Found Google Maps place URL %s", cleaned)
                    if len(urls) >= maximum_results:
                        break

            if len(urls) == last_count:
                stagnant_scrolls += 1
            else:
                stagnant_scrolls = 0
                last_count = len(urls)

            feed = page.locator('[role="feed"]').first
            if await feed.count():
                await feed.evaluate("(element) => element.scrollBy(0, element.scrollHeight)")
            else:
                await page.mouse.wheel(0, 1800)
            await asyncio.sleep(self._settings.scraper_delay_seconds)

        return urls[:maximum_results]

    async def _scrape_with_semaphore(
        self,
        browser: Browser,
        semaphore: asyncio.Semaphore,
        url: str,
        fallback_category: str,
        city: str,
    ) -> ScrapedBusiness | None:
        """Scrape one place URL while respecting configured concurrency."""
        async with semaphore:
            for attempt in range(self._settings.scraper_retries + 1):
                try:
                    return await self._scrape_place(browser, url, fallback_category, city)
                except Exception as exc:
                    self._logger.exception("Attempt %s failed for %s: %s", attempt + 1, url, exc)
                    if attempt >= self._settings.scraper_retries:
                        return None
                    await asyncio.sleep(self._settings.scraper_delay_seconds)
            return None

    async def _scrape_place(
        self, browser: Browser, url: str, fallback_category: str, city: str
    ) -> ScrapedBusiness | None:
        """Extract business details from a Google Maps place page."""
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=self._timeout_ms)
            await page.wait_for_selector("h1", timeout=self._timeout_ms)
            name = (await self._text(page, "h1")) or ""
            if not name:
                return None

            category = await self._text(page, 'button[jsaction*="category"]')
            address = await self._aria_text(page, 'button[data-item-id="address"]')
            phone = await self._phone(page)
            website = await self._website(page)
            rating = await self._rating(page)
            review_count = await self._review_count(page)
            hours = await self._business_hours(page)

            return ScrapedBusiness(
                business_name=name,
                category=category or fallback_category,
                phone_number=phone,
                address=address,
                city=city,
                state=None,
                country=None,
                website=website,
                google_maps_url=url,
                rating=rating,
                review_count=review_count,
                business_hours=hours,
            )
        except PlaywrightTimeoutError:
            self._logger.warning("Timed out scraping %s", url)
            return None
        finally:
            await page.close()

    async def _phone(self, page: Page) -> str | None:
        """Extract a phone number from known Maps selectors or page text."""
        phone = await self._aria_text(page, 'button[data-item-id^="phone:tel"]')
        if phone:
            return phone
        text = await page.locator("body").inner_text(timeout=self._timeout_ms)
        match = PHONE_PATTERN.search(text)
        return match.group(1).strip() if match else None

    async def _website(self, page: Page) -> str | None:
        """Extract a website URL if Google Maps exposes one."""
        website = page.locator('a[data-item-id="authority"]').first
        if await website.count():
            href = await website.get_attribute("href")
            if href:
                return href
        return None

    async def _rating(self, page: Page) -> float | None:
        """Extract the visible rating."""
        aria = await self._attribute(page, '[role="img"][aria-label*="stars"]', "aria-label")
        if not aria:
            return None
        match = RATING_PATTERN.search(aria)
        return float(match.group(1)) if match else None

    async def _review_count(self, page: Page) -> int | None:
        """Extract review count."""
        text = await page.locator("body").inner_text(timeout=self._timeout_ms)
        match = REVIEW_COUNT_PATTERN.search(text)
        return int(match.group(1).replace(",", "")) if match else None

    async def _business_hours(self, page: Page) -> str | None:
        """Extract business hours from visible hours controls."""
        text = await self._aria_text(page, '[aria-label*="Hours"]')
        if text:
            return text
        rows = await page.locator("table tr").evaluate_all(
            "(rows) => rows.map((row) => row.innerText).filter(Boolean)"
        )
        return "; ".join(str(row).strip() for row in rows[:7]) if rows else None

    async def _accept_google_consent(self, page: Page) -> None:
        """Accept Google's consent dialog when present."""
        for label in ("Accept all", "I agree"):
            button = page.get_by_role("button", name=label)
            if await button.count():
                await button.first.click(timeout=3000)
                return

    async def _text(self, page: Page, selector: str) -> str | None:
        """Return trimmed visible text for the first matching selector."""
        locator = page.locator(selector).first
        if not await locator.count():
            return None
        text = await locator.inner_text(timeout=self._timeout_ms)
        return text.strip() or None

    async def _aria_text(self, page: Page, selector: str) -> str | None:
        """Return aria-label or text for the first matching selector."""
        locator = page.locator(selector).first
        if not await locator.count():
            return None
        label = await locator.get_attribute("aria-label")
        if label:
            return label.replace("Address:", "").replace("Phone:", "").strip()
        text = await locator.inner_text(timeout=self._timeout_ms)
        return text.strip() or None

    async def _attribute(self, page: Page, selector: str, attribute: str) -> str | None:
        """Return an attribute for the first matching selector."""
        locator = page.locator(selector).first
        if not await locator.count():
            return None
        return await locator.get_attribute(attribute)

    def _proxy_settings(self) -> dict[str, str] | None:
        """Return Playwright proxy settings when configured."""
        if not self._settings.scraper_proxy_url:
            return None
        return {"server": self._settings.scraper_proxy_url}

    @property
    def _timeout_ms(self) -> int:
        """Return configured timeout in milliseconds."""
        return int(self._settings.scraper_timeout_seconds * 1000)
