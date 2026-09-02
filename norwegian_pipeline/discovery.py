"""Orchestrate notice discovery from all sources."""
from __future__ import annotations

import logging
from collections import defaultdict

from norwegian_pipeline.clients import anbudsregisteret, doffin, ted
from norwegian_pipeline.matching import match_notice
from norwegian_pipeline.models import TenderNotice

logger = logging.getLogger(__name__)


def _dedupe_key(notice: TenderNotice) -> str:
    if notice.notice_id:
        return f"id:{notice.notice_id}"
    return f"url:{notice.source_url}"


def discover_notices(*, include_doffin: bool = True, include_anbuds: bool = True) -> list[TenderNotice]:
    """Collect notices from TED, optional Doffin, and Anbudsregisteret."""
    combined: dict[str, TenderNotice] = {}

    for notice in ted.discover_all():
        combined[_dedupe_key(notice)] = notice
    logger.info("TED discovery: %d unique notices", len(combined))

    if include_doffin:
        for notice in doffin.discover_all():
            key = _dedupe_key(notice)
            if key not in combined:
                combined[key] = notice
        logger.info("After Doffin: %d unique notices", len(combined))

    if include_anbuds:
        for notice in anbudsregisteret.discover_all():
            key = _dedupe_key(notice)
            existing = combined.get(key)
            if existing:
                # Enrich TED notice with Anbudsregisteret estimated value if missing
                if not existing.estimated_value and notice.estimated_value:
                    existing.estimated_value = notice.estimated_value
                if not existing.publication_date and notice.publication_date:
                    existing.publication_date = notice.publication_date
            else:
                combined[key] = notice
        logger.info("After Anbudsregisteret: %d unique notices", len(combined))

    return list(combined.values())


def filter_relevant(notices: list[TenderNotice]) -> list[TenderNotice]:
    """Keep notices that match at least one target molecule."""
    relevant: list[TenderNotice] = []
    for notice in notices:
        hits = match_notice(notice.title, notice.raw_text, notice.tender_ref)
        if hits:
            relevant.append(notice)
    logger.info("Filtered to %d molecule-relevant notices", len(relevant))
    return relevant


def group_by_molecule(notices: list[TenderNotice]) -> dict[str, list[TenderNotice]]:
    groups: dict[str, list[TenderNotice]] = defaultdict(list)
    for notice in notices:
        hits = match_notice(notice.title, notice.raw_text, notice.tender_ref)
        for hit in hits:
            groups[hit.molecule].append(notice)
    return dict(groups)
