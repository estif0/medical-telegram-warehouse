#!/usr/bin/env bash
#
# Helper script to run dbt commands with proper environment configuration.
#
# Usage:
#     ./scripts/run_dbt.sh debug
#     ./scripts/run_dbt.sh run
#     ./scripts/run_dbt.sh test
#

# Load environment variables from .env
set -a
source "$(dirname "$0")/../.env"
set +a

# Change to dbt project directory
cd "$(dirname "$0")/../medical_warehouse"

# Set profiles directory to current directory
export DBT_PROFILES_DIR=.

# Run dbt command with all arguments passed to script
dbt "$@"
