#!/usr/bin/env python3
"""Serve the mirrored site with SPA route fallback and a diagnostic header."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
import os


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("X-Funnel-Mirror", "saudedospes-local-v1")
        super().end_headers()

    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isfile(path):
            return super().send_head()
        # Missing files with an extension remain 404; client-side routes fall back.
        if Path(self.path.split("?", 1)[0]).suffix:
            self.send_error(404, "Asset not found")
            return None
        self.path = "/index.html"
        return super().send_head()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--directory", default=str(Path(__file__).resolve().parent / "site"))
    a = ap.parse_args()
    os.chdir(a.directory)
    print(f"Serving {a.directory} at http://{a.host}:{a.port} (X-Funnel-Mirror)")
    ThreadingHTTPServer((a.host, a.port), Handler).serve_forever()


if __name__ == "__main__": main()
