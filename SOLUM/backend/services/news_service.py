import asyncio
import re
import html
import hashlib
import json
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import urlencode
import xml.etree.ElementTree as ET
import httpx
from backend.services.weather_service import get_cached, set_cached

USER_AGENT = "SOLUM-Disaster-Awareness/1.0"

def strip_html(text: str) -> str:
    if not text:
        return ""
    clean = re.sub(r"<[^>]*>", "", text)
    return re.sub(r"\s+", " ", html.unescape(clean)).strip()

def select_news_image(title: str, text: str = "") -> tuple:
    t = f"{title} {text}".lower()
    if any(k in t for k in ["lake", "wetland", "waterbod", "river", "water body", "reservoir", "tank", "ennore", "pallikaranai", "vaigai", "cauvery"]):
        return "assets/images/news/waterbody-restoration.svg", "Illustrative: Wetland & waterbody conservation"
    elif any(k in t for k in ["drain", "pump", "stormwater", "culvert", "waterlog", "inundat", "overflow", "desilt"]):
        return "assets/images/news/stormwater-drainage.svg", "Illustrative: Stormwater drainage & pumping unit"
    elif any(k in t for k in ["cyclone", "sea", "surge", "coastal", "coast", "tide", "beach", "kanyakumari", "cuddalore", "bay of bengal"]):
        return "assets/images/news/coastal-resilience.svg", "Illustrative: Coastal surge & seawall defence"
    elif any(k in t for k in ["landslide", "landslip", "hill", "ghat", "slope", "ooty", "nilgiri", "kodaikanal", "debris"]):
        return "assets/images/news/hill-slope.svg", "Illustrative: Western Ghats slope stability"
    elif any(k in t for k in ["power", "electric", "substation", "grid", "wire", "tangedco", "blackout", "feeder"]):
        return "assets/images/news/power-grid.svg", "Illustrative: Power grid & substation resilience"
    elif any(k in t for k in ["radar", "imd", "rain", "monsoon", "forecast", "alert", "weather", "downpour", "cyclonic"]):
        return "assets/images/news/monsoon-radar.svg", "Illustrative: IMD Doppler radar & monsoon track"
    else:
        return "assets/images/news/urban-planning.svg", "Illustrative: Urban planning & land resilience"

def parse_news_xml(raw_xml: str, region: str, provider: str) -> list:
    try:
        root = ET.fromstring(raw_xml)
    except Exception:
        return []
    
    now = datetime.now(timezone.utc)
    items = []

    for item in root.findall(".//item"):
        title = strip_html(item.findtext("title"))
        link = (item.findtext("link") or "").strip()
        if not title or not link.startswith("https://"):
            continue

        date_string = item.findtext("pubDate")
        try:
            dt = parsedate_to_datetime(date_string)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except Exception:
            continue

        # Keep articles from last 7 days only
        if dt < now - timedelta(days=7) or dt > now + timedelta(hours=1):
            continue

        raw_desc = strip_html(item.findtext("description"))
        if provider == "GDACS":
            country = next((e.text for e in item if e.tag.endswith("country")), "") or ""
            haystack = f"{title} {country} {raw_desc}".lower()
            if region.lower() not in haystack:
                continue

        source = item.find("source")
        publisher = strip_html(source.text if source is not None else provider)
        if publisher and title.endswith(f" - {publisher}"):
            title = title[:-(len(publisher) + 3)]

        is_breaking = "breaking" in title.lower() and (now - dt < timedelta(hours=12))
        img_url, img_caption = select_news_image(title, raw_desc)

        items.append({
            "title": title[:300],
            "publisher": publisher or provider,
            "url": link,
            "published": dt.isoformat(),
            "kind": "BREAKING" if is_breaking else "LATEST COVERAGE",
            "summary": raw_desc[:240] + ("…" if len(raw_desc) > 240 else "") if len(raw_desc) > 20 else "Open source report for verified field context. Confirm local action with official advisories.",
            "image_url": img_url,
            "image_caption": img_caption
        })

    return items

async def fetch_feed(client: httpx.AsyncClient, url: str) -> str:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml, text/xml"}
    resp = await client.get(url, headers=headers, timeout=9.0)
    resp.raise_for_status()
    return resp.text

async def get_news(region: str, scope: str = "district") -> dict:
    cache_key = f"news_{region.lower().strip()}_{scope}"
    cached_val = get_cached(cache_key, ttl=900) # 15 minutes
    if cached_val:
        return cached_val

    query = f"{region} (flood OR cyclone OR landslide OR earthquake OR heavy rain OR disaster OR weather) when:7d"
    google_url = "https://news.google.com/rss/search?" + urlencode({
        "q": query, "hl": "en-IN", "gl": "IN", "ceid": "IN:en"
    })
    gdacs_url = "https://www.gdacs.org/xml/rss.xml"

    results = []
    warnings = []

    async with httpx.AsyncClient() as client:
        t1 = fetch_feed(client, google_url)
        t2 = fetch_feed(client, gdacs_url)
        feeds = await asyncio.gather(t1, t2, return_exceptions=True)

    if isinstance(feeds[0], str):
        results.extend(parse_news_xml(feeds[0], region, "Google News / linked publishers"))
    else:
        warnings.append("Google News feed unavailable")

    if isinstance(feeds[1], str):
        results.extend(parse_news_xml(feeds[1], region, "GDACS"))
    else:
        warnings.append("GDACS feed unavailable")

    seen = set()
    deduped = []
    for item in sorted(results, key=lambda x: x["published"], reverse=True):
        k = item["title"].lower().strip()
        if k not in seen:
            seen.add(k)
            deduped.append(item)

    if not deduped:
        # Fallback evergreen items
        deduped = [
            {
                "title": "Stay informed before weather changes.",
                "summary": "Open official bulletins for current warnings. Live news is quiet or connecting; review local preparedness resources.",
                "publisher": "IMD Regional Centre",
                "url": "https://mausam.imd.gov.in/chennai/",
                "kind": "SOURCE DIRECTORY",
                "published": None,
                "image_url": "assets/images/news/monsoon-radar.svg",
                "image_caption": "Illustrative: IMD Doppler radar & monsoon forecast tracking"
            },
            {
                "title": "A ready household starts with a simple plan.",
                "summary": "Review official flood preparedness guidance and agree on an emergency contact.",
                "publisher": "IMD · Preparedness",
                "url": "https://mausam.imd.gov.in/chennai/mcdata/dos%26donts.pdf",
                "kind": "PREPAREDNESS RESOURCE",
                "published": None,
                "image_url": "assets/images/news/stormwater-drainage.svg",
                "image_caption": "Illustrative: Municipal stormwater & community preparedness"
            },
            {
                "title": "Restoration of urban waterbodies and wetland buffers.",
                "summary": "Community-led and civic conservation protects natural retention basins and minimizes downstream waterlogging.",
                "publisher": "Tamil Nadu Water Resources Department",
                "url": "https://chennaicorporation.gov.in/",
                "kind": "CIVIC INITIATIVE",
                "published": None,
                "image_url": "assets/images/news/waterbody-restoration.svg",
                "image_caption": "Illustrative: Wetland & waterbody conservation"
            }
        ]

    data = {
        "items": deduped[:8],
        "region": region,
        "scope": scope,
        "warnings": warnings,
        "coverage_note": "Keyword-matched coverage, not exhaustive or an official warning feed.",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "receipt_sha256": hashlib.sha256(json.dumps(deduped[:8], sort_keys=True).encode()).hexdigest(),
        "cached": False
    }

    set_cached(cache_key, data)
    return data
