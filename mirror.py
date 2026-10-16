#!/usr/bin/env python3
"""Recursively mirror same-origin static assets for saudedospes.online."""
from __future__ import annotations

import argparse
import html.parser
import mimetypes
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urldefrag
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ORIGIN = "https://saudedospes.online/"
ROOT = Path(__file__).resolve().parent / "site"
EXTENSIONS = r"(?:js|mjs|css|woff2?|ttf|otf|png|jpe?g|webp|svg|gif|json|mp4|ico|avif|pdf)"
REF = re.compile(r'''["'`(]((?:https?://[^"'`\s)]+|(?:/|\./|\.\./)?[A-Za-z0-9_~@./-]+\.(?:%s)(?:\?[^"'`\s)]*)?))''' % EXTENSIONS, re.I)
CSS_URL = re.compile(r'''url\(\s*["']?([^"')]+)''', re.I)


class Refs(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for key in ("src", "href", "poster"):
            if a.get(key): self.items.append(a[key])
        if a.get("srcset"):
            self.items.extend(x.strip().split()[0] for x in a["srcset"].split(",") if x.strip())


def fetch(url: str) -> tuple[bytes, str]:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; FunnelArchive/1.0)"})
    with urlopen(req, timeout=30) as r:
        final = r.geturl()
        if urlsplit(final).hostname != urlsplit(ORIGIN).hostname:
            raise ValueError(f"cross-origin redirect to {final}")
        return r.read(), r.headers.get_content_type()


def local_path(url: str) -> Path:
    p = urlsplit(url).path
    if not p or p.endswith("/"): p += "index.html"
    return ROOT / p.lstrip("/")


def discover(data: bytes, mime: str, current_url: str) -> set[str]:
    text = data.decode("utf-8", "ignore")
    refs: list[str] = []
    if "html" in mime or text.lstrip().lower().startswith("<!doctype html"):
        parser = Refs(); parser.feed(text); refs.extend(parser.items)
    refs.extend(REF.findall(text))
    if "css" in mime or current_url.lower().endswith(".css"):
        refs.extend(CSS_URL.findall(text))
    found = set()
    for ref in refs:
        ref = ref.strip().replace("\\/", "/")
        if not ref or ref.startswith(("data:", "blob:", "#", "mailto:", "javascript:")):
            continue
        absolute = urldefrag(urljoin(current_url, ref))[0]
        u = urlsplit(absolute)
        if u.scheme in ("http", "https") and u.hostname == urlsplit(ORIGIN).hostname:
            if re.search(r"\.(?:" + EXTENSIONS + r")$", u.path, re.I) or u.path in ("/~flock.js",):
                found.add(absolute)
    return found


def main():
    global ROOT
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path)
    ap.add_argument("--refresh", action="store_true", help="redownload files already present")
    args = ap.parse_args()
    ROOT = (args.root or ROOT).resolve()
    ROOT.mkdir(parents=True, exist_ok=True)
    queue = [ORIGIN]
    seen: set[str] = set()
    failures = []
    missing_404 = []
    while queue:
        url = queue.pop(0)
        if url in seen: continue
        seen.add(url)
        target = local_path(url)
        try:
            if target.exists() and not args.refresh:
                data = target.read_bytes()
                mime = mimetypes.guess_type(target.name)[0] or ("text/html" if target.name == "index.html" else "application/octet-stream")
            else:
                data, mime = fetch(url)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                print(f"GET {url} [{len(data)} bytes]")
            for ref in discover(data, mime, url):
                if ref not in seen: queue.append(ref)
        except HTTPError as e:
            if e.code == 404:
                missing_404.append(url)
                print(f"MISS 404 {url}")
            else:
                failures.append((url, str(e)))
                print(f"FAIL {url}: {e}")
        except Exception as e:
            failures.append((url, str(e)))
            print(f"FAIL {url}: {e}")
        time.sleep(.03)
    print(f"\nFetched/visited: {len(seen)}; HTTP 404 refs: {len(missing_404)}; other failures: {len(failures)}; root: {ROOT}")
    if missing_404:
        (ROOT.parent / "confirmed-404.txt").write_text("\n".join(missing_404) + "\n", encoding="utf-8")
    if failures: raise SystemExit(1)


if __name__ == "__main__":
    main()
