"""TED Search API v3 client."""
from __future__ import annotations

import logging
import re
from typing import Any, Iterator

from norwegian_pipeline.config import TED_MOLECULE_QUERIES, TED_SEARCH_FIELDS, TED_SEARCH_URL
from norwegian_pipeline.http_utils import get_json
from norwegian_pipeline.models import TenderNotice
from norwegian_pipeline.normalisation import format_number, parse_date, parse_norwegian_number

logger = logging.getLogger(__name__)


def _localised_text(value: Any, prefer: tuple[str, ...] = ("eng", "nob", "nno")) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "; ".join(str(v) for v in value if v)
    if isinstance(value, dict):
        for lang in prefer:
            if lang in value and value[lang]:
                v = value[lang]
                if isinstance(v, list):
                    return "; ".join(str(x) for x in v)
                return str(v)
        for v in value.values():
            text = _localised_text(v, prefer)
            if text:
                return text
    return str(value)


def _extract_lis_ref(title: str) -> str:
    match = re.search(r"LIS\s*(\d{4}[a-z]{0,3}(?:-\d+)?)", title, re.I)
    if match:
        return f"LIS {match.group(1)}"
    match = re.search(r"\b(\d{4}[a-z]{1,3})\b", title)
    if match:
        return match.group(1)
    return ""


def _notice_url(pub_number: str, links: dict[str, Any] | None) -> str:
    if links:
        html = links.get("html", {})
        if isinstance(html, dict):
            for key in ("ENG", "NOR", "NOB"):
                if key in html:
                    return html[key]
            if html:
                return next(iter(html.values()))
    return f"https://ted.europa.eu/en/notice/-/detail/{pub_number}"


def _map_notice(raw: dict[str, Any]) -> TenderNotice:
    pub = str(raw.get("publication-number", ""))
    title = _localised_text(raw.get("notice-title"))
    buyer = _localised_text(raw.get("buyer-name") or raw.get("organisation-name-buyer"))
    est = raw.get("estimated-value-proc", "")
    est_parsed = parse_norwegian_number(str(est)) if est not in ("", None) else None
    est_str = format_number(est_parsed) if est_parsed is not None else ""
    awarded = raw.get("result-value", "")
    awarded_parsed = parse_norwegian_number(str(awarded)) if awarded not in ("", None) else None
    awarded_str = format_number(awarded_parsed) if awarded_parsed is not None else ""
    currency = _localised_text(raw.get("estimated-value-cur-proc")) or "NOK"
    if currency and len(currency) > 5:
        currency = "NOK"

    description = " ".join(
        filter(
            None,
            [
                _localised_text(raw.get("description-lot")),
                _localised_text(raw.get("description-proc")),
                _localised_text(raw.get("title-lot")),
                _localised_text(raw.get("title-proc")),
            ],
        )
    )

    return TenderNotice(
        notice_id=pub,
        tender_ref=_extract_lis_ref(title) or _extract_lis_ref(description),
        title=title,
        buyer=buyer or "SYKEHUSINNKJØP HF",
        notice_type=str(raw.get("notice-type", "")),
        status="",
        publication_date=parse_date(str(raw.get("publication-date", ""))),
        contract_start=parse_date(str(raw.get("contract-duration-start-date-lot", ""))),
        estimated_value=est_str,
        awarded_value=awarded_str,
        awarded_supplier=_localised_text(raw.get("winner-name")),
        currency=currency,
        procedure_type=str(raw.get("procedure-type", "")),
        source_url=_notice_url(pub, raw.get("links")),
        source_name="TED",
        raw_text=f"{title} {description}",
        extra=raw,
    )


def search_notices(
    query: str,
    *,
    limit: int = 50,
    max_pages: int = 5,
) -> list[TenderNotice]:
    notices: list[TenderNotice] = []
    payload: dict[str, Any] = {
        "query": query,
        "fields": list(TED_SEARCH_FIELDS),
        "limit": min(limit, 100),
        "scope": "ALL",
        "paginationMode": "ITERATION",
        "onlyLatestVersions": False,
    }

    for _ in range(max_pages):
        data = get_json(TED_SEARCH_URL, method="POST", json_body=payload)
        batch = data.get("notices", [])
        for item in batch:
            notices.append(_map_notice(item))
        token = data.get("iterationNextToken")
        if not token or len(batch) < payload["limit"]:
            break
        payload["iterationNextToken"] = token

    logger.info("TED query %r returned %d notices", query, len(notices))
    return notices


def discover_all() -> list[TenderNotice]:
    seen: set[str] = set()
    results: list[TenderNotice] = []
    for query in TED_MOLECULE_QUERIES:
        try:
            for notice in search_notices(query, limit=30, max_pages=3):
                if notice.notice_id not in seen:
                    seen.add(notice.notice_id)
                    results.append(notice)
        except Exception as exc:
            logger.warning("TED search failed for %r: %s", query, exc)
    return results


def iter_notices() -> Iterator[TenderNotice]:
    yield from discover_all()
