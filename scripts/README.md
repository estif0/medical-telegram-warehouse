# scripts/

Executable scripts for running pipeline components.

**Status:** ✅ All scripts complete and tested

## Available Scripts

### `run_scraper.py` ✅
Extract messages and images from Telegram channels.

```bash
python scripts/run_scraper.py --channels CheMed123 lobelia4cosmetics tikvahpharma --days 7
```

**Output:** JSON files in `data/raw/telegram_messages/` and images in `data/raw/images/`

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
./scripts/run_dbt.sh docs generate  # Generate documentation
```

### `run_yolo_detection.py` ✅
Run YOLO object detection on all scraped images.

```bash
python scripts/run_yolo_detection.py --input data/raw/images --output data/processed/detections.csv
```

**Output:** Detection results in `data/processed/detections.csv` (608 detections)

### `run_api.py` ✅
Start FastAPI development server.

```bash
python scripts/run_api.py --port 8000 --reload
```

**Access:** http://localhost:8000/docs

### `run_dagster.py` ✅
Launch Dagster orchestration server.

```bash
python scripts/run_dagster.py
```

**Access:** http://localhost:3000

### `test_dagster.py` ✅
Test Dagster configuration.

```bash
python scripts/test_dagster.py
```

### `test_db_connection.py` ✅
Test database connectivity.

```bash
python scripts/test_db_connection.py
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

### `load_sample_data.py` ✅
Load sample/test data for development.

```bash
python scripts/load_sample_data.py
```

## Complete Pipeline Execution

### Manual Execution (Step-by-Step)

```bash
# 1. Scrape data from Telegram
python scripts/run_scraper.py --channels CheMed123 lobelia4cosmetics tikvahpharma

# 2. Load to database
python scripts/create_raw_table.py
python scripts/load_raw_data.py --all

# 3. Build dbt models
./scripts/run_dbt.sh run
./scripts/run_dbt.sh test

# 4. Run YOLO detection
python scripts/run_yolo_detection.py

# 5. Start API
python scripts/run_api.py

# 6. Verify everything
python scripts/verify_models.py
pytest tests/ -v
```

### Automated Execution (Dagster)

```bash
# Start Dagster and run orchestrated pipeline
python scripts/run_dagster.py

# Access Dagster UI at http://localhost:3000
# Jobs will run on schedule or can be triggered manually
```

## Configuration

All scripts read from `.env`:
```
TELEGRAM_API_ID=...
POSTGRES_HOST=localhost
POSTGRES_DB=medical_warehouse
...
```
