#!/usr/bin/env python3
"""
Dagster dev server startup script for Medical Telegram Warehouse.

This script launches the Dagster development server (dagster-webserver)
which provides the UI for monitoring and triggering pipeline runs.

Usage:
    python scripts/run_dagster.py
    python scripts/run_dagster.py --port 3001
    python scripts/run_dagster.py --host 0.0.0.0
"""

import argparse
import sys
import os
from pathlib import Path
import subprocess


def main():
    """Start Dagster development server."""
    parser = argparse.ArgumentParser(
        description="Start Dagster development server for pipeline orchestration"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host to bind the server to (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port to run the server on (default: 3000)",
    )
    parser.add_argument(
        "--dagster-home",
        type=str,
        default=None,
        help="Dagster home directory (default: .dagster in project root)",
    )

    args = parser.parse_args()

    # Set project root and dagster home
    project_root = Path(__file__).resolve().parent.parent
    dagster_home = args.dagster_home or str(project_root / ".dagster")

    # Ensure dagster_home is absolute path
    dagster_home = str(Path(dagster_home).resolve())

    Path(dagster_home).mkdir(parents=True, exist_ok=True)

    print(f"🚀 Starting Dagster development server...")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Dagster Home: {dagster_home}")
    print(f"   Project Root: {project_root}")
    print()
    print(f"📊 Dagster UI will be available at: http://{args.host}:{args.port}")
    print()
    print("Press Ctrl+C to stop the server")
    print("-" * 60)

    # Check if we're in a virtual environment
    venv_dagster = project_root / "venv" / "bin" / "dagster"
    if venv_dagster.exists():
        dagster_cmd = str(venv_dagster)
    else:
        dagster_cmd = "dagster"

    # Build dagster dev command
    cmd = [
        dagster_cmd,
        "dev",
        "-f",
        "src/orchestration/repository.py",
        "-h",
        args.host,
        "-p",
        str(args.port),
    ]

    try:
        # Run dagster dev with environment variables
        env = os.environ.copy()
        env["DAGSTER_HOME"] = dagster_home

        subprocess.run(cmd, cwd=project_root, env=env, check=True)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down Dagster server...")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting Dagster server: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("\n❌ Error: 'dagster' command not found.")
        print("   Please install Dagster: pip install dagster dagster-webserver")
        sys.exit(1)


if __name__ == "__main__":
    main()
