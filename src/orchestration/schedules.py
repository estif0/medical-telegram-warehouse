"""
Dagster schedules for the Medical Telegram Warehouse pipeline.

Schedules define when jobs should run automatically.
"""

from dagster import ScheduleDefinition
from .jobs import daily_etl_job, scrape_and_load_job, transform_job

# Schedule full ETL pipeline to run daily at 2 AM UTC
daily_pipeline_schedule = ScheduleDefinition(
    job=daily_etl_job,
    cron_schedule="0 2 * * *",  # At 2:00 AM every day
    execution_timezone="UTC",
    name="daily_etl_schedule",
    description="Run complete ETL pipeline daily at 2 AM UTC",
)

# Schedule scraping multiple times per day (every 6 hours)
frequent_scrape_schedule = ScheduleDefinition(
    job=scrape_and_load_job,
    cron_schedule="0 */6 * * *",  # Every 6 hours
    execution_timezone="UTC",
    name="frequent_scrape_schedule",
    description="Scrape Telegram data every 6 hours",
)

# Schedule transformation to run after daily scraping
daily_transform_schedule = ScheduleDefinition(
    job=transform_job,
    cron_schedule="30 2 * * *",  # At 2:30 AM every day (30 min after scraping)
    execution_timezone="UTC",
    name="daily_transform_schedule",
    description="Run dbt transformations daily at 2:30 AM UTC",
)
