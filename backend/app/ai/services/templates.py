from __future__ import annotations

import json
from pathlib import Path

from app.models.business import Business

TEMPLATE_NAMES = [
    "salon",
    "clinic",
    "lawyer",
    "coaching",
    "boutique",
    "restaurant",
    "gym",
    "spa",
    "dental_clinic",
    "real_estate",
]


class TemplateEngine:
    """Reusable demo website template engine."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or Path("templates")

    def list_templates(self) -> list[str]:
        """Return available template names."""
        return TEMPLATE_NAMES

    def config_for(
        self, template: str, business: Business, generated: dict[str, object]
    ) -> dict[str, object]:
        """Build template configuration by injecting CRM and AI-generated data."""
        base = self._load_config(template)
        base.update(
            {
                "businessName": business.business_name,
                "phone": business.phone_number or "",
                "address": business.address or "",
                "category": business.category or template.replace("_", " ").title(),
                "businessHours": _extract_hours(business.notes),
                "googleMapsUrl": business.google_maps_url or "",
                "whatsapp": _whatsapp_url(business.phone_number),
                "primaryColor": base.get("primaryColor") or "#0f766e",
                "secondaryColor": base.get("secondaryColor") or "#f59e0b",
            }
        )
        base.update(generated)
        return base

    def render(self, config: dict[str, object]) -> str:
        """Render a static demo website."""
        services = "".join(f"<li>{service}</li>" for service in config.get("services", []))
        faqs = "".join(f"<li>{faq}</li>" for faq in config.get("faq", []))
        testimonials = "".join(
            f"<blockquote>{item}</blockquote>" for item in config.get("testimonials", [])
        )
        cta = config.get("cta", "Book a consultation")
        whatsapp = config.get("whatsapp", "#")
        contact = f"<p>{config.get('phone', '')}</p><p>{config.get('address', '')}</p>"
        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{config.get("seoTitle", config["businessName"])}</title>
  <meta name="description" content="{config.get("seoDescription", "")}" />
  <meta name="keywords" content="{config.get("metaKeywords", "")}" />
  <style>
    body {{ margin:0; font-family:Arial,sans-serif; color:#1f2937; background:#f8fafc; }}
    header {{ background:{config["primaryColor"]}; color:white; padding:48px 7vw; }}
    section {{ padding:36px 7vw; }}
    .cta {{ background:{config["secondaryColor"]}; color:#111827; padding:14px 18px; }}
    .cta {{ border-radius:8px; display:inline-block; text-decoration:none; font-weight:700; }}
    .grid {{ display:grid; gap:18px; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); }}
    .card {{ background:white; border:1px solid #e5e7eb; border-radius:8px; padding:20px; }}
  </style>
</head>
<body>
  <header>
    <p>{config.get("category", "")}</p>
    <h1>{config.get("heroHeadline", config["businessName"])}</h1>
    <p>{config.get("about", "")}</p>
    <a class="cta" href="{whatsapp}">{cta}</a>
  </header>
  <section><h2>Services</h2><div class="card"><ul>{services}</ul></div></section>
  <section class="grid">
    <div class="card"><h2>About</h2><p>{config.get("about", "")}</p></div>
    <div class="card"><h2>Contact</h2>{contact}</div>
  </section>
  <section><h2>Sample Testimonials</h2><p>Sample content for client review.</p>
  {testimonials}</section>
  <section><h2>FAQ</h2><ul>{faqs}</ul></section>
</body>
</html>"""

    def _load_config(self, template: str) -> dict[str, object]:
        path = self._root / template / "config.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {
            "businessName": "",
            "phone": "",
            "address": "",
            "primaryColor": "",
            "secondaryColor": "",
            "services": [],
            "gallery": [],
            "about": "",
            "cta": "",
            "logo": "",
        }


def _whatsapp_url(phone: str | None) -> str:
    digits = "".join(character for character in (phone or "") if character.isdigit())
    return f"https://wa.me/{digits}" if digits else "#"


def _extract_hours(notes: str | None) -> str:
    if not notes or "Business hours:" not in notes:
        return "Hours to be confirmed by client."
    return notes.split("Business hours:", 1)[1].strip()
