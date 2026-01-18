# scripts/

Executable scripts for running pipeline components.

## Available Scripts

### `run_scraper.py`
Extract messages and images from Telegram channels.

```bash
python scripts/run_scraper.py --channels "CheMed123" "lobelia4cosmetics" --days 7
```

**Options:**
- `--channels` - Channel names to scrape (space-separated)
- `--days` - Number of days to scrape (default: 30)
- `--output` - Data lake output path (default: `data/raw/`)
- `--log-level` - Log level: DEBUG, INFO, WARNING (default: INFO)

### `load_raw_data.py`
Load raw JSON data from data lake to PostgreSQL.

```bash
python scripts/load_raw_data.py --source data/raw/telegram_messages/
```

**Options:**
- `--source` - Path to raw data directory
- `--incremental` - Only load new files (default: False)
- `--validate` - Validate data before loading (default: True)

### `run_yolo_detection.py`
Run object detection on downloaded images.

```bash
python scripts/run_yolo_detection.py --input data/raw/images/ --output data/detections.csv
```

**Options:**
- `--input` - Path to images directory
- `--output` - CSV output file for results
- `--model` - YOLO model size (nano, small, medium; default: nano)
- `--confidence` - Confidence threshold (0.0-1.0; default: 0.5)
- `--batch-size` - Batch processing size (default: 32)

### `run_api.py`
Start FastAPI development server.

```bash
python scripts/run_api.py --host 0.0.0.0 --port 8000
```

**Options:**
- `--host` - Server host (default: 0.0.0.0)
- `--port` - Server port (default: 8000)
- `--reload` - Auto-reload on code changes (default: True)

### `run_dagster.py`
Launch Dagster dev server for pipeline orchestration.

```bash
python scripts/run_dagster.py
```

Starts the Dagster UI at http://localhost:3000

### `test_db_connection.py`
Test PostgreSQL database connectivity.

```bash
python scripts/test_db_connection.py
```

Displays database version and schemas.

## Configuration

All scripts read from `.env`:
```
TELEGRAM_API_ID=...
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=medical_warehouse
...
```

## Running All Scripts

```bash
# Full pipeline (development)
python scripts/run_scraper.py
python scripts/load_raw_data.py
dbt run --project-dir medical_warehouse
python scripts/run_yolo_detection.py
python scripts/run_api.py
```

## Error Handling

All scripts include:
- Input validation
- Comprehensive error messages
- Logging to `logs/` directory
- Recovery mechanisms where applicable

Run with `--help` for detailed options:
```bash
python scripts/run_scraper.py --help
```
