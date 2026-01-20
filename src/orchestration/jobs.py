"""
Dagster jobs for the Medical Telegram Warehouse pipeline.

Jobs define the execution order and dependencies between assets.
"""

from dagster import define_asset_job, AssetSelection

# Define the main ETL job that runs all assets in order
daily_etl_job = define_asset_job(
    name="daily_etl_pipeline",
    description="Complete ETL pipeline: scrape → load → transform → enrich",
    selection=AssetSelection.all(),
    tags={"pipeline": "medical_telegram_warehouse", "environment": "production"},
)

# Job for just scraping and loading (partial pipeline)
scrape_and_load_job = define_asset_job(
    name="scrape_and_load",
    description="Scrape Telegram data and load into raw schema",
    selection=AssetSelection.groups("extraction", "loading"),
    tags={"pipeline": "medical_telegram_warehouse", "stage": "ingestion"},
)

# Job for just transformation (when raw data already exists)
transform_job = define_asset_job(
    name="transform_only",
    description="Run dbt transformations on existing raw data",
    selection=AssetSelection.groups("transformation"),
    tags={"pipeline": "medical_telegram_warehouse", "stage": "transformation"},
)

# Job for just enrichment (YOLO detection)
enrich_job = define_asset_job(
    name="enrich_only",
    description="Run YOLO detection on images",
    selection=AssetSelection.groups("enrichment"),
    tags={"pipeline": "medical_telegram_warehouse", "stage": "enrichment"},
)
