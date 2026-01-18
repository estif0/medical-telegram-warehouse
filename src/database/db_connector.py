"""
Database connector module for PostgreSQL operations.

This module provides a database connection manager for the medical warehouse
PostgreSQL database with connection pooling and schema management.

Example:
    >>> from src.database.db_connector import DatabaseConnector
    >>> db = DatabaseConnector()
    >>> db.connect()
    >>> db.create_schemas()
    >>> db.close()
"""

import os
import logging
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import psycopg2
from psycopg2 import pool, sql, Error
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DatabaseConnector:
    """
    PostgreSQL database connection manager with connection pooling.

    This class manages database connections, schema creation, and query execution
    for the medical warehouse PostgreSQL database.

    Attributes:
        host (str): Database host
        port (int): Database port
        database (str): Database name
        user (str): Database user
        password (str): Database password
        connection_pool: psycopg2 connection pool
        logger: Logger instance

    Example:
        >>> db = DatabaseConnector()
        >>> db.connect()
        >>> result = db.execute_query("SELECT * FROM raw.telegram_messages LIMIT 10")
        >>> db.close()
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize DatabaseConnector with connection parameters.

        Args:
            host: Database host (defaults to POSTGRES_HOST env var)
            port: Database port (defaults to POSTGRES_PORT env var)
            database: Database name (defaults to POSTGRES_DB env var)
            user: Database user (defaults to POSTGRES_USER env var)
            password: Database password (defaults to POSTGRES_PASSWORD env var)
        """
        self.host = host or os.getenv("POSTGRES_HOST", "localhost")
        self.port = int(port or os.getenv("POSTGRES_PORT", 5432))
        self.database = database or os.getenv("POSTGRES_DB", "medical_warehouse")
        self.user = user or os.getenv("POSTGRES_USER", "warehouse_user")
        self.password = password or os.getenv("POSTGRES_PASSWORD", "")

        self.connection_pool: Optional[pool.SimpleConnectionPool] = None
        self.logger = logging.getLogger(__name__)

    def connect(self, min_connections: int = 1, max_connections: int = 10) -> None:
        """
        Establish connection pool to PostgreSQL database.

        Args:
            min_connections: Minimum number of connections in pool
            max_connections: Maximum number of connections in pool

        Raises:
            psycopg2.Error: If connection fails
        """
        try:
            self.logger.info(
                f"Connecting to PostgreSQL database at {self.host}:{self.port}"
            )

            self.connection_pool = pool.SimpleConnectionPool(
                min_connections,
                max_connections,
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
            )

            # Test connection
            conn = self.connection_pool.getconn()
            conn.close()
            self.connection_pool.putconn(conn)

            self.logger.info("Successfully connected to PostgreSQL database")

        except Error as e:
            self.logger.error(f"Failed to connect to database: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.

        Yields:
            psycopg2.connection: Database connection

        Example:
            >>> with db.get_connection() as conn:
            ...     cursor = conn.cursor()
            ...     cursor.execute("SELECT 1")
        """
        if not self.connection_pool:
            raise RuntimeError(
                "Database connection pool not initialized. Call connect() first."
            )

        conn = self.connection_pool.getconn()
        try:
            yield conn
        finally:
            self.connection_pool.putconn(conn)

    def create_schemas(self, schemas: Optional[List[str]] = None) -> None:
        """
        Create database schemas if they don't exist.

        Args:
            schemas: List of schema names to create (defaults to raw, staging, marts)

        Raises:
            psycopg2.Error: If schema creation fails
        """
        if schemas is None:
            schemas = ["raw", "staging", "marts"]

        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    for schema in schemas:
                        cursor.execute(
                            sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                                sql.Identifier(schema)
                            )
                        )
                        self.logger.info(f"Schema '{schema}' created or already exists")
                conn.commit()

        except Error as e:
            self.logger.error(f"Failed to create schemas: {e}")
            raise

    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch: bool = True,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Execute a SQL query and optionally fetch results.

        Args:
            query: SQL query to execute
            params: Query parameters for parameterized queries
            fetch: Whether to fetch and return results

        Returns:
            List of result rows as dictionaries if fetch=True, None otherwise

        Raises:
            psycopg2.Error: If query execution fails

        Example:
            >>> results = db.execute_query(
            ...     "SELECT * FROM raw.telegram_messages WHERE channel_name = %s",
            ...     params=("CheMed123",)
            ... )
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, params)

                    if fetch:
                        results = cursor.fetchall()
                        return [dict(row) for row in results]
                    else:
                        conn.commit()
                        return None

        except Error as e:
            self.logger.error(f"Query execution failed: {e}")
            self.logger.error(f"Query: {query}")
            raise

    def execute_many(self, query: str, data: List[tuple]) -> None:
        """
        Execute a query with multiple parameter sets (bulk insert).

        Args:
            query: SQL query with placeholders
            data: List of parameter tuples

        Raises:
            psycopg2.Error: If execution fails

        Example:
            >>> db.execute_many(
            ...     "INSERT INTO table (col1, col2) VALUES (%s, %s)",
            ...     [("val1", "val2"), ("val3", "val4")]
            ... )
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.executemany(query, data)
                conn.commit()
                self.logger.info(f"Bulk insert completed: {len(data)} rows")

        except Error as e:
            self.logger.error(f"Bulk insert failed: {e}")
            raise

    def table_exists(self, table_name: str, schema: str = "public") -> bool:
        """
        Check if a table exists in the database.

        Args:
            table_name: Name of the table
            schema: Schema name (default: public)

        Returns:
            True if table exists, False otherwise
        """
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = %s 
                AND table_name = %s
            );
        """
        try:
            result = self.execute_query(query, params=(schema, table_name))
            return result[0]["exists"] if result else False
        except Error as e:
            self.logger.error(f"Error checking table existence: {e}")
            return False

    def close(self) -> None:
        """
        Close all connections in the pool.
        """
        if self.connection_pool:
            self.connection_pool.closeall()
            self.logger.info("Database connection pool closed")
