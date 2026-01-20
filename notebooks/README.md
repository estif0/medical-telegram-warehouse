# notebooks/

Jupyter notebooks for data exploration, analysis, and demonstration.

## Guidelines

- **Always import from `/src`** if modules are available (check first!)
- **Markdown cells** explain what each analysis section does
- **Code is narrative** - tells a story about the data
- **Visualizations** use plotly/matplotlib with clear titles and labels
- **Conclusions** summarize key findings

## Notebooks

**Status:** 2/4 notebooks complete

### `01_data_exploration.ipynb` ✅
Raw data exploration and profiling.

**Objectives:**
- Explore raw message data from data lake
- Data quality assessment
- Basic statistics (message count, date range, etc.)
- Channel distribution

**Data:** 3 channels scraped (CheMed123, lobelia4cosmetics, tikvahpharma)

### `02_star_schema_analysis.ipynb` ✅
Dimensional model analysis and star schema demonstration.

**Objectives:**
- Query transformed data from marts
- Show fact/dimension relationships
- Demonstrate query patterns on star schema
- Compare performance

**Models:** 4 dbt models (1 staging, 3 marts)

### `03_yolo_analysis.ipynb` ⏳
YOLO object detection results analysis.

**Objectives:**
- Analyze detected objects across images
- Compare image categories by channel
- Correlate visual content with engagement metrics
- Identify patterns

**Data:** 608 images with detections available

### `04_api_demo.ipynb` ⏳
API endpoint demonstrations.

**Objectives:**
- Show real API requests and responses
- Demonstrate all 8 endpoints
- Example use cases
- Response interpretation

**API:** FastAPI running at http://localhost:8000

## Running Notebooks

```bash
# Start Jupyter
jupyter notebook

# Or JupyterLab
jupyter lab
```

## Best Practices

1. Use relative imports for src modules
2. Add docstrings explaining analysis sections
3. Clean outputs before committing
4. Use descriptive variable names
5. Include interpretations of findings
6. Add visualizations with titles/labels
