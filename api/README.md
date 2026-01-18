# api/

FastAPI application for exposing data warehouse insights through REST endpoints.

## Structure

```
api/
├── main.py           # FastAPI application entry point
├── database.py       # Database connection & session management
├── schemas.py        # Pydantic request/response models
├── routes/           # Endpoint route modules
│   ├── reports.py   # Analytics endpoints
│   ├── channels.py  # Channel-specific endpoints
│   └── search.py    # Message search endpoints
└── utils/           # Helper functions
    └── query_builder.py  # SQL query builders
```

## Key Endpoints

### Reports
- `GET /api/reports/top-products` - Top 10 mentioned medical products
- `GET /api/reports/visual-content` - Visual content statistics

### Channels
- `GET /api/channels/{channel_name}/activity` - Channel posting activity over time

### Search
- `GET /api/search/messages` - Search messages by keyword

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Access documentation
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

## Configuration

API settings are in `.env`:
```
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true
DATABASE_URL=postgresql://user:password@localhost:5432/medical_warehouse
```

## Response Format

All endpoints return JSON with consistent structure:
```python
{
    "status": "success",  # or "error"
    "data": {...},        # Endpoint-specific data
    "message": "Optional message",
    "timestamp": "2026-01-18T12:00:00Z"
}
```

## Testing

```bash
pytest tests/test_api.py -v
```

## Documentation

FastAPI automatically generates interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

See `schemas.py` for all request/response models with examples.
