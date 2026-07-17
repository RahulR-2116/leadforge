from __future__ import annotations

from urllib.parse import urlparse

IGNORED_WEBSITE_DOMAINS = {
    "facebook.com",
    "fb.com",
    "instagram.com",
    "youtube.com",
    "youtu.be",
    "linkedin.com",
    "google.com",
    "google.co.in",
    "goo.gl",
    "g.page",
    "maps.app.goo.gl",
    "justdial.com",
}


def detect_official_website(url: str | None) -> str | None:
    """Return a normalized official website URL or None for ignored/listing URLs."""
    if not url:
        return None

    normalized_url = _ensure_scheme(url.strip())
    parsed = urlparse(normalized_url)
    host = _normalize_host(parsed.netloc)

    if not host or _is_ignored_domain(host):
        return None

    return normalized_url


def has_official_website(url: str | None) -> bool:
    """Return whether a URL points to an official business website."""
    return detect_official_website(url) is not None


def _ensure_scheme(url: str) -> str:
    """Add an HTTPS scheme when a scraper returns a bare domain."""
    if url.startswith(("http://", "https://")):
        return url
    return f"https://{url}"


def _normalize_host(host: str) -> str:
    """Normalize a URL host for domain checks."""
    lowered = host.lower().split("@")[-1].split(":")[0]
    return lowered.removeprefix("www.")


def _is_ignored_domain(host: str) -> bool:
    """Return whether the host is a social media, maps, or listing platform."""
    return any(host == domain or host.endswith(f".{domain}") for domain in IGNORED_WEBSITE_DOMAINS)
