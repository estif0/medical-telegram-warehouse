"""
Dagster assets for the Medical Telegram Warehouse pipeline.

Assets represent data products that are materialized by the pipeline.
Each asset corresponds to a stage in the ETL/ELT process.
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from dagster import asset, AssetExecutionContext, RetryPolicy, Output
import pandas as pd


# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DBT_DIR = PROJECT_ROOT / "medical_warehouse"


@asset(
    description="Scrape messages and images from Telegram channels",
    retry_policy=RetryPolicy(max_retries=2, delay=60),
    group_name="extraction",
)
def raw_telegram_data(context: AssetExecutionContext) -> Dict[str, Any]:
    """
    Execute Telegram scraper to fetch messages from channels.

    Returns:
        Dict with scraping statistics (messages, images, channels)
    """
    context.log.info("Starting Telegram data scraping...")

    # Run scraper script
    scraper_script = SCRIPTS_DIR / "run_scraper.py"

    if not scraper_script.exists():
        context.log.warning(f"Scraper script not found at {scraper_script}")
        return {
            "status": "skipped",
            "messages_scraped": 0,
            "images_downloaded": 0,
            "timestamp": datetime.now().isoformat(),
        }

    try:
        result = subprocess.run(
            ["python3", str(scraper_script), "--limit", "50"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
        )

        context.log.info(f"Scraper output: {result.stdout}")
        if result.stderr:
            context.log.warning(f"Scraper errors: {result.stderr}")

        # Parse output for statistics (simple approach)
        messages_count = result.stdout.count("message") if result.stdout else 0

        return {
            "status": "success",
            "messages_scraped": messages_count,
            "timestamp": datetime.now().isoformat(),
            "return_code": result.returncode,
        }

    except subprocess.TimeoutExpired:
        context.log.error("Scraper timed out after 10 minutes")
        raise
    except Exception as e:
        context.log.error(f"Error running scraper: {e}")
        raise


@asset(
    description="Load raw JSON data into PostgreSQL raw schema",
    retry_policy=RetryPolicy(max_retries=2, delay=30),
    group_name="loading",
    deps=["raw_telegram_data"],
)
def loaded_raw_data(context: AssetExecutionContext) -> Dict[str, Any]:
    """
    Load raw Telegram data from JSON files into PostgreSQL.

    Returns:
        Dict with loading statistics
    """
    context.log.info("Loading raw data into PostgreSQL...")

    # Run data loader script
    loader_script = SCRIPTS_DIR / "load_raw_data.py"

    if not loader_script.exists():
        context.log.warning(f"Loader script not found at {loader_script}")
        return {
            "status": "skipped",
            "records_loaded": 0,
            "timestamp": datetime.now().isoformat(),
        }

    try:
        result = subprocess.run(
            ["python3", str(loader_script)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        context.log.info(f"Loader output: {result.stdout}")
        if result.stderr:
            context.log.warning(f"Loader errors: {result.stderr}")

        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "return_code": result.returncode,
        }

    except Exception as e:
        context.log.error(f"Error loading raw data: {e}")
        raise


@asset(
    description="Transform raw data into dimensional model using dbt",
    retry_policy=RetryPolicy(max_retries=2, delay=30),
    group_name="transformation",
    deps=["loaded_raw_data"],
)
def transformed_data(context: AssetExecutionContext) -> Dict[str, Any]:
    """
    Run dbt models to transform raw data into star schema.

    Returns:
        Dict with transformation statistics
    """
    context.log.info("Running dbt transformations...")

    try:
        # Run dbt models
        result = subprocess.run(
            ["dbt", "run", "--project-dir", str(DBT_DIR)],
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
        )

        context.log.info(f"dbt run output: {result.stdout}")
        if result.stderr:
            context.log.warning(f"dbt run warnings: {result.stderr}")

        # Run dbt tests
        test_result = subprocess.run(
            ["dbt", "test", "--project-dir", str(DBT_DIR)],
            capture_output=True,
            text=True,
            timeout=300,
        )

        context.log.info(f"dbt test output: {test_result.stdout}")

        # Parse dbt output for model count
        models_run = result.stdout.count("OK created") if result.stdout else 0
        tests_passed = test_result.stdout.count("PASS") if test_result.stdout else 0

        return {
            "status": "success",
            "models_run": models_run,
            "tests_passed": tests_passed,
            "timestamp": datetime.now().isoformat(),
            "return_code": result.returncode,
        }

    except Exception as e:
        context.log.error(f"Error running dbt: {e}")
        raise


@asset(
    description="Enrich data with YOLO object detection on images",
    retry_policy=RetryPolicy(max_retries=2, delay=60),
    group_name="enrichment",
    deps=["transformed_data"],
)
def enriched_data(context: AssetExecutionContext) -> Dict[str, Any]:
    """
    Run YOLO detection on images and store results.

    Returns:
        Dict with detection statistics
    """
    context.log.info("Running YOLO object detection...")

    # Run YOLO detection script
    yolo_script = SCRIPTS_DIR / "run_yolo_detection.py"

    if not yolo_script.exists():
        context.log.warning(f"YOLO script not found at {yolo_script}")
        return {
            "status": "skipped",
            "images_processed": 0,
            "timestamp": datetime.now().isoformat(),
        }

    # Output paths
    output_csv = PROJECT_ROOT / "data" / "processed" / "yolo_detections_dagster.csv"

    try:
        result = subprocess.run(
            [
                "python3",
                str(yolo_script),
                "--input",
                str(DATA_RAW_DIR / "images"),
                "--output",
                str(output_csv),
                "--confidence",
                "0.5",
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=1800,  # 30 minute timeout for YOLO processing
        )

        context.log.info(f"YOLO output: {result.stdout}")
        if result.stderr:
            context.log.warning(f"YOLO warnings: {result.stderr}")

        # Read detection results if CSV exists
        if output_csv.exists():
            df = pd.read_csv(output_csv)
            images_processed = (
                df["image_path"].nunique() if "image_path" in df.columns else 0
            )
            total_detections = len(df)

            context.log.info(
                f"Processed {images_processed} images, found {total_detections} detections"
            )

            return {
                "status": "success",
                "images_processed": images_processed,
                "total_detections": total_detections,
                "output_file": str(output_csv),
                "timestamp": datetime.now().isoformat(),
                "return_code": result.returncode,
            }
        else:
            return {
                "status": "completed",
                "images_processed": 0,
                "message": "No detections file generated",
                "timestamp": datetime.now().isoformat(),
            }

    except Exception as e:
        context.log.error(f"Error running YOLO detection: {e}")
        raise


@asset(
    description="Data warehouse ready for API queries",
    group_name="serving",
    deps=["enriched_data"],
)
def data_warehouse_ready(context: AssetExecutionContext) -> Dict[str, Any]:
    """
    Verify data warehouse is ready and accessible.

    Returns:
        Dict with warehouse status
    """
    context.log.info("Verifying data warehouse status...")

    try:
        # Simple verification - could add database connectivity check
        from api.database import test_connection

        db_connected = test_connection()

        return {
            "status": "ready" if db_connected else "unavailable",
            "database_connected": db_connected,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        context.log.warning(f"Could not verify database: {e}")
        return {
            "status": "unknown",
            "database_connected": False,
            "timestamp": datetime.now().isoformat(),
        }
