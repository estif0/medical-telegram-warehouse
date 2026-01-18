# scripts/

Executable scripts for running pipeline components.

**Status:** ✅ Scraper & dbt scripts ready | ⏳ YOLO & API scripts planned

## Available Scripts

### `run_scraper.py` ✅
Extract messages and images from Telegram channels.

```bash
python scripts/run_scraper.py --channels "CheMed123" "lobelia4cosmetics" --days 7
```

### `load_raw_data.py` ✅
Load raw JSON data from data lake to PostgreSQL.

```bash
python scripts/load_raw_data.py --all
# Or specific date: --date 2026-01-18
```

### `run_dbt.sh` ✅
Helper script to run dbt commands with proper environment.

```bash
./scripts/run_dbt.sh run   # Build models
./scripts/run_dbt.sh test  # Run tests (39/39 passing)
```

### `create_raw_table.py` ✅
Create raw.telegram_messages table in PostgreSQL.

```bash
python scripts/create_raw_table.py
```

### `verify_models.py` ✅
Verify dbt models and data in database.

```bash
python scripts/verify_models.py
```

### `run_yolo_detection.py` ⏳
Run object detection on images (Task 3 - planned).

### `run_api.py` ⏳
Start FastAPI development server (Task 4 - planned).

### `run_dagster.py` ⏳
Launch Dagster dev server (Task 5 - planned).

## Current Pipeline

```bash
# 1. Scrape data
python scripts/run_scraper.py

# 2. Load to database
python scripts/create_raw_table.py
python scripts/load_raw_data.py --all

# 3. Build dbt models
./scripts/run_dbt.sh run
./scripts/run_dbt.sh test

# 4. Verify
python scripts/verify_models.py
```

## Configuration

All scripts read from `.env`:
```
TELEGRAM_API_ID=...
POSTGRES_HOST=localhost
POSTGRES_DB=medical_warehouse
...
```
