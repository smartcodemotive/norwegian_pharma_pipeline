"""Tests for molecule matching and Norwegian number parsing."""
from __future__ import annotations

from norwegian_pipeline.matching import match_text
from norwegian_pipeline.normalisation import parse_date, parse_norwegian_number


def test_match_paliperidone_by_name() -> None:
    hits = match_text("Sykehusinnkjøp lyser ut 2601c paliperidon")
    assert any(h.molecule == "Paliperidone" for h in hits)


def test_match_paliperidone_by_atc() -> None:
    hits = match_text("Dellev. 90 N05AX13 Paliperidon injeksjon lav dose")
    assert any(h.molecule == "Paliperidone" and h.method == "atc_code" for h in hits)


def test_axitinib_not_matched_by_name_only() -> None:
    hits = match_text("LIS 2207 Onkologi rammeavtale")
    assert not any(h.molecule == "Axitinib" and h.method == "name_in_text" for h in hits)


def test_axitinib_matched_by_atc() -> None:
    hits = match_text("Virkestoffliste: L01EK01 aksitinib tabletter")
    assert any(h.molecule == "Axitinib" for h in hits)


def test_anagrelide_matched_by_atc() -> None:
    hits = match_text("Virkestoffliste B01AC24 anagrelid kapsler")
    assert any(h.molecule == "Anagrelide" and h.atc_code == "B01AC24" for h in hits)


def test_parse_norwegian_number() -> None:
    assert parse_norwegian_number("320 000 000") == 320000000.0
    assert parse_norwegian_number("10,5") == 10.5
    assert parse_norwegian_number("10.000,50") == 10000.5


def test_parse_date() -> None:
    assert parse_date("24.04.2024") == "2024-04-24"
    assert parse_date("2025-06-24+02:00") == "2025-06-24"
