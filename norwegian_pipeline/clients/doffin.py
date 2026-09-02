"""Doffin Public API v2 client (optional API key)."""
from __future__ import annotations

import logging
import os
import re
from typing import Any

from norwegian_pipeline.config import DOFFIN_API_BASE, MOLECULES
from norwegian_pipeline.http_utils import get_json
from norwegian_pipeline.models import TenderNotice
from norwegian_pipeline.normalisation import parse_date, parse_norwegian_number

logger = logging.getLogger(__name__)


def _api_key() -> str:
    return os.environ.get("DOFFIN_API_KEY", "")


def _headers() -> dict[str, str]:
    key = _api_key()
    if not key:
        return {}
    return {"Ocp-Apim-Subscription-Key": key}


def _extract_lis_ref(text: str) -> str:
    match = re.search(r"LIS\s*(\d{4}[a-z]{0,3})", text, re.I)
    return f"LIS {match.group(1)}" if match else ""


def _map_hit(hit: dict[str, Any]) -> TenderNotice:
    notice_id = str(hit.get("id") or hit.get("noticeId") or "")
    title = str(hit.get("heading") or hit.get("title") or "")
    buyer = str(hit.get("buyerName") or hit.get("contractingAuthority") or "")
    est = hit.get("estimatedValue") or hit.get("value") or ""
    return TenderNotice(
        notice_id=notice_id,
        tender_ref=_extract_lis_ref(title),
        title=title,
        buyer=buyer,
        notice_type=str(hit.get("type") or ""),
        status=str(hit.get("status") or ""),
        publication_date=parse_date(str(hit.get("publicationDate") or "")),
        estimated_value=str(parse_norwegian_number(str(est))) if est else "",
        currency="NOK",
        procedure_type=str(hit.get("procedureType") or ""),
        source_url=f"https://www.doffin.no/notice/{notice_id}" if notice_id else "https://www.doffin.no/",
        source_name="Doffin",
        raw_text=title,
        extra=hit,
    )


def search_notices(search_string: str, *, page: int = 0, num_hits: int = 50) -> list[TenderNotice]:
    if not _api_key():
        logger.info(
            "DOFFIN_API_KEY not set; skipping Doffin API. "
            "Register at https://dof-notices-prod-api.developer.azure-api.net/"
        )
        return []

    params = {
        "searchString": search_string,
        "page": str(page),
        "numHitsPerPage": str(num_hits),
        "sortBy": "PUBLICATION_DATE_DESC",
    }
    try:
        data = get_json(
            f"{DOFFIN_API_BASE}/notices/search",
            params=params,
            headers=_headers(),
        )
    except Exception as exc:
        logger.warning("Doffin search failed for %r: %s", search_string, exc)
        return []

    hits = data.get("hits") or data.get("notices") or []
    return [_map_hit(h) for h in hits]


def discover_all() -> list[TenderNotice]:
    if not _api_key():
        return []

    seen: set[str] = set()
    results: list[TenderNotice] = []
    terms: set[str] = set()
    for profile in MOLECULES.values():
        terms.update(profile.name_patterns)
        terms.update(profile.atc_codes)
        terms.update(profile.lis_refs)

    for term in sorted(terms):
        for notice in search_notices(term):
            if notice.notice_id and notice.notice_id not in seen:
                seen.add(notice.notice_id)
                results.append(notice)
    return results
