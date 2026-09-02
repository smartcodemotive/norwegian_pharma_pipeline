"""Probe Mercell document availability for LIS tenders."""
from __future__ import annotations

import re
import urllib.request
from pathlib import Path

PAGES = [
    "https://www.mercell.com/nb-no/anbud/176511702/lis-2207-onkologi-anbud.aspx",
    "https://www.mercell.com/en/tender/191826142/intensjonskunngjoering--tilleggsavtaler-til-lis-2301d-ureg-atc-koder-j05af01-n05ax13-n05cd08-p01cx04-s01ax18-s01ee09-og-v03ab13-tender.aspx",
]

OUT = Path("data/cache/mercell")


def fetch(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "NorwegianPharmaPipeline/1.0 (academic assessment)",
            "Accept-Language": "nb-NO,en;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        return resp.read().decode("utf-8", errors="replace")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for url in PAGES:
        slug = url.split("/")[-1].replace(".aspx", "")[:60]
        print(f"\n=== {slug} ===")
        try:
            html = fetch(url)
        except Exception as exc:
            print(f"FETCH FAILED: {exc}")
            continue
        (OUT / f"{slug}.html").write_text(html, encoding="utf-8")
        print(f"Saved HTML ({len(html)} chars)")
        for pattern in [
            r'href="([^"]+\.xlsx[^"]*)"',
            r'href="([^"]+\.pdf[^"]*)"',
            r"GetFile\.ashx\?[^\"']+",
            r"/file/[^\"']+",
        ]:
            hits = re.findall(pattern, html, flags=re.I)
            if hits:
                print(f"  {pattern}: {hits[:5]}")


if __name__ == "__main__":
    main()
