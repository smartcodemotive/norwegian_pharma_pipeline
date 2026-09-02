"""Anbudsregisteret.no search scraper (supplementary discovery)."""
from __future__ import annotations

import logging
import re
from html import unescape
from typing import Any

from norwegian_pipeline.config import ANBUDSREGISTERET_SEARCH, MOLECULES
from norwegian_pipeline.http_utils import get_text
from norwegian_pipeline.models import TenderNotice
from norwegian_pipeline.normalisation import parse_date, parse_norwegian_number

logger = logging.getLogger(__name__)


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", unescape(text)).strip()


def _extract_notice_id(path: str) -> str:
    slug = path.rstrip("/").split("/")[-1]
    ted_match = re.match(r"^(\d{6}-\d{4})", slug)
    if ted_match:
        return ted_match.group(1)
    trailing = re.search(r"-(\d{6})$", slug)
    if trailing:
        return trailing.group(1)
    return slug


def _extract_lis_ref(title: str) -> str:
    match = re.search(r"LIS\s*(\d{4}[a-z]{0,3}(?:-\d+)?)", title, re.I)
    if match:
        return f"LIS {match.group(1)}"
    match = re.search(r"\b(\d{4}[a-z]{1,3})\b", title)
    return match.group(1) if match else ""


def _parse_search_results(html: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    pattern = re.compile(
        r'<h3>\s*<a href="(/anbud/[^"]+)">([^<]+)</a>\s*</h3>(.*?)(?=<h3>|</section>|$)',
        re.DOTALL | re.IGNORECASE,
    )
    for match in pattern.finditer(html):
        path, title, tail = match.groups()
        title = _strip_html(title)
        snippet = _strip_html(tail)[:800]
        value = ""
        value_match = re.search(r"([\d\s]+)\s*000\s*000\s*kr", snippet)
        if value_match:
            value = value_match.group(0).replace("kr", "").strip()
        else:
            vm = re.search(r"([\d\s.,]+)\s*kr", snippet)
            value = vm.group(1).strip() if vm else ""
        date_match = re.search(r"(\d{2}\.\d{2}\.\d{4})", snippet)
        pub_date = date_match.group(1) if date_match else ""
        results.append(
            {
                "path": path,
                "title": title,
                "estimated_value": value,
                "publication_date": pub_date,
                "snippet": snippet,
            }
        )
    return results


def search(query: str) -> list[TenderNotice]:
    url = f"{ANBUDSREGISTERET_SEARCH}?q={query}"
    try:
        html = get_text(url)
    except Exception as exc:
        logger.warning("Anbudsregisteret search failed for %r: %s", query, exc)
        return []

    notices: list[TenderNotice] = []
    for hit in _parse_search_results(html):
        title = hit["title"]
        notices.append(
            TenderNotice(
                notice_id=_extract_notice_id(hit["path"]),
                tender_ref=_extract_lis_ref(title),
                title=title,
                buyer="SYKEHUSINNKJØP HF",
                estimated_value=str(parse_norwegian_number(hit["estimated_value"]))
                if hit["estimated_value"]
                else "",
                publication_date=parse_date(hit["publication_date"]),
                currency="NOK",
                source_url=f"https://anbudsregisteret.no{hit['path']}",
                source_name="Anbudsregisteret",
                raw_text=f"{title} {hit.get('snippet', '')}",
            )
        )
    return notices


def discover_all() -> list[TenderNotice]:
    seen_urls: set[str] = set()
    results: list[TenderNotice] = []
    terms: set[str] = set()
    for profile in MOLECULES.values():
        terms.update(profile.name_patterns)
        terms.update(profile.atc_codes)
        terms.update(profile.lis_refs)
        terms.add(profile.english_name.lower())

    for term in sorted(terms):
        for notice in search(term):
            if notice.source_url not in seen_urls:
                seen_urls.add(notice.source_url)
                results.append(notice)
    return results
