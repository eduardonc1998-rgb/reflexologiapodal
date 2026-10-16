#!/usr/bin/env python3
"""Compare local-file references in mirrored HTML, JS, CSS and source maps."""
from pathlib import Path
from urllib.parse import urlsplit
from urllib.parse import urlsplit
import re
import sys

ROOT = Path(__file__).resolve().parent / "site"
EXT = r"(?:js|mjs|css|woff2?|ttf|otf|png|jpe?g|webp|svg|gif|json|mp4|ico|avif|pdf)"
PATTERNS = [
    re.compile(r'''["'`(]((?:/|\./|\.\./)[A-Za-z0-9_~@./-]+\.(?:%s)(?:\?[^"'`\s)]*)?)''' % EXT, re.I),
    re.compile(r'''["'`]((?:assets|img|__l5e/assets-v1)/[A-Za-z0-9_~@./-]+\.(?:%s)(?:\?[^"'`\s)]*)?)''' % EXT, re.I),
]

def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT
    refs: set[str] = set()
    confirmed_404 = set()
    status_file = root.parent / "confirmed-404.txt"
    if status_file.exists():
        for line in status_file.read_text(encoding="utf-8").splitlines():
            if line.strip(): confirmed_404.add(urlsplit(line.strip()).path)
    scanned = 0
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in (".html", ".js", ".mjs", ".css", ".map", ".json"):
            continue
        scanned += 1
        text = p.read_text(encoding="utf-8", errors="ignore")
        for rx in PATTERNS:
            refs.update(x.split("?", 1)[0] for x in rx.findall(text))
    present, missing, non_assets = [], [], []
    for ref in sorted(refs):
        if ref.split("?", 1)[0] in confirmed_404:
            non_assets.append(ref)
            continue
        path = ref.lstrip("/")
        # Resolve relative imports from the directory of the referring bundle.
        candidates = [root / path]
        if ref.startswith(("./", "../")):
            for source in root.rglob("*"):
                if source.is_file() and source.suffix.lower() in (".js", ".mjs", ".css"):
                    cand = (source.parent / ref).resolve()
                    if cand.is_relative_to(root): candidates.append(cand)
        (present if any(c.is_file() for c in candidates) else missing).append(ref)
    print(f"Ficheiros de código analisados: {scanned}")
    print(f"Referências locais distintas: {len(refs)}")
    print(f"Presentes em disco: {len(present)}")
    print(f"Referências confirmadas como 404 no servidor (não são assets existentes): {len(non_assets)}")
    print(f"Ficheiros existentes em falta no disco: {len(missing)}")
    for ref in missing: print("  " + ref)
    return 1 if missing else 0

if __name__ == "__main__": raise SystemExit(main())
