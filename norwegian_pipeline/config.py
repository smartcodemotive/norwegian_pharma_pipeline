"""Pipeline configuration: molecules, search terms, and defaults."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = PROJECT_ROOT / "data" / "cache"
DOCS_DIR = CACHE_DIR / "documents"
OUTPUT_CSV = PROJECT_ROOT / "output.csv"
VIZ_DIR = PROJECT_ROOT / "visualizations"

USER_AGENT = "NorwegianPharmaPipeline/1.0 (take-home assessment; contact: assessment@example.com)"
RATE_LIMIT_SECONDS = 1.5
REQUEST_TIMEOUT = 60

TED_SEARCH_URL = "https://api.ted.europa.eu/v3/notices/search"
DOFFIN_API_BASE = "https://betaapi.doffin.no/public/v2"
ANBUDSREGISTERET_SEARCH = "https://anbudsregisteret.no/sok"


@dataclass(frozen=True)
class MoleculeProfile:
    """Target molecule with English name, ATC codes, and search patterns."""

    english_name: str
    atc_codes: tuple[str, ...]
    name_patterns: tuple[str, ...]
    brand_names: tuple[str, ...] = ()
    # Norwegian tender refs where molecule appears by code, not name
    lis_refs: tuple[str, ...] = ()
    notes: str = ""

    @property
    def all_search_terms(self) -> tuple[str, ...]:
        terms = list(self.name_patterns) + list(self.atc_codes) + list(self.brand_names)
        return tuple(dict.fromkeys(terms))


MOLECULES: dict[str, MoleculeProfile] = {
    "Axitinib": MoleculeProfile(
        english_name="Axitinib",
        atc_codes=("L01EK01", "L01EF03"),
        name_patterns=("axitinib", "aksitinib", "axitinib"),
        brand_names=("inlyta",),
        lis_refs=("2207",),
        notes=(
            "Rarely named in notice titles; typically listed in LIS oncology "
            "virkestoffliste (e.g. LIS 2207) by ATC code L01EK01."
        ),
    ),
    "Everolimus": MoleculeProfile(
        english_name="Everolimus",
        atc_codes=("L01EG02", "L04AH02", "L01XE10", "L04AA18"),
        name_patterns=("everolimus", "everolim"),
        brand_names=("afinitor", "certican"),
        lis_refs=("2632a",),
        notes="Often tendered with other immunosuppressants (e.g. mycophenolic acid).",
    ),
    "Lenalidomide": MoleculeProfile(
        english_name="Lenalidomide",
        atc_codes=("L04AX04",),
        name_patterns=("lenalidomid", "lenalidomide", "lenalidom"),
        brand_names=("revlimid",),
        lis_refs=("2234", "2234b"),
        notes="High-value myeloma therapy; LIS 2234 series.",
    ),
    "Anagrelide": MoleculeProfile(
        english_name="Anagrelide",
        atc_codes=("B01AC24", "B01AC14"),
        name_patterns=("anagrelid", "anagrelide"),
        brand_names=("agrylin", "xagrid"),
        lis_refs=("2507gj",),
        notes="Smaller tender; identified by LIS ref 2507gj-1 in notice title.",
    ),
    "Paliperidone": MoleculeProfile(
        english_name="Paliperidone",
        atc_codes=("N05AX13",),
        name_patterns=("paliperidon", "paliperidone", "paliperid"),
        brand_names=("invega", "xeplion"),
        lis_refs=("2601c",),
        notes="Also discoverable via ATC N05AX13 in LIS 2301d supplemental notices.",
    ),
}

CSV_COLUMNS: tuple[str, ...] = (
    "noticeId",
    "tenderRef",
    "title",
    "buyer",
    "country",
    "productMolecule",
    "moleculeDetected",
    "moleculeVariant",
    "detectionMethod",
    "atcCode",
    "itemNumber",
    "productName",
    "strength",
    "packsize",
    "supplier",
    "maxPrice",
    "packsSoldLast12m",
    "estimatedValue",
    "awardedValue",
    "awardedSupplier",
    "noticeType",
    "status",
    "publicationDate",
    "contractStart",
    "currency",
    "procedureType",
    "sourceDocument",
    "sourceUrl",
)

TED_SEARCH_FIELDS: tuple[str, ...] = (
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
)

TED_MOLECULE_QUERIES: list[str] = [
    'buyer-name~"SYKEHUSINNKJØP" AND classification-cpv=33600000',
    'FT~"LIS" AND FT~"legemidler" AND buyer-country=NOR',
]

for profile in MOLECULES.values():
    for term in profile.all_search_terms:
        TED_MOLECULE_QUERIES.append(f'FT~"{term}" AND buyer-country=NOR')

TED_MOLECULE_QUERIES = list(dict.fromkeys(TED_MOLECULE_QUERIES))
