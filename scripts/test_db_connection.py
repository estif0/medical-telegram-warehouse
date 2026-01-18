#!/usr/bin/env python3
"""
Test database connection script.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()


def test_database_connection():
    """Test connection to PostgreSQL database."""

    # Get connection details from environment
    db_user = os.getenv("POSTGRES_USER", "warehouse_user")
    db_password = os.getenv("POSTGRES_PASSWORD", "changeme")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "medical_warehouse")

    # Build connection URL
    connection_url = (
        f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )

    print("=" * 60)
    print("🧪 Testing Database Connection")
    print("=" * 60)
    print(f"\n📍 Connection Details:")
    print(f"   Host: {db_host}")
    print(f"   Port: {db_port}")
    print(f"   Database: {db_name}")
    print(f"   User: {db_user}")

    try:
        # Create engine
        engine = create_engine(connection_url)

        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]  # type: ignore

            print(f"\n✅ Connection Successful!")
            print(f"\n📦 PostgreSQL Version:")
            print(f"   {version}")

            # Check schemas
            result = connection.execute(
                text(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'public')"
                )
            )
            schemas = [row[0] for row in result.fetchall()]

            print(f"\n📂 Schemas:")
            if schemas:
                for schema in schemas:
                    print(f"   ✓ {schema}")
            else:
                print(f"   ⚠️  No custom schemas found (will be created on first load)")

            print("\n" + "=" * 60)
            print("✅ Database is ready to use!")
            print("=" * 60)
            return True

    except Exception as e:
        print(f"\n❌ Connection Failed!")
        print(f"\n⚠️  Error: {str(e)}")
        print("\n💡 Troubleshooting:")
        print(f"   1. Ensure PostgreSQL is running on {db_host}:{db_port}")
        print(f"   2. Verify credentials in .env file")
        print(f"   3. If using Docker: docker-compose up -d")
        print("\n" + "=" * 60)
        return False


if __name__ == "__main__":
    success = test_database_connection()
    exit(0 if success else 1)
