#!/usr/bin/env python3
"""Generate static, Google-readable event pages from the public events API."""
import datetime
import html
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

API = "https://boletos-menopausia-dichosa.menopausiadichosa.chatgpt.site/api/events"
ROOT = "https://menopausiadichosa.com"
OUT = Path("eventos")
def esc(v):
    return html.escape(str(v or ""), quote=True)
def main():
    req = Request(API, headers={"User-Agent": "MenopausiaDichosaEventPages/1.0"})
    with urlopen(req, timeout=25) as response:
        events = json.load(response)
    if not isinstance(events, list):
        raise ValueError("Events API did not return a list")
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-5))).date().isoformat()
    count = 0
    for e in events:
        if not isinstance(e, dict) or not e.get("active") or not e.get("id") or not e.get("title"):
            continue
        date, time = str(e.get("date", "")), str(e.get("time", ""))
        if date < today or len(date) != 10 or len(time) not in (4,5) or ":" not in time:
            continue
        try:
            start = datetime.datetime.strptime(date + " " + time, "%Y-%m-%d %H:%M")
        except ValueError:
            continue
        event_id = str(e["id"])
        if not all(c.isalnum() or c == "-" for c in event_id):
            continue
        url = ROOT + "/eventos/" + event_id + "/"
        booking = ROOT + "/boletos/?evento=" + event_id
        online = bool(e.get("online"))
        place = str(e.get("place") or "")
        if not online and not place:
            continue
        schema = {"@context":"https://schema.org","@type":"Event","name":str(e["title"]),
                  "startDate":start.strftime("%Y-%m-%dT%H:%M:%S-05:00"),
                  "eventStatus":"https://schema.org/EventScheduled",
                  "eventAttendanceMode":"https://schema.org/OnlineEventAttendanceMode" if online else "https://schema.org/OfflineEventAttendanceMode",
                  "location":{"@type":"VirtualLocation","url":booking} if online else {"@type":"Place","name":place,"address":{"@type":"PostalAddress","addressLocality":"Cancún","addressRegion":"Quintana Roo","addressCountry":"MX"}},
                  "organizer":{"@type":"Organization","name":"Menopausia Dichosa™","url":ROOT+"/"},"url":url}
        if e.get("description"):
            schema["description"] = str(e["description"])
        if e.get("image_key"):
            schema["image"] = API + "/" + event_id + "/image"
        if isinstance(e.get("price_cents"), int) and e["price_cents"] >= 0:
            schema["offers"] = {"@type":"Offer","url":booking,"price":f"{e['price_cents']/100:.2f}","priceCurrency":"MXN",
                                "availability":"https://schema.org/InStock" if e.get("available",0)>0 else "https://schema.org/SoldOut"}
        title, desc = esc(e["title"]), esc(e.get("description") or "Sesión educativa de Menopausia Dichosa™")
        ld = json.dumps(schema, ensure_ascii=False).replace("<", "\\u003c")
        image = f'<img style="max-width:100%;border-radius:12px" src="{esc(API+"/"+event_id+"/image")}" alt="{title}">' if e.get("image_key") else ""
        body = f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} | Menopausia Dichosa™</title><meta name="description" content="{desc[:155]}"><link rel="canonical" href="{url}"><script type="application/ld+json">{ld}</script><style>body{{background:#fff8fa;color:#33232c;font:17px/1.6 Arial,sans-serif}}main{{max-width:700px;margin:30px auto;padding:24px}}h1{{color:#880e3d}}a.btn{{display:inline-block;background:#c90057;color:white;padding:13px 24px;border-radius:9px;text-decoration:none}}</style></head><body><main>{image}<h1>{title}</h1><p>{esc(date)} · {esc(time)} h · {esc("En línea" if online else place)}</p><p>{desc}</p><p><a class="btn" href="{esc(booking)}">Ver detalles y reservar</a></p><p><a href="/#eventos">Ver todos los eventos</a></p></main></body></html>'''
        target = OUT / event_id / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        count += 1
    print(f"Generated {count} event pages")
if __name__ == "__main__":
    main()
