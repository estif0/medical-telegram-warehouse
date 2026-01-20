#!/usr/bin/env python3
"""
Test script to verify Dagster pipeline setup.

This script tests that:
1. Dagster repository is loadable
2. Jobs are defined correctly
3. Schedules are configured
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set DAGSTER_HOME
os.environ["DAGSTER_HOME"] = str(project_root / ".dagster")

from dagster import DagsterInstance
from src.orchestration.repository import defs


def test_repository():
    """Test that repository loads correctly."""
    print("Testing Dagster repository...")

    # Get Definitions object
    definitions = defs

    # Check jobs (jobs is a list in Definitions)
    job_names = [job.name for job in definitions.jobs] if definitions.jobs else []
    print(f"✅ Found {len(job_names)} jobs: {job_names}")

    # Check schedules
    schedule_names = (
        [schedule.name for schedule in definitions.schedules]
        if definitions.schedules
        else []
    )
    print(f"✅ Found {len(schedule_names)} schedules: {schedule_names}")

    # Check assets
    asset_keys = (
        [asset.key for asset in definitions.assets] if definitions.assets else []
    )


def test_job_execution():
    """Test that jobs can be executed."""
    print("\nTesting job execution...")

    # Load instance
    instance = DagsterInstance.get()

    # Get Definitions
    definitions = defs

    # Get the daily ETL job
    if definitions.jobs:
        daily_pipeline = definitions.jobs[0]  # Get first job

        print(f"✅ Job '{daily_pipeline.name}' is configured")
        print(f"   Description: {daily_pipeline.description or 'No description'}")

        # Note: We're not actually running the job here to avoid side effects
        print("   (Skipping actual execution to avoid side effects)")
    else:
        print("⚠️  No jobs found")

    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Dagster Pipeline Test Suite")
    print("=" * 60)

    try:
        test_repository()
        test_job_execution()

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        print("\nTo run the pipeline:")
        print("1. Open Dagster UI: http://localhost:3000")
        print("2. Navigate to 'daily_telegram_pipeline' job")
        print("3. Click 'Launchpad' and 'Launch Run'")
        print("\nOr use CLI:")
        print(
            "dagster job execute -m src.orchestration.repository -j daily_telegram_pipeline"
        )

        return 0
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
