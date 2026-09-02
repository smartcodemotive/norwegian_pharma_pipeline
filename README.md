# Assignment C — Norwegian Pharmaceutical Tender Pipeline

Python pipeline that discovers, extracts, and analyses Norwegian public procurement data for five target molecules:

- **Axitinib**
- **Everolimus**
- **Lenalidomide**
- **Anagrelide**
- **Paliperidone**

## Quick start

```bash
# Create virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
pip install -e .

# Run extraction (writes output.csv)
python -m norwegian_pipeline.pipeline

# Generate visualisations (writes visualizations/*.png)
python scripts/visualize.py
```

Optional: set `DOFFIN_API_KEY` for Doffin Public API v2 access (free registration at [Doffin API portal](https://dof-notices-prod-api.developer.azure-api.net/)).

```bash
set DOFFIN_API_KEY=your-key-here   # Windows
export DOFFIN_API_KEY=your-key-here  # macOS/Linux
```

## Project structure

```
norwegian_pipeline/
  config.py          # Molecule profiles, ATC codes, search terms
  discovery.py       # Multi-source notice discovery
  matching.py        # Name + ATC + LIS-ref detection
  pipeline.py        # Main orchestration
  clients/
    ted.py           # TED Search API v3 (no key required)
    doffin.py        # Doffin API v2 (optional key)
    anbudsregisteret.py  # Supplementary HTML search
  parsers/
    documents.py     # XLSX / PDF parsers for tender attachments
  retrieval.py       # Document download + cache
  output.py          # UTF-8 CSV writer
data/sample/         # Virkestoffliste excerpt + lifecycle rows
scripts/
  run_pipeline.py
  visualize.py
  build_sample_pack_data.py
output.csv           # Generated extraction output
visualizations/      # Charts + interpretations.md
```

## How sources were found

### Primary route: Sykehusinnkjøp HF / LIS → TED + Doffin

Norwegian hospital pharmaceuticals are procured nationally by **Sykehusinnkjøp HF**, division legemidler (**LIS** — *Legemiddelinnkjøpssamarbeidet*). Above-threshold competitions are published on:

| Source | Role | Access |
|--------|------|--------|
| [TED Search API v3](https://api.ted.europa.eu/v3/notices/search) | Above-threshold notices (JSON, no auth) | **Used** |
| [Doffin](https://www.doffin.no/) | National notice database | API requires key; web UI is JS-rendered |
| [Anbudsregisteret.no](https://anbudsregisteret.no/) | Aggregated search / metadata | **Used** as supplementary discovery |
| [Mercell / Ivalua](https://www.mercell.com/) | Tender documents (virkestoffliste, prisskjema) | **Login wall** for XLSX/PDF attachments |

### Approaches tried

| Approach | Result |
|----------|--------|
| TED full-text + ATC queries (`FT~"N05AX13"`, `FT~"lenalidomid"`, etc.) | Works well; main discovery path |
| Doffin API without key | 404 / auth required — documented, skipped unless key set |
| Doffin web search (`doffin.no/search`) | JavaScript SPA — not scrape-friendly without browser |
| Mercell document download | Tender pages list attachments; direct XLSX download requires supplier login |
| Name-only search for Axitinib | **Zero title hits** — molecule appears by **ATC L01EK01** inside LIS 2207 oncology virkestoffliste |

### Molecule-specific discovery notes

| Molecule | How it appears in Norwegian data |
|----------|----------------------------------|
| **Paliperidone** | Name (`paliperidon`) in LIS 2601c; also **N05AX13** in LIS 2301d supplemental notices |
| **Lenalidomide** | Name (`lenalidomid`) in LIS 2234 series; high framework value (~320 MNOK) |
| **Everolimus** | Name in LIS 2632a; dual ATC **L01EG02** / **L04AH02** depending on indication |
| **Anagrelide** | Name + LIS ref **2507gj**; smaller standalone tender (~10 MNOK) |
| **Axitinib** | **Not in notice titles**; identified via **L01EK01** in LIS 2207 Onkologi attachment list |

## What is implemented

- Multi-source discovery (TED + Anbudsregisteret + optional Doffin)
- Molecule matching via **English/Norwegian names**, **ATC codes**, and **LIS tender refs**
- XLSX parser for virkestoffliste / prisskjema column layouts (Norwegian headers)
- PDF text extraction (when documents are reachable)
- Local HTTP cache under `data/cache/` (re-runs do not re-hit sources)
- Rate limiting (1.5 s between requests), retries with backoff, meaningful User-Agent
- UTF-8 CSV output with ISO dates and empty cells where data is unknown
- Five visualisations with written interpretations

## What was skipped and why

| Item | Reason |
|------|--------|
| Full Mercell/Ivalua attachment download | Supplier login required — URLs recorded in code/README |
| Doffin API (without key) | Requires free API registration |
| Award values / winning suppliers for most rows | Not published in freely accessible notices (confidential by notice type) |
| `packsSoldLast12m`, `maxPrice` for most packs | Inside prisskjema XLSX behind login |
| OCR | Not required per brief |
| 100% notice coverage | Explicitly not required; target 40–120 rows |

## Duplicates and notice lifecycles

The same procurement often appears multiple times:

- **Different languages** (Norwegian `2601c paliperidon` vs English `2601c paliperidone`)
- **Lifecycle stages** (prior information → competition → result/intent)
- **Different IDs** (TED `434619-2026` vs Anbudsregisteret slug)

**Handling:** deduplicate on `(noticeId, productMolecule, strength, packsize, detectionMethod)` while **keeping** distinct lifecycle rows when `noticeType` or `publicationDate` differs. Rows from different sources for the same TED publication are merged at discovery time (Anbudsregisteret enriches missing estimated values).

## Limitations and trade-offs

1. **Pack-level detail** depends on parsing virkestoffliste attachments; most live attachments sit behind Mercell login. A representative excerpt is included in `data/sample/` to demonstrate the parser; fields without public evidence are left empty.
2. **Axitinib** requires ATC-based inference inside oncology bundles — name search alone systematically fails (by design in the assessment).
3. **Anbudsregisteret** HTML parsing may break if site layout changes.
4. **Estimated values** are framework ceilings from notices, not pack-level revenue.

## Visualisations

Generated by `python scripts/visualize.py`:

1. **01_value_by_molecule** — headline estimated value vs molecule
2. **02_notice_lifecycle** — prior info / competition / intent by molecule
3. **03_strength_distribution** — pack strength spread from virkestoffliste
4. **04_detection_methods** — name vs ATC vs LIS-ref matching
5. **05_publication_timing** — when notices were published

See `visualizations/interpretations.md` for chart-by-chart commentary.

### Analytical summary

- **Where the money is:** Lenalidomide and oncology frameworks (LIS 2207, where Axitinib lives) show the largest headline NOK — but these are multi-molecule bundles with incumbent complexity.
- **Where volume/strength complexity is:** Everolimus and Lenalidomide have the widest strength portfolios in pack data.
- **Supplier crowding:** Public notices rarely disclose winners without login; supplier fields are mostly empty by design.
- **Timing:** Paliperidone **2601c** (2026) and Everolimus **2632a** (2025) are the most time-relevant bid opportunities in the dataset.

## Recommendation

**Prioritise Paliperidone (LIS 2601c)** for a near-term generics bid.

**Why:** active 2026 competition, standalone virkestoff tender (not a massive oncology bundle), name and ATC discovery both work, and pack structure is relatively contained (oral + low-dose injection lines).

**What would change my mind:**

- Login-access prisskjema showing very low volumes or a single locked-in supplier on injection presentations
- Learning that 2601c is predominantly continuation of existing Invega/Xeplion contracts with switch barriers
- A better risk-adjusted return on **Anagrelide (2507gj)** if pack-level data shows uncrowded supply and full contestability of the ~10 MNOK framework

**I would not prioritise Axitinib** on headline value alone: it sits inside LIS 2207 Onkologi (~3.2 BNOK bundle) where bidding means competing across dozens of oncology molecules, not a single SKU.

## Time spent

Approximately **5 hours** (source discovery, pipeline implementation, parsing, visualisation, documentation).

## What I would do next

1. Register for Doffin API key and wire authenticated document download
2. Supplier login to Mercell/Ivalua for prisskjema and forbruk columns
3. Add regression tests for matching and Norwegian number parsing
4. Link notices via `procedure-identifier` across TED lifecycle versions
5. Integrate Felleskatalogen / Legemiddelverket for max price and item numbers where published

## AI assistance

Built with AI-assisted development (Cursor). All source choices, matching logic, empty-field policy, and the bid recommendation are documented above and defensible in review.
