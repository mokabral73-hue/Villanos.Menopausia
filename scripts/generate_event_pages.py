#!/usr/bin/env python3
"""Generate static, Google-readable event pages from the public events API."""
import datetime
import html
import json
from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

API = "https://boletos-menopausia-dichosa.menopausiadichosa.chatgpt.site/api/events"
ROOT = "https://menopausiadichosa.com"
OUT = Path("eventos")
TZ = datetime.timezone(datetime.timedelta(hours=-5))


def esc(value):
    return html.escape(str(value or ""), quote=True)


def first_value(event, *keys):
    for key in keys:
        value = event.get(key)
        if value not in (None, ""):
            return value
    return None


def iso_local(date_value, time_value):
    if not date_value or not time_value:
        return None
    try:
        parsed = datetime.datetime.strptime(
            f"{str(date_value)[:10]} {str(time_value)[:5]}", "%Y-%m-%d %H:%M"
        ).replace(tzinfo=TZ)
    except ValueError:
        return None
    return parsed.isoformat()


def optional_end_date(event, event_date):
    end_date = first_value(event, "end_date", "endDate") or event_date
    end_time = first_value(event, "end_time", "endTime")
    return iso_local(end_date, end_time)


def optional_valid_from(event):
    raw = first_value(
        event,
        "valid_from",
        "validFrom",
        "registration_opened_at",
        "registrationOpenedAt",
        "created_at",
        "createdAt",
    )
    if not raw:
        return None
    text = str(raw).strip()
    if "T" in text:
        return text
    if len(text) >= 10:
        return f"{text[:10]}T00:00:00-05:00"
    return None


def optional_performer(event):
    name = first_value(event, "performer", "speaker", "presenter", "facilitator")
    if not name:
        return None
    return {"@type": "Person", "name": str(name)}


def main():
    req = Request(API, headers={"User-Agent": "MenopausiaDichosaEventPages/2.0"})
    with urlopen(req, timeout=25) as response:
        events = json.load(response)
    if not isinstance(events, list):
        raise ValueError("Events API did not return a list")

    today = datetime.datetime.now(TZ).date().isoformat()
    count = 0
    current_event_ids = []

    for event in events:
        if (
            not isinstance(event, dict)
            or not event.get("active")
            or not event.get("id")
            or not event.get("title")
        ):
            continue

        date_value = str(event.get("date", ""))
        time_value = str(event.get("time", ""))
        start_date = iso_local(date_value, time_value)
        if date_value < today or not start_date:
            continue

        event_id = str(event["id"])
        if not all(char.isalnum() or char == "-" for char in event_id):
            continue

        page_url = f"{ROOT}/eventos/{event_id}/"
        booking_url = f"{ROOT}/boletos/?evento={event_id}"
        online = bool(event.get("online"))
        place = str(event.get("place") or "")
        address = str(event.get("address") or "")
        location_url = str(event.get("location_url") or event.get("locationUrl") or "")

        if not online and not place:
            continue

        if online:
            location = {
                "@type": "VirtualLocation",
                "url": location_url or booking_url,
            }
        else:
            postal_address = {
                "@type": "PostalAddress",
                "addressLocality": str(
                    first_value(event, "city", "addressLocality") or "Cancún"
                ),
                "addressRegion": str(
                    first_value(event, "region", "state", "addressRegion")
                    or "Quintana Roo"
                ),
                "addressCountry": str(
                    first_value(event, "country", "addressCountry") or "MX"
                ),
            }
            if address and address.lower() != "evento en línea":
                postal_address["streetAddress"] = address
            location = {"@type": "Place", "name": place, "address": postal_address}

        schema = {
            "@context": "https://schema.org",
            "@type": "Event",
            "name": str(event["title"]),
            "startDate": start_date,
            "eventStatus": "https://schema.org/EventScheduled",
            "eventAttendanceMode": (
                "https://schema.org/OnlineEventAttendanceMode"
                if online
                else "https://schema.org/OfflineEventAttendanceMode"
            ),
            "location": location,
            "organizer": {
                "@type": "Organization",
                "name": "Menopausia Dichosa™",
                "url": ROOT + "/",
            },
            "url": page_url,
        }

        end_date = optional_end_date(event, date_value)
        if end_date:
            schema["endDate"] = end_date

        performer = optional_performer(event)
        if performer:
            schema["performer"] = performer

        if event.get("description"):
            schema["description"] = str(event["description"])

        image_url = None
        if event.get("image_key"):
            image_url = f"{API}/{event_id}/image"
            schema["image"] = image_url

        if isinstance(event.get("price_cents"), int) and event["price_cents"] >= 0:
            offer = {
                "@type": "Offer",
                "url": booking_url,
                "price": f"{event['price_cents'] / 100:.2f}",
                "priceCurrency": "MXN",
                "availability": (
                    "https://schema.org/InStock"
                    if event.get("available", 0) > 0
                    else "https://schema.org/SoldOut"
                ),
            }
            valid_from = optional_valid_from(event)
            if valid_from:
                offer["validFrom"] = valid_from
            schema["offers"] = offer

        title = esc(event["title"])
        description_text = str(
            event.get("description") or "Sesión educativa de Menopausia Dichosa™"
        )
        description = esc(description_text)
        meta_desc = esc(" ".join(description_text.split())[:155])
        ld = json.dumps(schema, ensure_ascii=False).replace("<", "\\u003c")

        social_image = image_url or f"{ROOT}/compartir-portada.jpg"
        image_html = (
            f'<img style="max-width:100%;border-radius:12px" '
            f'src="{esc(image_url)}" alt="{title}">'
            if image_url
            else ""
        )

        body = f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="index,follow,max-image-preview:large"><title>{title} | Menopausia Dichosa™</title><meta name="description" content="{meta_desc}"><link rel="canonical" href="{page_url}"><meta property="og:type" content="website"><meta property="og:title" content="{title} | Menopausia Dichosa™"><meta property="og:description" content="{meta_desc}"><meta property="og:url" content="{page_url}"><meta property="og:image" content="{esc(social_image)}"><meta name="twitter:card" content="summary_large_image"><script type="application/ld+json">{ld}</script><style>body{{background:#fff8fa;color:#33232c;font:17px/1.6 Arial,sans-serif}}main{{max-width:700px;margin:30px auto;padding:24px}}h1{{color:#880e3d}}a.btn{{display:inline-block;background:#c90057;color:white;padding:13px 24px;border-radius:9px;text-decoration:none}}</style></head><body><main>{image_html}<h1>{title}</h1><p>{esc(date_value)} · {esc(time_value)} h · {esc("En línea" if online else place)}</p><p>{description}</p><p><a class="btn" href="{esc(booking_url)}">Ver detalles y reservar</a></p><p><a href="/#eventos">Ver todos los eventos</a></p></main></body></html>'''

        target = OUT / event_id / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        current_event_ids.append(event_id)
        count += 1

    # Sitemap: include only evergreen pages and events that are active and upcoming now.
    urls = [
        ROOT + "/",
        ROOT + "/metodo/",
        ROOT + "/menopausia-en-cancun/",
        ROOT + "/guia/",
        ROOT + "/test/",
    ]
    urls.extend(f"{ROOT}/eventos/{event_id}/" for event_id in sorted(current_event_ids))

    root = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    today_iso = datetime.datetime.now(TZ).date().isoformat()
    for url in urls:
        node = ET.SubElement(root, "url")
        ET.SubElement(node, "loc").text = url
        ET.SubElement(node, "lastmod").text = today_iso
    ET.ElementTree(root).write("sitemap.xml", encoding="utf-8", xml_declaration=True)

    print(f"Generated {count} event pages and sitemap with {len(urls)} URLs")


if __name__ == "__main__":
    main()
