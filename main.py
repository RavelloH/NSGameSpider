"""Archive recently released Nintendo Switch covers from Nintendo Hong Kong."""
import argparse
import datetime as dt
import re
import unicodedata
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

SOURCE = "https://www.nintendo.com/hk/schedule"
HK = dt.timezone(dt.timedelta(hours=8))
IMAGE_HOSTS = {"images.ctfassets.net"}

def fetch(url, max_bytes):
    request = Request(url, headers={"User-Agent": "NSGameSpider/2.0"})
    with urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"Unexpected HTTP {response.status}: {url}")
        data = response.read(max_bytes + 1)
        if not data or len(data) > max_bytes:
            raise RuntimeError(f"Invalid response size: {url}")
        return data

def filename(title):
    value = unicodedata.normalize("NFC", title)
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip(" .")
    value = value.encode("utf-8")[:220].decode("utf-8", errors="ignore").rstrip(" .")
    return value + ".jpg" if value else None

def jpeg_url(url):
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname not in IMAGE_HOSTS:
        return None
    query = dict(parse_qsl(parts.query))
    query["fm"] = "jpg"
    return urlunsplit(parts._replace(query=urlencode(query)))

def parse_schedule(data, today):
    soup = BeautifulSoup(data, "html.parser")
    current = None
    cards = {}
    for element in soup.select(".local-schedule__dayFull, .local-schedule__listContent"):
        if "local-schedule__dayFull" in element.get("class", []):
            match = re.match(r"(\d{4})\.(\d{1,2})\.(\d{1,2})", element.get_text(strip=True))
            current = dt.date(*map(int, match.groups())) if match else None
            continue
        if current is None or not today - dt.timedelta(days=30) <= current <= today:
            continue
        if element.get("data-theme") != "switch":
            continue
        title = element.select_one(".local-schedule__listTitle strong")
        image = element.select_one(".local-schedule__listThum")
        if title is None or image is None:
            continue
        style = image.get("style", "")
        raw_url = style.split("url(", 1)[1].split(")", 1)[0] if "url(" in style else ""
        name = filename(title.get_text(" ", strip=True))
        url = jpeg_url(raw_url.strip("'\x22")) if raw_url else None
        if name and url:
            cards[name] = (current, url)
    if not cards:
        raise RuntimeError("No released Switch covers found; source or layout may have changed")
    return sorted(cards.items(), key=lambda item: item[1][0], reverse=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=80)
    parser.add_argument("--output", type=Path, default=Path("img"))
    args = parser.parse_args()
    if args.limit <= 0:
        parser.error("--limit must be positive")
    today = dt.datetime.now(HK).date()
    cards = parse_schedule(fetch(SOURCE, 8 * 1024 * 1024), today)
    missing = [(name, url) for name, (_, url) in cards if not (args.output / name).is_file()]
    print(f"Found {len(cards)} released Switch covers; {len(missing)} new")
    if args.dry_run:
        return
    args.output.mkdir(parents=True, exist_ok=True)
    for name, url in missing[:args.limit]:
        data = fetch(url, 8 * 1024 * 1024)
        if not data.startswith(b"\xff\xd8\xff"):
            raise RuntimeError(f"Invalid JPEG: {name}")
        path = args.output / name
        temp = path.with_suffix(".jpg.tmp")
        temp.write_bytes(data)
        temp.replace(path)
    print(f"Archived {min(len(missing), args.limit)} new covers")

if __name__ == "__main__":
    main()
