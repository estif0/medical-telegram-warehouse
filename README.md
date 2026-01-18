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
python -c "from sqlalchemy import create_engine; import os; from dotenv import load_dotenv; load_dotenv(); engine = create_engine(os.getenv('DATABASE_URL')); print('✅ Database connected!' if engine.connect() else '❌ Connection failed')"
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

## Development Workflow

See [docs/local/steps.md](docs/local/steps.md) for detailed implementation steps.

## Tasks Overview

1. **Task 1**: Data Scraping & Collection (Telegram → Data Lake)
2. **Task 2**: Data Modeling & Transformation (dbt Star Schema)
3. **Task 3**: Data Enrichment (YOLO Object Detection)
4. **Task 4**: Analytical API (FastAPI Endpoints)
5. **Task 5**: Pipeline Orchestration (Dagster)

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
- [Copilot Instructions](.github/copilot-instructions.md)

## License

MIT
