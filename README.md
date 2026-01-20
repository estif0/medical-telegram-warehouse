# Medical Telegram Warehouse

An end-to-end data pipeline for extracting, transforming, and analyzing data from Ethiopian medical business Telegram channels using **dbt**, **Dagster**, and **YOLOv8**.

## Quick Start

### 1. Prerequisites
- Python 3.10+
- Docker & Docker Compose
- PostgreSQL (via Docker)
- Git

### 2. Clone & Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd medical-telegram-warehouse

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials:
# - Telegram API credentials from https://my.telegram.org
# - Database passwords
nano .env
```

### 4. Start Database
```bash
# Start PostgreSQL with Docker
docker-compose up -d

# Verify database is running
docker-compose ps
```

### 5. Test Connection
```bash
# Test database connectivity
python scripts/test_db_connection.py
```

### 6. Run the Pipeline
```bash
# Scrape data from Telegram
python scripts/run_scraper.py --channels CheMed123 lobelia4cosmetics tikvahpharma

# Load and transform with dbt
python scripts/load_raw_data.py --all
./scripts/run_dbt.sh run

# Enrich with YOLO detection
python scripts/run_yolo_detection.py

# Start API for querying insights
python scripts/run_api.py

# Or use Dagster for orchestrated pipeline
python scripts/run_dagster.py
```

## Project Structure

```
medical-telegram-warehouse/
├── src/                    # Modular OOP code
│   ├── scraper/           # Telegram scraping modules
│   ├── database/          # Database connection & loading
│   ├── yolo/              # Object detection modules
│   └── orchestration/     # Dagster pipeline
├── api/                   # FastAPI application
├── medical_warehouse/     # dbt project
├── notebooks/             # Jupyter analysis notebooks
├── tests/                 # Unit & integration tests
├── scripts/               # Executable scripts
├── data/                  # Data lake (raw/processed)
├── demos/                 # Reference implementations
├── docs/                  # Project documentation
└── logs/                  # Application logs
```

## Current Status

- ✅ **Task 1**: Scraper + Data Lake (3 channels, 608 images)
- ✅ **Task 2**: dbt Star Schema (39/39 tests passing)
- ✅ **Task 3**: YOLO Object Detection (608 detections)
- ✅ **Task 4**: Analytical API (8 endpoints)
- ✅ **Task 5**: Dagster Pipeline Orchestration (4 jobs, 3 schedules)

**Test Coverage:** 79/79 tests passing ✅

## Quick Commands

```bash
# Run scraper
python scripts/run_scraper.py --channels CheMed123 lobelia4cosmetics tikvahpharma

# Load data & build dbt models
python scripts/load_raw_data.py --all
./scripts/run_dbt.sh run

# Run YOLO detection
python scripts/run_yolo_detection.py

# Start API server
python scripts/run_api.py

# Start Dagster orchestration
python scripts/run_dagster.py

# Run all tests
pytest tests/ -v         # 79 Python tests passing
./scripts/run_dbt.sh test  # 39 dbt tests passing
```

## Development Workflow

See [docs/local/steps.md](docs/local/steps.md) for detailed implementation steps.

## Key Technologies

- **Data Extraction**: Telethon
- **Database**: PostgreSQL
- **Transformation**: dbt
- **Enrichment**: YOLOv8
- **API**: FastAPI
- **Orchestration**: Dagster
- **Containerization**: Docker

## Documentation

- [Project Overview](docs/local/project-overview.md)
- [Implementation Steps](docs/local/steps.md)
- [Interim Report](docs/INTERIM_REPORT.md)
- [Copilot Instructions](.github/copilot-instructions.md)

## API Documentation

Once the API is running, access interactive documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Dagster UI

Once Dagster is running, access the orchestration dashboard:
- **Dagster UI**: http://localhost:3000

## Project Statistics

- **Lines of Code**: ~3,500+ (excluding tests)
- **Test Coverage**: 79 tests, 80%+ coverage
- **Git Commits**: 35+ meaningful commits
- **Pull Requests**: 4 feature branches merged
- **Channels Scraped**: 3 (CheMed123, lobelia4cosmetics, tikvahpharma)
- **Images Processed**: 608 with YOLO detection
- **API Endpoints**: 8 analytical endpoints
- **dbt Models**: 4 (1 staging, 3 marts)
- **Dagster Jobs**: 4 orchestration jobs

## License

MIT
