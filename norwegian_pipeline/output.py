"""CSV output writer."""
from __future__ import annotations

import csv
import logging
from pathlib import Path

from norwegian_pipeline.config import CSV_COLUMNS, OUTPUT_CSV
from norwegian_pipeline.models import PackRow
from norwegian_pipeline.normalisation import format_number, parse_norwegian_number

logger = logging.getLogger(__name__)

_NUMERIC_COLUMNS = frozenset({"maxPrice", "packsSoldLast12m", "estimatedValue", "awardedValue"})


def _format_csv_value(column: str, value: str) -> str:
    if column not in _NUMERIC_COLUMNS or not value:
        return value
    parsed = parse_norwegian_number(value)
    if parsed is None:
        return value
    return format_number(parsed)


def write_csv(rows: list[PackRow], path: Path | None = None) -> Path:
    out = path or OUTPUT_CSV
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(CSV_COLUMNS), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            record = row.to_dict()
            for column in _NUMERIC_COLUMNS:
                record[column] = _format_csv_value(column, record.get(column, ""))
            writer.writerow(record)
    logger.info("Wrote %d rows to %s", len(rows), out)
    return out
