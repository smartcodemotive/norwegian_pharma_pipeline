"""Probe TED API extended fields."""
from __future__ import annotations

import json
import urllib.request

TED = "https://api.ted.europa.eu/v3/notices/search"

FIELDS = [
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
    "description-lot",
    "description-proc",
    "tender-value",
    "result-value",
    "winner-name",
    "contract-title",
    "place-of-performance",
    "title-lot",
    "title-proc",
    "identifier-proc",
    "deadline-receipt-tender-date-lot",
    "contract-duration-start-date-lot",
    "contract-duration-end-date-lot",
    "organisation-name-buyer",
    "organisation-city-buyer",
    "organisation-country-buyer",
]

QUERIES = [
    'FT~"paliperidon" AND buyer-country=NOR',
    'FT~"lenalidomid" AND buyer-country=NOR',
    'FT~"everolimus" AND buyer-country=NOR',
    'FT~"anagrelid" AND buyer-country=NOR',
    'FT~"axitinib" AND buyer-country=NOR',
    'FT~"LIS 2601" AND buyer-country=NOR',
    'FT~"LIS 2507" AND buyer-country=NOR',
    'FT~"LIS 2301" AND buyer-country=NOR',
]


def search(query: str, limit: int = 20) -> dict:
    payload = {
        "query": query,
        "fields": FIELDS,
        "limit": limit,
        "scope": "ALL",
        "paginationMode": "ITERATION",
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        TED,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


if __name__ == "__main__":
    all_notices: list[dict] = []
    for query in QUERIES:
        result = search(query, limit=20)
        count = result.get("totalNoticeCount", 0)
        notices = result.get("notices", [])
        print(f"\n{query}: {count} total, fetched {len(notices)}")
        all_notices.extend(notices)
        for notice in notices[:3]:
            title = notice.get("notice-title", {})
            t = title.get("eng") or title.get("nob") or next(iter(title.values()), "")
            print(
                f"  {notice.get('publication-number')} | {notice.get('notice-type')} | "
                f"{notice.get('procedure-type')} | {t[:90]}"
            )

    with open("data/cache/ted_probe.json", "w", encoding="utf-8") as fh:
        json.dump(all_notices, fh, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(all_notices)} notices to data/cache/ted_probe.json")
