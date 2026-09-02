"""Molecule detection across notices and documents."""
from __future__ import annotations

import re
from dataclasses import dataclass

from norwegian_pipeline.config import MOLECULES, MoleculeProfile


@dataclass
class MatchResult:
    molecule: str
    detected: bool
    variant: str
    method: str
    atc_code: str = ""


def _compile_pattern(term: str) -> re.Pattern[str]:
    return re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)


def _match_profile(text: str, profile: MoleculeProfile) -> MatchResult | None:
    if not text:
        return None

    # ATC codes (highest specificity for Norwegian LIS documents)
    for atc in profile.atc_codes:
        if re.search(rf"\b{re.escape(atc)}\b", text, re.IGNORECASE):
            return MatchResult(
                molecule=profile.english_name,
                detected=True,
                variant=atc,
                method="atc_code",
                atc_code=atc,
            )

    # LIS tender reference patterns (e.g. 2601c, 2507gj) — require LIS prefix or full ref
    for ref in profile.lis_refs:
        patterns = [
            rf"\bLIS\s*{re.escape(ref)}\b",
            rf"\b{re.escape(ref)}\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Avoid false positives: short numeric refs must appear in pharma context
                if ref.isdigit() or (ref[:4].isdigit() and len(ref) <= 5):
                    pharma_ctx = re.search(
                        r"legemid|pharma|virkestoff|medicinal|farmas",
                        text,
                        re.IGNORECASE,
                    )
                    if not pharma_ctx and ref not in text.lower():
                        continue
                return MatchResult(
                    molecule=profile.english_name,
                    detected=True,
                    variant=match.group(0),
                    method="lis_ref_in_title",
                )

    # Name and brand patterns
    for term in list(profile.name_patterns) + list(profile.brand_names):
        pattern = _compile_pattern(term)
        match = pattern.search(text)
        if match:
            method = "brand_name" if term in profile.brand_names else "name_in_text"
            return MatchResult(
                molecule=profile.english_name,
                detected=True,
                variant=match.group(0),
                method=method,
            )

    return None


def match_text(text: str) -> list[MatchResult]:
    """Return all molecule matches found in text (may be multiple)."""
    results: list[MatchResult] = []
    for profile in MOLECULES.values():
        hit = _match_profile(text, profile)
        if hit:
            results.append(hit)
    return results


def match_notice(title: str, body: str = "", tender_ref: str = "") -> list[MatchResult]:
    """Match molecules in notice fields; prefer title-specific method labels."""
    results: list[MatchResult] = []
    seen: set[tuple[str, str]] = set()

    for field, text in (
        ("title", title),
        ("body", body),
        ("ref", tender_ref),
    ):
        if not text:
            continue
        for hit in match_text(text):
            key = (hit.molecule, hit.method)
            if key in seen:
                continue
            seen.add(key)
            method = hit.method
            if hit.method == "name_in_text":
                method = "name_in_title" if field == "title" else "name_in_notice"
            elif hit.method == "lis_ref_in_title":
                method = "lis_ref_in_title" if field in {"title", "ref"} else "lis_ref_in_notice"
            elif hit.method == "atc_code":
                method = "atc_code_in_title" if field == "title" else "atc_code_in_notice"
            results.append(
                MatchResult(
                    molecule=hit.molecule,
                    detected=hit.detected,
                    variant=hit.variant,
                    method=method,
                    atc_code=hit.atc_code,
                )
            )
    return results


def best_match(text: str) -> MatchResult | None:
    hits = match_text(text)
    return hits[0] if hits else None


def profile_for_molecule(name: str) -> MoleculeProfile | None:
    return MOLECULES.get(name)
