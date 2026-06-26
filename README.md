# Data Engineering Event Pipeline

A Python data engineering pipeline that simulates ingesting, validating, and cleaning a messy real-world e-commerce event stream. The pipeline generates synthetic event data with intentional noise, then processes it through three stages to produce a clean, typed dataset.

---

## Pipeline Architecture

```
src/ingest.py  →  src/validate.py  →  src/load.py
    │                   │                  │
 data/raw/         data/staging/      data/cleaned/
 (raw JSON)     (valid + invalid CSV)  (cleaned CSV)
```

| Stage | Script | What it does |
|---|---|---|
| Ingest | `src/ingest.py` | Generates 3 raw JSON files (~10k events each) with intentional noise |
| Validate | `src/validate.py` | Deduplicates, validates, and splits into valid/invalid staging CSVs |
| Load | `src/load.py` | Casts types, sorts by timestamp, writes final cleaned CSV |

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## How to Run

Run the full pipeline:

```bash
python scripts/run_pipeline.py
```

Or run stages individually:

```bash
python src/ingest.py
python src/validate.py
python src/load.py
```

---

## Data Schema

| Field | Type | Required | Description |
|---|---|---|---|
| `event_id` | string | yes | Unique event identifier (`evt_000001`) |
| `user_id` | integer | yes | User identifier (1–10000) |
| `event_type` | string | yes | Type of interaction (see allowed values below) |
| `timestamp` | datetime | yes | UTC time the event occurred |
| `source` | string | no | Traffic source (web, mobile_ios, etc.) |
| `metadata` | string | no | Free-text description of the event |

**Allowed `event_type` values:** `page_view`, `scroll`, `search`, `add_to_cart`, `remove_from_cart`, `purchase`

---

## Validation Rules

A record is marked **invalid** if any of the following are true:

- A required field is missing or null
- `event_type` is not in the allowed values list (after case normalization)
- `timestamp` is not a valid ISO datetime, or is in the future

Case variants like `PAGE_VIEW`, `Search`, and `ADD_TO_CART` are normalized to lowercase before validation, so they are recovered rather than rejected.

Duplicate records (identical raw events) are detected in O(1) time via hashing and written to the invalid staging file.

`source` and `metadata` are optional — null values do not invalidate a record.

---

## Output Files

| File | Description |
|---|---|
| `data/raw/events_2025_01_0{0,1,2}.json` | Raw generated event data |
| `data/staging/events_valid.csv` | Records that passed all validation checks |
| `data/staging/events_invalid.csv` | Records that failed, with an `error_reason` column |
| `data/cleaned/events_cleaned.csv` | Final output: typed, sorted by timestamp |
| `data_validation_summary.json` | Run statistics (see sample below) |
| `data_summary.log` | Structured log of each pipeline run |

---

## Intentional Noise (Ingest)

The ingest stage generates data that mimics common real-world data quality issues:

- **Missing fields** (~5% of events are missing one or more fields)
- **Null values** (all fields have a small probability of being null)
- **Duplicate events** (~2% of events are appended twice)
- **Case variants** (`PAGE_VIEW`, `Search`, `ADD_TO_CART`, `REMOVE_FROM_CART`, `Purchase`)
- **Invalid sources** (`mobil`, `hsearch`, `WEB`, `unknown_source`)

This results in roughly 20–25% of records being flagged as invalid on a typical run.

---

## Sample Validation Summary

```json
{
    "run_metadata": {
        "run_id": "2026_06_26",
        "input_files": ["events_2025_01_00.json", "events_2025_01_01.json", "events_2025_01_02.json"],
        "pipeline_stage": "data_validation",
        "runtime": "3.27 seconds"
    },
    "data_statistics": {
        "total_records": 29062,
        "valid_records": 22160,
        "invalid_records": 6902,
        "percent_invalid": "23.75%"
    },
    "failure_analysis": {
        "duplicate_events": 582,
        "invalid_event_type": 556,
        "invalid_timestamp": 791,
        "missing_event_id": 1427,
        "missing_user_id": 1401,
        "missing_event_type": 1370,
        "missing_timestamp": 1377
    },
    "null_rates": {
        "event_type": "6.76%",
        "timestamp": "7.61%",
        "source": "6.82%",
        "metadata": "13.66%"
    }
}
```
