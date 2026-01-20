# Dagster Orchestration

Pipeline orchestration for the Medical Telegram Warehouse using Dagster.

## Overview

This module implements the complete data pipeline orchestration using Dagster, coordinating:
- Telegram data scraping
- Data loading to PostgreSQL
- dbt transformations
- YOLO object detection enrichment

## Structure

```
src/orchestration/
├── __init__.py          # Package initialization
├── assets.py            # Dagster assets (data pipeline steps)
├── jobs.py              # Dagster jobs (asset execution graphs)
├── schedules.py         # Automated schedule definitions
├── resources.py         # Shared resources (DB, configs, logger)
└── repository.py        # Dagster Definitions (main entry point)
```

## Jobs

### 1. `daily_etl_pipeline`
Complete end-to-end pipeline that runs all steps in sequence:
1. Scrape data from Telegram channels
2. Load raw data to PostgreSQL
3. Run dbt transformations (staging + marts)
4. Enrich with YOLO object detection

**Schedule:** Daily at 2:00 AM (Africa/Addis_Ababa)

### 2. `scrape_and_load`
Scrapes Telegram channels and loads data to database.

**Schedule:** Every 6 hours for frequent updates

### 3. `transform_only`
Runs only dbt transformations on existing data.

**Schedule:** Daily at 3:00 AM (after ETL pipeline)

### 4. `enrich_only`
Runs only YOLO object detection on images without existing detections.

**Schedule:** Manual execution

## Schedules

| Schedule                   | Job                | Frequency     | Time (UTC+3) |
| -------------------------- | ------------------ | ------------- | ------------ |
| `daily_etl_schedule`       | daily_etl_pipeline | Daily         | 2:00 AM      |
| `frequent_scrape_schedule` | scrape_and_load    | Every 6 hours | -            |
| `daily_transform_schedule` | transform_only     | Daily         | 3:00 AM      |

## Assets

Dagster assets represent data artifacts produced by the pipeline:

- **`raw_telegram_data`**: Scraped messages and images stored in data lake
- **`loaded_raw_data`**: Data loaded into PostgreSQL raw schema
- **`transformed_data`**: Cleaned and modeled data in staging_marts schema
- **`enriched_data`**: Data enriched with YOLO object detection results

## Resources

Shared resources available to all assets and jobs:

- **Database**: PostgreSQL connection for data warehouse operations
- **Configuration**: Environment variables and settings
- **Logger**: Centralized logging
- **File System**: Data lake storage access

## Running the Pipeline

### Start Dagster UI

```bash
# Using the startup script
python scripts/run_dagster.py

# Or directly
dagster dev -f src/orchestration/repository.py
```

The Dagster UI will be available at **http://localhost:3000**

### Execute Jobs Manually

#### Via UI
1. Open http://localhost:3000
2. Navigate to "Jobs" → Select a job
3. Click "Launchpad" → "Launch Run"

#### Via CLI
```bash
# Set DAGSTER_HOME
export DAGSTER_HOME=/home/voldi/Projects/ai-ml/medical-telegram-warehouse/.dagster

# Execute a job
dagster job execute -f src/orchestration/repository.py -j daily_etl_pipeline

# Execute specific assets
dagster asset materialize -f src/orchestration/repository.py -a raw_telegram_data
```

### Enable Schedules

Schedules are automatically loaded but need to be turned ON:

1. Open Dagster UI
2. Navigate to "Automation" → "Schedules"
3. Toggle each schedule to "Running"

## Testing

Test the Dagster setup:

```bash
python scripts/test_dagster.py
```

**Expected Output:**
```
✅ Found 4 jobs
✅ Found 3 schedules
✅ All tests passed!
```

## Configuration

### Environment Variables

Required in `.env`:
```env
# Database
POSTGRES_USER=warehouse_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=medical_warehouse
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Telegram API
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=your_phone

# Data Paths
DATA_RAW_PATH=data/raw
DATA_PROCESSED_PATH=data/processed
LOGS_PATH=logs

# YOLO
YOLO_MODEL=yolov8n.pt
YOLO_CONFIDENCE_THRESHOLD=0.25
```

### Dagster Configuration

Configuration file: `.dagster/dagster.yaml`

```yaml
storage:
  sqlite:
    base_dir: .dagster/storage

run_launcher:
  module: dagster.core.launcher
  class: DefaultRunLauncher

telemetry:
  enabled: false
```

## Dependencies

- `dagster` - Orchestration framework
- `dagster-webserver` - Web UI
- All project dependencies (scraper, database, dbt, YOLO)

## Monitoring

### Via Dagster UI

- **Runs**: View execution history and status
- **Assets**: Check materialization status and lineage
- **Logs**: Detailed execution logs per run
- **Schedules**: Monitor schedule ticks and runs

### Via Logs

Pipeline logs are stored in:
- Dagster logs: `.dagster/logs/`
- Application logs: `logs/`

## Troubleshooting

### Dagster Won't Start

```bash
# Check if port 3000 is in use
lsof -i :3000

# Kill existing Dagster processes
pkill -f dagster

# Restart cleanly
python scripts/run_dagster.py
```

### Jobs Fail to Execute

1. Check logs in Dagster UI
2. Verify database connection
3. Ensure all dependencies are installed
4. Check environment variables

### Schedules Not Running

1. Ensure Dagster daemon is running
2. Turn schedules ON in UI
3. Check schedule tick logs

## Production Deployment

For production deployment:

1. **Use persistent storage** (PostgreSQL instead of SQLite)
2. **Enable monitoring** and alerts
3. **Configure retries** for failed runs
4. **Set up secrets management** (don't use .env files)
5. **Use production launchers** (Kubernetes, Docker, etc.)

See [Dagster deployment documentation](https://docs.dagster.io/deployment) for details.

## Architecture

```
┌─────────────────────────────────────────────────┐
│         Dagster Orchestration Layer             │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────┐    ┌───────────────────┐    │
│  │  Schedules   │───▶│   Jobs/Assets     │    │
│  └──────────────┘    └───────────────────┘    │
│                              │                  │
│                              ▼                  │
│  ┌──────────────────────────────────────────┐ │
│  │         Pipeline Steps                    │ │
│  │  1. Scrape  → 2. Load → 3. Transform    │ │
│  │                    ↓                      │ │
│  │              4. Enrich (YOLO)            │ │
│  └──────────────────────────────────────────┘ │
│                                                 │
└─────────────────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  PostgreSQL Warehouse │
        └───────────────────────┘
```

## Next Steps

- Set up Slack/email notifications for failures
- Add data quality checks as assets
- Implement incremental materialization
- Add backfill capabilities
- Configure cloud deployment
