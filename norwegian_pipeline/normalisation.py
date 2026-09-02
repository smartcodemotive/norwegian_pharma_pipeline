"""Normalisation helpers for dates, numbers, and text."""
from __future__ import annotations

import re
from datetime import datetime

from dateutil import parser as date_parser


def parse_date(value: str) -> str:
    """Return ISO date YYYY-MM-DD or empty string."""
    if not value or value.lower() in {"none", "nan", "n/a"}:
        return ""
    value = value.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return value
    # Norwegian dd.mm.yyyy
    m = re.fullmatch(r"(\d{2})\.(\d{2})\.(\d{4})", value)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    # TED style 2022-12-08+01:00
    value = value[:10]
    try:
        return date_parser.parse(value, dayfirst=True).strftime("%Y-%m-%d")
    except (ValueError, TypeError, OverflowError):
        return ""


def parse_norwegian_number(value: str) -> float | None:
    """
    Parse Norwegian numeric strings.

    Norwegian convention: space or dot as thousands separator, comma as decimal.
    Examples: '320 000 000', '1,5', '10.000,50'
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = re.sub(r"[^\d,.\s-]", "", text)
    text = text.replace("\xa0", " ").strip()
    if not text:
        return None

    # Both comma and dot present: last separator is decimal
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        # comma decimal if single comma near end
        if text.count(",") == 1 and len(text.split(",")[-1]) <= 2:
            text = text.replace(" ", "").replace(",", ".")
        else:
            text = text.replace(",", "").replace(" ", "")
    else:
        # dot or space thousands only
        if text.count(".") > 1 or (" " in text and "." in text):
            text = text.replace(".", "").replace(" ", "")
        elif text.count(".") == 1 and len(text.split(".")[-1]) == 3:
            text = text.replace(".", "")
        else:
            text = text.replace(" ", "")

    try:
        return float(text)
    except ValueError:
        return None


def format_number(value: float | None) -> str:
    if value is None:
        return ""
    if value == int(value):
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def normalise_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def infer_notice_status(notice_type: str, publication_date: str) -> str:
    nt = (notice_type or "").lower()
    if "result" in nt or "award" in nt or "can-standard" in nt:
        return "awarded"
    if "cancel" in nt:
        return "cancelled"
    if "prior" in nt or "pin" in nt or "planning" in nt:
        return "prior_information"
    if publication_date:
        try:
            pub = datetime.strptime(publication_date, "%Y-%m-%d")
            if (datetime.utcnow() - pub).days > 365:
                return "expired"
        except ValueError:
            pass
    return "active"
