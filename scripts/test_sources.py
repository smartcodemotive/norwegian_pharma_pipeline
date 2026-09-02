"""Quick probe of TED and Doffin for molecule-related notices."""
from __future__ import annotations

import json
import urllib.request

TED_URL = "https://api.ted.europa.eu/v3/notices/search"


def ted_search(query: str, limit: int = 10) -> dict:
    payload = {
        "query": query,
        "fields": [
            "publication-number",
            "notice-title",
            "buyer-name",
            "publication-date",
            "procedure-type",
            "estimated-value-proc",
            "estimated-value-cur-proc",
            "classification-cpv",
            "notice-type",
            "links",
        ],
        "limit": limit,
        "scope": "ALL",
        "paginationMode": "PAGE_NUMBER",
        "page": 1,
        "onlyLatestVersions": False,
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        TED_URL,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


queries = [
    'FT~"L01EK01" AND buyer-country=NOR',
    'FT~"axitinib"',
    'FT~"Inlyta" AND buyer-country=NOR',
    'FT~"L04AX04" AND buyer-country=NOR',
    'FT~"L01EG02" AND buyer-country=NOR',
    'FT~"L01XX35" AND buyer-country=NOR',
    'FT~"2601c" AND buyer-country=NOR',
    'FT~"2507gj" AND buyer-country=NOR',
]

# Also dump links for one notice
sample = ted_search('FT~"paliperidon" AND buyer-country=NOR', 1)
print("SAMPLE LINKS:", json.dumps(sample.get("notices", [{}])[0], indent=2, ensure_ascii=False)[:4000])

for q in queries:
    try:
        res = ted_search(q, 5)
        print(f"{q!r} -> {res.get('totalNoticeCount', 0)} notices")
        for n in res.get("notices", [])[:2]:
            title = n.get("notice-title", {})
            t = title.get("eng") or title.get("nob") or next(iter(title.values()), "")
            print(f"  {n.get('publication-number')} | {t[:100]}")
    except Exception as exc:
        print(f"{q!r} -> ERROR {exc}")
    print()
