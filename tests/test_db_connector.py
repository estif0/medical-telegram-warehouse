"""
Unit tests for DatabaseConnector class.

Tests database connection, schema creation, and query execution.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from psycopg2 import pool, Error
from src.database.db_connector import DatabaseConnector


class TestDatabaseConnector:
    """Test suite for DatabaseConnector class."""

    @pytest.fixture
    def db_connector(self):
        """Fixture for DatabaseConnector instance."""
        return DatabaseConnector(
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="test_password",
        )

    def test_init(self, db_connector):
        """Test DatabaseConnector initialization."""
        assert db_connector.host == "localhost"
        assert db_connector.port == 5432
        assert db_connector.database == "test_db"
        assert db_connector.user == "test_user"
        assert db_connector.password == "test_password"
        assert db_connector.connection_pool is None

    @patch("src.database.db_connector.pool.SimpleConnectionPool")
    def test_connect_success(self, mock_pool, db_connector):
        """Test successful database connection."""
        # Arrange
        mock_conn = Mock()
        mock_pool.return_value.getconn.return_value = mock_conn

        # Act
        db_connector.connect()

        # Assert
        mock_pool.assert_called_once()
        assert db_connector.connection_pool is not None

    @patch("src.database.db_connector.pool.SimpleConnectionPool")
    def test_connect_failure(self, mock_pool, db_connector):
        """Test database connection failure."""
        # Arrange
        mock_pool.side_effect = Error("Connection failed")

        # Act & Assert
        with pytest.raises(Error):
            db_connector.connect()

    @patch("src.database.db_connector.pool.SimpleConnectionPool")
    def test_get_connection(self, mock_pool, db_connector):
        """Test get_connection context manager."""
        # Arrange
        mock_conn = Mock()
        mock_pool_instance = Mock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance
        db_connector.connect()

        # Reset putconn call count from connect test connection
        mock_pool_instance.putconn.reset_mock()

        # Act
        with db_connector.get_connection() as conn:
            assert conn == mock_conn

        # Assert
        mock_pool_instance.putconn.assert_called_once_with(mock_conn)

    @patch("src.database.db_connector.pool.SimpleConnectionPool")
    def test_create_schemas(self, mock_pool, db_connector):
        """Test create_schemas creates default schemas."""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_pool_instance = Mock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance
        db_connector.connect()

        # Act
        db_connector.create_schemas()

        # Assert
        assert mock_cursor.execute.call_count == 3  # raw, staging, marts

    @patch("src.database.db_connector.pool.SimpleConnectionPool")
    def test_execute_query_with_fetch(self, mock_pool, db_connector):
        """Test execute_query returns results when fetch=True."""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{"id": 1}, {"id": 2}]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_pool_instance = Mock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance
        db_connector.connect()

        # Act
        results = db_connector.execute_query("SELECT * FROM test", fetch=True)

        # Assert
        assert len(results) == 2
        mock_cursor.execute.assert_called_once()

    @patch("src.database.db_connector.pool.SimpleConnectionPool")
    def test_execute_query_without_fetch(self, mock_pool, db_connector):
        """Test execute_query commits when fetch=False."""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_pool_instance = Mock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance
        db_connector.connect()

        # Act
        result = db_connector.execute_query("INSERT INTO test VALUES (1)", fetch=False)

        # Assert
        assert result is None
        mock_conn.commit.assert_called_once()

    @patch("src.database.db_connector.pool.SimpleConnectionPool")
    def test_execute_many(self, mock_pool, db_connector):
        """Test execute_many for bulk operations."""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_pool_instance = Mock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance
        db_connector.connect()
        data = [(1, "a"), (2, "b")]

        # Act
        db_connector.execute_many("INSERT INTO test VALUES (%s, %s)", data)

        # Assert
        mock_cursor.executemany.assert_called_once()
        mock_conn.commit.assert_called_once()

    @patch("src.database.db_connector.pool.SimpleConnectionPool")
    def test_table_exists_true(self, mock_pool, db_connector):
        """Test table_exists returns True for existing table."""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{"exists": True}]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_pool_instance = Mock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance
        db_connector.connect()

        # Act
        result = db_connector.table_exists("test_table", "public")

        # Assert
        assert result is True

    @patch("src.database.db_connector.pool.SimpleConnectionPool")
    def test_table_exists_false(self, mock_pool, db_connector):
        """Test table_exists returns False for non-existing table."""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{"exists": False}]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_pool_instance = Mock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance
        db_connector.connect()

        # Act
        result = db_connector.table_exists("nonexistent", "public")

        # Assert
        assert result is False

    @patch("src.database.db_connector.pool.SimpleConnectionPool")
    def test_close(self, mock_pool, db_connector):
        """Test close closes connection pool."""
        # Arrange
        mock_pool_instance = Mock()
        mock_pool.return_value = mock_pool_instance
        db_connector.connect()

        # Act
        db_connector.close()

        # Assert
        mock_pool_instance.closeall.assert_called_once()
