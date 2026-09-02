"""Data models for tender extraction rows."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TenderNotice:
    """Normalised notice metadata from any source."""

    notice_id: str
    tender_ref: str
    title: str
    buyer: str
    country: str = "Norway"
    notice_type: str = ""
    status: str = ""
    publication_date: str = ""
    contract_start: str = ""
    estimated_value: str = ""
    awarded_value: str = ""
    awarded_supplier: str = ""
    currency: str = "NOK"
    procedure_type: str = ""
    source_url: str = ""
    source_name: str = ""
    raw_text: str = ""
    document_urls: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class PackRow:
    """One output CSV row (notice-level or pack-level)."""

    notice_id: str = ""
    tender_ref: str = ""
    title: str = ""
    buyer: str = ""
    country: str = "Norway"
    product_molecule: str = ""
    molecule_detected: str = ""
    molecule_variant: str = ""
    detection_method: str = ""
    atc_code: str = ""
    item_number: str = ""
    product_name: str = ""
    strength: str = ""
    packsize: str = ""
    supplier: str = ""
    max_price: str = ""
    packs_sold_last_12m: str = ""
    estimated_value: str = ""
    awarded_value: str = ""
    awarded_supplier: str = ""
    notice_type: str = ""
    status: str = ""
    publication_date: str = ""
    contract_start: str = ""
    currency: str = "NOK"
    procedure_type: str = ""
    source_document: str = ""
    source_url: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "noticeId": self.notice_id,
            "tenderRef": self.tender_ref,
            "title": self.title,
            "buyer": self.buyer,
            "country": self.country,
            "productMolecule": self.product_molecule,
            "moleculeDetected": self.molecule_detected,
            "moleculeVariant": self.molecule_variant,
            "detectionMethod": self.detection_method,
            "atcCode": self.atc_code,
            "itemNumber": self.item_number,
            "productName": self.product_name,
            "strength": self.strength,
            "packsize": self.packsize,
            "supplier": self.supplier,
            "maxPrice": self.max_price,
            "packsSoldLast12m": self.packs_sold_last_12m,
            "estimatedValue": self.estimated_value,
            "awardedValue": self.awarded_value,
            "awardedSupplier": self.awarded_supplier,
            "noticeType": self.notice_type,
            "status": self.status,
            "publicationDate": self.publication_date,
            "contractStart": self.contract_start,
            "currency": self.currency,
            "procedureType": self.procedure_type,
            "sourceDocument": self.source_document,
            "sourceUrl": self.source_url,
        }
