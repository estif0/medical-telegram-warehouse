# FastAPI Analytical API

REST API for querying the Medical Telegram Warehouse and accessing analytical insights about Ethiopian medical business Telegram channels.

**Status:** ✅ Complete - 15/15 tests passing

## Features

- ✅ **Product Analytics**: Top mentioned medical products and trends
- ✅ **Visual Content Statistics**: Image analysis and object detection insights (608 images)
- ✅ **Channel Activity**: Daily metrics and engagement patterns (3 channels)
- ✅ **Message Search**: Full-text search across all messages with filters
- ✅ **Health Monitoring**: Database connection status and API health

**Total Endpoints:** 8 analytical endpoints

## Structure

```
api/
├── main.py           # FastAPI application entry point
├── database.py       # Database connection & session management
├── schemas.py        # Pydantic request/response models
└── routes/           # Endpoint route modules
    ├── reports.py    # Analytics endpoints
    ├── channels.py   # Channel-specific endpoints
    └── search.py     # Message search endpoints
```

## API Endpoints

### Reports

#### `GET /api/reports/top-products`
Get top mentioned products across all channels.

**Parameters:**
- `limit` (int, optional): Number of products to return (1-100, default: 10)

**Response:**
```json
{
  "total_products": 3,
  "products": [
    {
      "product_name": "paracetamol",
      "mention_count": 15,
      "avg_views": 1250.5,
      "channels": ["CheMed123", "tikvahpharma"]
    }
  ]
}
```

#### `GET /api/reports/visual-content`
Get statistics about visual content and object detection.

**Parameters:**
- `channel` (str, optional): Filter by channel name

**Response:**
```json
{
  "total_images": 207,
  "images_with_detections": 143,
  "total_detections": 543,
  "categories": [...],
  "top_detected_classes": {
    "bottle": 226,
    "person": 173
  }
}
```

### Channels

#### `GET /api/channels/list`
Get list of all available channels with statistics.

**Response:**
```json
{
  "total_channels": 3,
  "channels": [...]
}
```

#### `GET /api/channels/{channel_name}/activity`
Get channel activity over time.

**Parameters:**
- `days` (int, optional): Number of days to analyze (1-365, default: 30)

**Response:**
```json
{
  "channel_name": "CheMed123",
  "total_messages": 150,
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-01-31"
  },
  "daily_activity": [...]
}
```

### Search

#### `GET /api/search/messages`
Search messages by keyword.

**Parameters:**
- `query` (str, required): Search query
- `channel` (str, optional): Filter by channel
- `has_image` (bool, optional): Filter by image presence
- `limit` (int, optional): Maximum results (1-100, default: 20)

**Response:**
```json
{
  "total_matches": 15,
  "query": "paracetamol",
  "messages": [...]
}
```

#### `GET /api/search/keywords`
Get most common keywords from messages.

**Parameters:**
- `limit` (int, optional): Number of keywords (1-100, default: 20)

**Response:**
```json
{
  "total_keywords": 10,
  "keywords": [
    {"keyword": "paracetamol", "count": 15},
    ...
  ]
}
```

### Health

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-01-20T10:30:00"
}
```

## Running the API

### Start the Server

```bash
# Basic usage
python scripts/run_api.py

# Custom port
python scripts/run_api.py --port 8080

# Development mode with auto-reload
python scripts/run_api.py --reload

# Multiple workers (production)
python scripts/run_api.py --workers 4
```

### Access Documentation

Once running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Testing

Run API tests:

```bash
pytest tests/test_api.py -v
```

**Test Coverage:**
- 15 comprehensive tests
- Tests root endpoints, reports, channels, search
- Tests validation and error handling
- Tests OpenAPI documentation generation
- **15/15 tests passing** ✅

## Architecture

### Database Connection

The API uses SQLAlchemy with connection pooling for efficient database access:

```python
from api.database import get_db
from fastapi import Depends

@router.get("/endpoint")
def endpoint(db: Session = Depends(get_db)):
    # Use db session
    pass
```

### Pydantic Models

All endpoints use Pydantic models for request/response validation:

```python
from api.schemas import MessageSearchResponse

@router.get("/search", response_model=MessageSearchResponse)
def search_endpoint():
    # Response automatically validated
    pass
```

### Error Handling

Global exception handler provides consistent error responses:

```python
{
  "detail": "Error message",
  "error": "Technical details"
}
```

## Configuration

Environment variables (in `.env`):

```env
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=telegram_warehouse
```

## Dependencies

- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `sqlalchemy` - ORM
- `psycopg2-binary` - PostgreSQL adapter
- `pydantic` - Data validation
- `python-dotenv` - Environment variables

## Notes

- **CSV Fallback**: Visual content endpoint falls back to CSV files if database unavailable
- **CORS**: Configured to allow all origins (restrict in production)
- **Rate Limiting**: Not implemented (add in production)
- **Authentication**: Not implemented (add for production deployment)

## Example Usage

```bash
# Search for paracetamol mentions
curl "http://localhost:8000/api/search/messages?query=paracetamol&limit=5"

# Get top products
curl "http://localhost:8000/api/reports/top-products?limit=10"

# Check channel activity
curl "http://localhost:8000/api/channels/CheMed123/activity?days=7"

# Get visual content stats
curl "http://localhost:8000/api/reports/visual-content"
```

## Production Deployment

For production deployment:

1. Set proper environment variables
2. Use multiple workers: `--workers 4`
3. Add authentication middleware
4. Implement rate limiting
5. Restrict CORS origins
6. Use HTTPS/TLS
7. Add logging and monitoring

