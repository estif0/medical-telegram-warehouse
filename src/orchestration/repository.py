"""
Dagster repository (Definitions) for Medical Telegram Warehouse.

This module defines all Dagster components (assets, jobs, schedules, resources)
and makes them available to the Dagster daemon and UI.
"""

from dagster import Definitions, load_assets_from_modules

from . import assets
from .jobs import daily_etl_job, scrape_and_load_job, transform_job, enrich_job
from .schedules import (
    daily_pipeline_schedule,
    frequent_scrape_schedule,
    daily_transform_schedule,
)
from .resources import get_default_resources


# Load all assets from the assets module
all_assets = load_assets_from_modules([assets])

# Define the Dagster repository
defs = Definitions(
    assets=all_assets,
    jobs=[daily_etl_job, scrape_and_load_job, transform_job, enrich_job],
    schedules=[
        daily_pipeline_schedule,
        frequent_scrape_schedule,
        daily_transform_schedule,
    ],
    resources=get_default_resources(),
)
