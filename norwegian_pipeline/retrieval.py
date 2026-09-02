"""Document retrieval with local caching."""
from __future__ import annotations

import logging
import re
from pathlib import Path

from norwegian_pipeline.config import DOCS_DIR
from norwegian_pipeline.http_utils import download_file, get_text
from norwegian_pipeline.models import TenderNotice

logger = logging.getLogger(__name__)

# Known public document URLs discovered during source research.
# Many Mercell/Ivalua attachments require supplier login; these are documented in README.
KNOWN_DOCUMENTS: dict[str, list[dict[str, str]]] = {
    "LIS 2207": [
        {
            "url": "https://www.mercell.com/nb-no/anbud/176511702/lis-2207-onkologi-anbud.aspx",
            "name": "LIS 2207 Onkologi tender page (Mercell)",
            "note": "Vedlegg 02 Kravspesifikasjon.xlsx contains virkestoffliste with ATC codes",
        },
    ],
    "LIS 2234": [
        {
            "url": "https://www.mercell.com/nb-no/anbud/",
            "name": "LIS 2234 Lenalidomid (Mercell – search required)",
            "note": "Login may be required for prisskjema",
        },
    ],
    "2632a": [
        {
            "url": "https://www.mercell.com/nb-no/anbud/",
            "name": "LIS 2632a Everolimus tender page",
            "note": "Public notice metadata on TED/Anbudsregisteret",
        },
    ],
}


def _safe_filename(name: str) -> str:
    return re.sub(r"[^\w.\-]+", "_", name)[:120]


def fetch_notice_documents(notice: TenderNotice) -> list[Path]:
    """Attempt to download documents linked to a notice."""
    saved: list[Path] = []
    dest_dir = DOCS_DIR / _safe_filename(notice.notice_id or "unknown")
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Try TED PDF (often empty for automated download; cached either way)
    links = notice.extra.get("links", {}) if notice.extra else {}
    pdf_links = links.get("pdf", {}) if isinstance(links, dict) else {}
    if isinstance(pdf_links, dict):
        eng_pdf = pdf_links.get("ENG")
        if eng_pdf:
            path = download_file(eng_pdf, dest_dir / f"{notice.notice_id}.pdf")
            if path:
                saved.append(path)

    # Known LIS document pages
    ref = notice.tender_ref.upper()
    for key, docs in KNOWN_DOCUMENTS.items():
        if key.upper() in ref.upper() or key.upper() in notice.title.upper():
            for doc in docs:
                page_path = dest_dir / _safe_filename(doc["name"]) + ".html"
                try:
                    html = get_text(doc["url"])
                    page_path.write_text(html, encoding="utf-8")
                    saved.append(page_path)
                except Exception as exc:
                    logger.warning("Could not fetch %s: %s", doc["url"], exc)

    return saved


def extract_xlsx_urls_from_html(html: str) -> list[str]:
    patterns = [
        r'href="([^"]+\.xlsx[^"]*)"',
        r'href="([^"]*GetFile\.ashx[^"]*)"',
        r'href="([^"]*download[^"]*\.xlsx[^"]*)"',
    ]
    urls: list[str] = []
    for pattern in patterns:
        urls.extend(re.findall(pattern, html, flags=re.I))
    return list(dict.fromkeys(urls))
