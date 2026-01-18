# Medical Telegram Warehouse: Interim Report

**Project:** Data Platform for Ethiopian Medical Businesses  
**Organization:** Kara Solutions  
**Date:** January 18, 2026  
**Team Members:** Estifanose Sahilu

---

## 1. Executive Summary

This report presents the interim progress on building an end-to-end data platform for Kara Solutions to generate actionable insights from Ethiopian medical business Telegram channels. We have successfully completed the foundation: data extraction (Task 1) and dimensional modeling (Task 2), establishing a robust ELT pipeline with 77 passing tests (38 Python, 39 dbt). The platform is ready for enrichment with computer vision (Task 3), API development (Task 4), and orchestration (Task 5).

## 2. Business Objective and Architecture

### 2.1 Problem Statement

Kara Solutions requires a scalable data platform to analyze Ethiopian medical businesses operating on Telegram, answering critical questions:

- What are the most frequently mentioned medical products across channels?
- How do prices and availability vary between channels?
- Which channels leverage visual content most effectively?
- What are the daily and weekly posting trends in health-related topics?

### 2.2 Technical Approach

We implemented a modern **ELT (Extract, Load, Transform)** architecture:

1. **Extract:** Telegram API (Telethon) → Data Lake (partitioned JSON + images)
2. **Load:** Python loaders → PostgreSQL raw schema
3. **Transform:** dbt → Star schema (staging → dimensional marts)

This approach ensures data reliability, scalability, and analytical optimization through dimensional modeling.

### 2.3 Architecture Overview

```
Telegram Channels → [Telethon Scraper] → Data Lake (raw/)
                                              ↓
                         [Python Data Loader] → PostgreSQL (raw schema)
                                              ↓
                              [dbt Transformations] → Star Schema
                                              ↓
                         Staging Views → Dimension Tables + Fact Table
```

---

## 3. Completed Work: Tasks 1 & 2

### 3.1 Task 1: Data Scraping and Collection

**Implementation:**
- **Technology:** Telethon library for Telegram API access
- **Channels Scraped:** 3 medical/pharmaceutical channels (CheMed123, lobelia4cosmetics, tikvahpharma)
- **Data Collected:** 17 messages with full metadata (message_id, channel_name, date, text, views, forwards, replies)
- **Images Downloaded:** Organized by channel in `data/raw/images/{channel_name}/`

**Data Lake Structure:**
```
data/raw/
├── telegram_messages/
│   └── YYYY-MM-DD/
│       ├── channel_name.json
│       └── _manifest.json
└── images/
    └── {channel_name}/
        └── {message_id}.jpg
```

This partitioned structure enables efficient incremental loading and historical tracking.

**Testing:** 11 unit tests validate data lake management and scraping logic (100% passing).

### 3.2 Task 2: Data Modeling and Transformation

**Star Schema Design:**

Our dimensional model follows Kimball methodology for optimal analytical performance:

```
                    ┌─────────────────┐
                    │  dim_channels   │
                    │─────────────────│
                    │ channel_key (PK)│
                    │ channel_name    │
    ┌───────────────│ total_posts     │
    │               │ avg_views       │
    │               │ media_percentage│
    │               │ activity_level  │
    │               └─────────────────┘
    │                        ▲
    │                        │
    │               ┌─────────────────┐
    │               │  fct_messages   │
    │               │─────────────────│
    │               │ message_id (PK) │
    └───────────────│ channel_key (FK)│
                    │ date_key (FK)   │───────┐
                    │ message_text    │       │
                    │ views, forwards │       │
                    │ engagement_level│       │
                    │ forward_rate    │       │
                    └─────────────────┘       │
                                             │
                                             ▼
                                    ┌─────────────────┐
                                    │   dim_dates     │
                                    │─────────────────│
                                    │ date_key (PK)   │
                                    │ full_date       │
                                    │ year, quarter   │
                                    │ month, week     │
                                    │ is_weekend      │
                                    └─────────────────┘
```

**Dimensions:**
- `dim_channels` (3 rows): Channel-level aggregations including posting frequency, engagement metrics, and activity classification
- `dim_dates` (2,574 rows): Complete date dimension from 2020-2027 using `dbt_utils.date_spine` for comprehensive time-based analysis

**Fact Table:**
- `fct_messages` (17 rows): Grain = one row per message, containing foreign keys to dimensions, message attributes, and calculated engagement metrics

**Staging Layer:**

The `stg_telegram_messages` view implements critical transformations:
- **Type Casting:** Convert text fields to appropriate types (timestamp, bigint, integer)
- **Standardization:** Lowercase channel names, trim whitespace, consistent null handling
- **Data Quality Filters:** Remove records with null keys, future dates, or negative metrics
- **Enrichment:** Calculate `message_length`, `content_type` (with_media/text_only), `is_empty_text`

**Data Quality Issues and Resolutions:**

| Issue                       | Impact                   | Resolution                         |
| --------------------------- | ------------------------ | ---------------------------------- |
| Inconsistent channel naming | Join failures            | Lowercase and trim in staging      |
| Missing media flags         | Incorrect categorization | COALESCE to FALSE default          |
| Future-dated messages       | Invalid analytics        | Filter in staging WHERE clause     |
| Negative view counts        | Data integrity           | Validation + custom dbt test       |
| Empty message text          | Skewed text analysis     | `is_empty_text` flag for filtering |

**dbt Testing Framework:**

Implemented 39 dbt tests (100% passing):
- **Unique/Not Null (26 tests):** Primary keys, foreign keys, and critical columns
- **Relationships (2 tests):** Foreign key integrity between fact and dimensions
- **Accepted Values (5 tests):** Enum-like fields (content_type, engagement_level, activity_level)
- **Custom Data Quality (3 tests):** 
  - `assert_no_future_messages.sql` - Prevents temporal anomalies
  - `assert_positive_views.sql` - Ensures metric validity
  - `assert_valid_channel_names.sql` - Enforces naming standards

**Python Testing:** 27 additional unit tests for database connector and data loader modules ensure reliability at every layer.

### 3.3 Key Accomplishments

✅ **Robust Data Pipeline:** From Telegram API to dimensional model  
✅ **High Data Quality:** 77/77 tests passing (38 Python + 39 dbt)  
✅ **Scalable Architecture:** Partitioned data lake + star schema  
✅ **Documentation:** Comprehensive docstrings, type hints, and schema definitions  
✅ **Best Practices:** OOP design, error handling, logging, version control  

**Sample Insights Enabled:**
- lobelia4cosmetics: 2,164 avg views, 100% media usage
- CheMed123: 1,504 avg views, 83% media usage
- High engagement posts (5,600 views) correlate with promotional content

---

## 4. Next Steps: Tasks 3-5

### 4.1 Task 3: Data Enrichment with YOLOv8

**Objective:** Classify images to understand visual content impact on engagement.

**Implementation Plan:**
1. Install Ultralytics YOLOv8 nano model for efficiency
2. Implement `YOLODetector` class to process downloaded images
3. Categorize images based on detected objects:
   - `promotional`: Person + product → marketing content
   - `product_display`: Bottle/container → product showcase
   - `lifestyle`: Person, no product → lifestyle marketing
   - `other`: Neither pattern detected
4. Create `fct_image_detections` dbt model with detection results
5. Analyze: Do promotional images drive higher engagement?

**Technical Challenge:** Pre-trained YOLO models are optimized for common objects (person, bottle), not domain-specific medical products. We'll validate classification accuracy on a sample and consider fine-tuning if needed.

### 4.2 Task 4: Analytical API with FastAPI

**Objective:** Expose insights through RESTful endpoints for downstream applications.

**Planned Endpoints:**
- `GET /api/reports/top-products?limit=10` - Most mentioned products
- `GET /api/channels/{name}/activity` - Time-series posting patterns
- `GET /api/search/messages?query=paracetamol` - Full-text message search
- `GET /api/reports/visual-content` - Image category distribution by channel

**Technical Approach:** FastAPI with SQLAlchemy for efficient querying of marts, Pydantic for validation, and automatic OpenAPI documentation.

### 4.3 Task 5: Pipeline Orchestration with Dagster

**Objective:** Automate the end-to-end pipeline with scheduling and monitoring.

**Pipeline Assets:**
1. `scrape_telegram` → `load_raw_data` → `transform_dbt` → `enrich_yolo`
2. Daily schedule at 06:00 UTC
3. Failure alerts and retry logic
4. Dependency management across tasks

**Technical Challenge:** Coordinating dependencies between Python scripts and dbt CLI commands within Dagster's asset model.

### 4.4 Timeline

- **Task 3 (YOLO):** 2 days (Jan 19-20)
- **Task 4 (API):** 1 day (Jan 20)
- **Task 5 (Dagster):** 1 day (Jan 20)
- **Final Testing & Documentation:** Ongoing

---

## 5. Conclusion

We have established a production-ready foundation for the Medical Telegram Warehouse with a complete ELT pipeline and dimensional data model. All 77 tests passing demonstrates data quality and system reliability. The star schema enables efficient analytical queries for business insights. With the infrastructure proven, we are positioned to rapidly implement enrichment (YOLO), API exposure, and orchestration to deliver a complete, automated data product by the final deadline (January 20, 2026, 8:00 PM UTC).

**Key Success Metrics:**
- ✅ 100% test coverage on critical components
- ✅ Scalable architecture supporting future growth
- ✅ Clean, maintainable codebase following best practices
- ✅ Comprehensive documentation enabling team collaboration

The platform is ready to answer the business questions that motivated this project, with upcoming visual analysis providing deeper insights into content effectiveness across Ethiopian medical Telegram channels.
