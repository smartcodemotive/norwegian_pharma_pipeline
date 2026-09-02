"""Build sample virkestoffliste xlsx and pack rows from public tender structures."""
from __future__ import annotations

import csv
from pathlib import Path

from openpyxl import Workbook

from norwegian_pipeline.config import CSV_COLUMNS, PROJECT_ROOT
from norwegian_pipeline.parsers.documents import parse_xlsx

SAMPLE_DIR = PROJECT_ROOT / "data" / "sample"
XLSX_PATH = SAMPLE_DIR / "LIS_virkestoffliste_excerpt.xlsx"
PACK_CSV = SAMPLE_DIR / "sample_pack_rows.csv"

# Representative pack lines modelled on public LIS tender attachment structure.
# Prices and volumes left empty where not published in freely accessible documents.
VIRKESTOFF_ROWS = [
    # Lenalidomide — LIS 2234 (public notice value ~320 MNOK)
    ("L04AX04", "", "Lenalidomid", "5 mg", "21 kaps", "", "", "368699"),
    ("L04AX04", "", "Lenalidomid", "10 mg", "21 kaps", "", "", "368699"),
    ("L04AX04", "", "Lenalidomid", "15 mg", "21 kaps", "", "", "368699"),
    ("L04AX04", "", "Lenalidomid", "25 mg", "21 kaps", "", "", "368699"),
    # Everolimus — LIS 2632a
    ("L04AH02", "", "Everolimus", "0,5 mg", "30 tab", "", "", "404973"),
    ("L04AH02", "", "Everolimus", "0,75 mg", "30 tab", "", "", "404973"),
    ("L01EG02", "", "Everolimus", "2,5 mg", "30 tab", "", "", "404973"),
    ("L01EG02", "", "Everolimus", "5 mg", "30 tab", "", "", "404973"),
    ("L01EG02", "", "Everolimus", "10 mg", "30 tab", "", "", "404973"),
    # Paliperidone — LIS 2601c / N05AX13
    ("N05AX13", "", "Paliperidon", "1 mg", "28 tab", "", "", "434619"),
    ("N05AX13", "", "Paliperidon", "3 mg", "28 tab", "", "", "434619"),
    ("N05AX13", "", "Paliperidon", "6 mg", "28 tab", "", "", "434619"),
    ("N05AX13", "", "Paliperidon injeksjon lav dose", "75 mg", "1 amp", "", "", "682047"),
    ("N05AX13", "", "Paliperidon injeksjon lav dose", "100 mg", "1 amp", "", "", "682047"),
    # Anagrelide — LIS 2507gj-1 (ATC B01AC24)
    ("B01AC24", "", "Anagrelid", "0,5 mg", "100 kaps", "", "", "244859"),
    # Axitinib — LIS 2207 Onkologi virkestoffliste (ATC only in public docs)
    ("L01EK01", "", "Aksitinib", "1 mg", "56 tab", "", "", "176511702"),
    ("L01EK01", "", "Aksitinib", "3 mg", "56 tab", "", "", "176511702"),
    ("L01EK01", "", "Aksitinib", "5 mg", "56 tab", "", "", "176511702"),
    ("L01EK01", "", "Aksitinib", "7 mg", "56 tab", "", "", "176511702"),
]

NOTICE_META = {
    "368699": {
        "noticeId": "368699",
        "tenderRef": "LIS 2234b",
        "title": "LIS 2234b Lenalidomid",
        "estimatedValue": "320000000",
        "publicationDate": "2021-07-01",
        "sourceUrl": "https://anbudsregisteret.no/anbud/lis-2234b-lenalidomid-2021-368699",
    },
    "404973": {
        "noticeId": "404973-2025",
        "tenderRef": "2632a",
        "title": "Norway – Pharmaceutical products – 2632a Everolimus and Mycophenolic Acid",
        "estimatedValue": "128000000",
        "publicationDate": "2025-06-24",
        "sourceUrl": "https://anbudsregisteret.no/anbud/404973-2025-norway-pharmaceutical-products-2632a-everolimus-and-mykofenolic",
    },
    "434619": {
        "noticeId": "434619-2026",
        "tenderRef": "2601c",
        "title": "Norway – Medical equipments, pharmaceuticals – 2601c paliperidone",
        "estimatedValue": "",
        "publicationDate": "2026-06-25",
        "sourceUrl": "https://anbudsregisteret.no/anbud/434619-2026-norway-medical-equipments-pharmaceuticals-and-personal-care",
    },
    "682047": {
        "noticeId": "682047-2022",
        "tenderRef": "LIS 2301d",
        "title": "Intensjonskunngjøring – Tilleggsavtaler til LIS 2301d, ATC N05AX13 Paliperidon injeksjon",
        "estimatedValue": "",
        "publicationDate": "2022-12-08",
        "sourceUrl": "https://ted.europa.eu/en/notice/-/detail/682047-2022",
    },
    "244859": {
        "noticeId": "244859-2024",
        "tenderRef": "2507gj",
        "title": "Norway – Pharmaceutical products – 2507gj-1 anagrelid",
        "estimatedValue": "10000000",
        "publicationDate": "2024-04-24",
        "sourceUrl": "https://anbudsregisteret.no/anbud/244859-2024-norway-pharmaceutical-products-2507gj-1-anagrelid",
    },
    "176511702": {
        "noticeId": "176511702",
        "tenderRef": "LIS 2207",
        "title": "LIS 2207 Onkologi",
        "estimatedValue": "3200000000",
        "publicationDate": "",
        "sourceUrl": "https://www.mercell.com/nb-no/anbud/176511702/lis-2207-onkologi-anbud.aspx",
    },
}


def build_xlsx() -> Path:
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "Virkestoffliste"
    ws.append(["ATC-kode", "Varenummer", "Virkestoff", "Styrke", "Pakning", "Makspris", "Forbruk siste 12 mnd"])
    for row in VIRKESTOFF_ROWS:
        ws.append(row[:7])
    wb.save(XLSX_PATH)
    return XLSX_PATH


def build_pack_csv() -> Path:
    xlsx = build_xlsx()
    parsed = parse_xlsx(xlsx, source_document=xlsx.name)

    rows: list[dict[str, str]] = []

    # Build CSV from VIRKESTOFF_ROWS + metadata directly for reliability
    for atc, item, product, strength, packsize, max_price, volume, notice_key in VIRKESTOFF_ROWS:
        meta = NOTICE_META[notice_key]
        molecule = {
            "L04AX04": "Lenalidomide",
            "L04AH02": "Everolimus",
            "L01EG02": "Everolimus",
            "N05AX13": "Paliperidone",
            "B01AC24": "Anagrelide",
            "L01EK01": "Axitinib",
        }[atc]
        rows.append(
            {
                "noticeId": meta["noticeId"],
                "tenderRef": meta["tenderRef"],
                "title": meta["title"],
                "buyer": "SYKEHUSINNKJØP HF",
                "country": "Norway",
                "productMolecule": molecule,
                "moleculeDetected": "yes",
                "moleculeVariant": product,
                "detectionMethod": "atc_code_in_document",
                "atcCode": atc,
                "itemNumber": item,
                "productName": product,
                "strength": strength,
                "packsize": packsize,
                "supplier": "",
                "maxPrice": max_price,
                "packsSoldLast12m": volume,
                "estimatedValue": meta.get("estimatedValue", ""),
                "awardedValue": "",
                "awardedSupplier": "",
                "noticeType": "competition",
                "status": "expired",
                "publicationDate": meta.get("publicationDate", ""),
                "contractStart": "",
                "currency": "NOK",
                "procedureType": "open",
                "sourceDocument": XLSX_PATH.name,
                "sourceUrl": meta["sourceUrl"],
            }
        )

    # Notice-level lifecycle rows (prior info + competition + intent) from public indexes
    lifecycle = [
        ("147880-2021", "LIS 2234", "LIS 2234 Lenalidomid", "Lenalidomide", "lenalidomid", "name_in_title", "320000000", "2021-03-15", "prior_information"),
        ("48506-2021", "LIS 2234", "Norway-Vadsø: Pharmaceutical products (lenalidomid)", "Lenalidomide", "lenalidomid", "name_in_notice", "320000000", "2021-02-01", "competition"),
        ("300744", "LIS 2234", "LIS 2234 Lenalidomid. Veiledende kunngjøring", "Lenalidomide", "lenalidomid", "name_in_title", "320000000", "2021-01-28", "prior_information"),
        ("98880-2025", "2632", "Prior information notice 2632 transplantation", "Everolimus", "2632", "lis_ref_in_title", "", "2025-02-13", "prior_information"),
        ("208250-2025", "2632", "Norway – Pharmaceutical products – 2632 transplantation", "Everolimus", "everolimus", "name_in_title", "185000000", "2025-04-01", "competition"),
        ("522128-2024", "2507gj", "Prior information notice 2507gj anagrelid", "Anagrelide", "anagrelid", "name_in_title", "", "2024-08-30", "prior_information"),
        ("2601c", "2601c", "2601c paliperidon", "Paliperidone", "paliperidon", "name_in_title", "", "2026-06-25", "competition"),
        ("667535-2022", "LIS 2301d", "Norway-Vadsø: Pharmaceutical products (N05AX13)", "Paliperidone", "N05AX13", "atc_code_in_title", "", "2022-11-01", "competition"),
        ("344617", "LIS 2107", "LIS 2107 Onkologi", "Axitinib", "L01EK01", "atc_code_in_document_list", "1303000000", "2021-02-26", "competition"),
    ]
    for notice_id, tender_ref, title, molecule, variant, method, est, pub, ntype in lifecycle:
        rows.append(
            {
                "noticeId": notice_id,
                "tenderRef": tender_ref,
                "title": title,
                "buyer": "SYKEHUSINNKJØP HF",
                "country": "Norway",
                "productMolecule": molecule,
                "moleculeDetected": "yes",
                "moleculeVariant": variant,
                "detectionMethod": method,
                "atcCode": "",
                "itemNumber": "",
                "productName": "",
                "strength": "",
                "packsize": "",
                "supplier": "",
                "maxPrice": "",
                "packsSoldLast12m": "",
                "estimatedValue": est,
                "awardedValue": "",
                "awardedSupplier": "",
                "noticeType": ntype,
                "status": "expired" if pub < "2026-01-01" else "active",
                "publicationDate": pub,
                "contractStart": "",
                "currency": "NOK",
                "procedureType": "open",
                "sourceDocument": "TED/Anbudsregisteret notice index",
                "sourceUrl": f"https://ted.europa.eu/en/notice/-/detail/{notice_id}"
                if "-" in notice_id
                else f"https://anbudsregisteret.no/sok?q={variant}",
            }
        )

    with PACK_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(CSV_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    parsed_count = len(parse_xlsx(xlsx, source_document=xlsx.name))
    print(f"Built {xlsx} ({parsed_count} parser hits) and {PACK_CSV} ({len(rows)} rows)")
    return PACK_CSV


if __name__ == "__main__":
    build_pack_csv()
