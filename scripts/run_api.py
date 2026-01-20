#!/usr/bin/env python3
"""
Start the FastAPI application.

This script launches the API server with uvicorn.

Usage:
    python scripts/run_api.py
    python scripts/run_api.py --port 8080
    python scripts/run_api.py --reload  # Development mode
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

import uvicorn


def main():
    """Main function to start the API server."""
    parser = argparse.ArgumentParser(description="Start Medical Telegram Warehouse API")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--workers", type=int, default=1, help="Number of worker processes (default: 1)"
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["critical", "error", "warning", "info", "debug"],
        help="Logging level (default: info)",
    )

    args = parser.parse_args()

    print(f"🚀 Starting Medical Telegram Warehouse API")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Docs: http://{args.host}:{args.port}/docs")
    print(f"   ReDoc: http://{args.host}:{args.port}/redoc")
    print()

    uvicorn.run(
        "api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
        log_level=args.log_level,
        access_log=True,
    )


if __name__ == "__main__":
    main()
