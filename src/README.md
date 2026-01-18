# src/

Modular, object-oriented Python code for the data pipeline.

**Status:** ✅ Scraper & Database modules complete | ⏳ YOLO & Orchestration in progress

## Modules

### `scraper/` ✅
Telegram data extraction and data lake management.

**Files:**
- `telegram_scraper.py` - Telethon-based scraper (11 tests passing)
- `data_lake_manager.py` - Data lake management (11 tests passing)

**Usage:**
```python
from src.scraper.telegram_scraper import TelegramScraper
from src.scraper.data_lake_manager import DataLakeManager

scraper = TelegramScraper(api_id, api_hash, phone)
messages = scraper.get_channel_messages("channel_name")

dlm = DataLakeManager()
dlm.save_message_json(messages, "channel_name")
```

### `database/` ✅
PostgreSQL database operations.

**Files:**
- `db_connector.py` - Connection & schema management (11 tests passing)
- `data_loader.py` - JSON to PostgreSQL loader (16 tests passing)

**Usage:**
```python
from src.database.db_connector import DatabaseConnector
from src.database.data_loader import DataLoader

db = DatabaseConnector()
db.connect()

loader = DataLoader(db)
loader.load_json_to_postgres("data/raw/telegram_messages/")
```

### `yolo/` ⏳
Object detection and image classification (Task 3 - in progress).

**Planned Files:**
- `yolo_detector.py` - YOLOv8 object detection
- `image_classifier.py` - Image categorization
- `detection_manager.py` - Detection result storage

**Usage:**
```python
# Coming soon in Task 3
from src.yolo.yolo_detector import YOLODetector

detector = YOLODetector(model="yolov8n.pt")
results = detector.detect_objects("path/to/image.jpg")
```

### `utils/`
Shared utilities and helpers.

**Files:**
- `logger.py` - Centralized logging configuration

**Usage:**
```python
from src.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("Starting data pipeline...")
```

### `orchestration/` ⏳
Dagster pipeline definitions (Task 5 - planned).

**Planned Files:**
- `assets.py` - Dagster assets
- `jobs.py` - Dagster jobs
- `schedules.py` - Pipeline schedules

## Dependencies

All dependencies are in `requirements.txt`. Install with:
```bash
pip install -r requirements.txt
```

## Standards

- **OOP**: Use classes for modularity
- **Type Hints**: All function signatures must have type hints
- **Docstrings**: Google-style docstrings for all classes/methods
- **Error Handling**: Comprehensive try-except with logging
- **Testing**: Unit tests in `tests/` for each module

## Testing

Run tests with:
```bash
pytest tests/ -v --cov=src
```

Target: 80%+ code coverage
