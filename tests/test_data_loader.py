"""
Unit tests for DataLoader class.

Tests data loading, validation, and duplicate checking.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime
from pathlib import Path
from src.database.data_loader import DataLoader
from src.database.db_connector import DatabaseConnector


class TestDataLoader:
    """Test suite for DataLoader class."""

    @pytest.fixture
    def mock_db_connector(self):
        """Fixture for mocked DatabaseConnector."""
        mock_db = Mock(spec=DatabaseConnector)
        mock_db.connection_pool = True  # Simulate connected state
        return mock_db

    @pytest.fixture
    def data_loader(self, mock_db_connector):
        """Fixture for DataLoader instance with mocked DB."""
        return DataLoader(db_connector=mock_db_connector)

    def test_init_with_connector(self, mock_db_connector):
        """Test DataLoader initialization with provided connector."""
        # Act
        loader = DataLoader(db_connector=mock_db_connector)

        # Assert
        assert loader.db_connector == mock_db_connector

    @patch("src.database.data_loader.DatabaseConnector")
    def test_init_without_connector(self, mock_db_class):
        """Test DataLoader initialization creates new connector if not provided."""
        # Arrange
        mock_instance = Mock()
        mock_instance.connection_pool = None
        mock_db_class.return_value = mock_instance

        # Act
        loader = DataLoader()

        # Assert
        mock_db_class.assert_called_once()
        mock_instance.connect.assert_called_once()

    def test_create_raw_table(self, data_loader, mock_db_connector):
        """Test create_raw_table executes correct SQL."""
        # Act
        data_loader.create_raw_table()

        # Assert
        mock_db_connector.execute_query.assert_called_once()
        call_args = mock_db_connector.execute_query.call_args
        assert "CREATE TABLE IF NOT EXISTS raw.telegram_messages" in call_args[0][0]

    def test_check_duplicates_empty_list(self, data_loader):
        """Test check_duplicates with empty list returns empty."""
        # Act
        result = data_loader.check_duplicates([])

        # Assert
        assert result == []

    def test_check_duplicates_with_existing(self, data_loader, mock_db_connector):
        """Test check_duplicates returns existing IDs."""
        # Arrange
        mock_db_connector.execute_query.return_value = [
            {"message_id": 1},
            {"message_id": 2},
        ]

        # Act
        result = data_loader.check_duplicates([1, 2, 3])

        # Assert
        assert result == [1, 2]

    def test_validate_message_data_valid(self, data_loader):
        """Test _validate_message_data with valid message."""
        # Arrange
        message = {
            "message_id": 123,
            "channel_name": "test_channel",
            "message_date": "2026-01-18T10:00:00",
        }

        # Act
        result = data_loader._validate_message_data(message)

        # Assert
        assert result is True

    def test_validate_message_data_missing_field(self, data_loader):
        """Test _validate_message_data with missing required field."""
        # Arrange
        message = {
            "message_id": 123,
            "channel_name": "test_channel",
            # missing message_date
        }

        # Act
        result = data_loader._validate_message_data(message)

        # Assert
        assert result is False

    def test_validate_message_data_invalid_id(self, data_loader):
        """Test _validate_message_data with invalid message_id."""
        # Arrange
        message = {
            "message_id": "not_a_number",
            "channel_name": "test_channel",
            "message_date": "2026-01-18T10:00:00",
        }

        # Act
        result = data_loader._validate_message_data(message)

        # Assert
        assert result is False

    def test_bulk_insert_empty_list(self, data_loader):
        """Test bulk_insert with empty list returns 0."""
        # Act
        result = data_loader.bulk_insert([])

        # Assert
        assert result == 0

    def test_bulk_insert_all_duplicates(self, data_loader, mock_db_connector):
        """Test bulk_insert skips all duplicate messages."""
        # Arrange
        messages = [
            {
                "message_id": 1,
                "channel_name": "test",
                "message_date": "2026-01-18T10:00:00",
            },
            {
                "message_id": 2,
                "channel_name": "test",
                "message_date": "2026-01-18T10:00:00",
            },
        ]
        mock_db_connector.execute_query.return_value = [
            {"message_id": 1},
            {"message_id": 2},
        ]

        # Act
        result = data_loader.bulk_insert(messages)

        # Assert
        assert result == 0

    def test_bulk_insert_new_messages(self, data_loader, mock_db_connector):
        """Test bulk_insert inserts new messages."""
        # Arrange
        messages = [
            {
                "message_id": 1,
                "channel_name": "test",
                "message_date": "2026-01-18T10:00:00",
            },
            {
                "message_id": 2,
                "channel_name": "test",
                "message_date": "2026-01-18T10:00:00",
            },
        ]
        mock_db_connector.execute_query.return_value = []  # No duplicates

        # Act
        result = data_loader.bulk_insert(messages)

        # Assert
        assert result == 2
        mock_db_connector.execute_many.assert_called_once()

    def test_bulk_insert_filters_invalid(self, data_loader, mock_db_connector):
        """Test bulk_insert filters out invalid messages."""
        # Arrange
        messages = [
            {
                "message_id": 1,
                "channel_name": "test",
                "message_date": "2026-01-18T10:00:00",
            },
            {
                "message_id": "invalid",
                "channel_name": "test",
                "message_date": "2026-01-18T10:00:00",
            },
            {"channel_name": "test"},  # missing message_id
        ]
        mock_db_connector.execute_query.return_value = []

        # Act
        result = data_loader.bulk_insert(messages)

        # Assert
        assert result == 1  # Only 1 valid message

    @patch("pathlib.Path.rglob")
    @patch("pathlib.Path.is_dir")
    @patch("pathlib.Path.is_file")
    @patch("pathlib.Path.exists")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"message_id": 1, "channel_name": "test", "message_date": "2026-01-18"}',
    )
    def test_load_json_to_postgres_single_file(
        self,
        mock_file,
        mock_exists,
        mock_is_file,
        mock_is_dir,
        mock_rglob,
        data_loader,
        mock_db_connector,
    ):
        """Test load_json_to_postgres with single JSON file."""
        # Arrange
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_is_dir.return_value = False
        mock_db_connector.execute_query.return_value = []

        # Act
        with patch.object(
            Path, "suffix", new_callable=lambda: property(lambda self: ".json")
        ):
            result = data_loader.load_json_to_postgres("test.json")

        # Assert
        assert result == 1

    @patch("pathlib.Path.exists")
    def test_load_json_to_postgres_path_not_found(self, mock_exists, data_loader):
        """Test load_json_to_postgres raises error for non-existent path."""
        # Arrange
        mock_exists.return_value = False

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            data_loader.load_json_to_postgres("nonexistent/path")

    def test_get_table_stats(self, data_loader, mock_db_connector):
        """Test get_table_stats returns statistics."""
        # Arrange
        mock_db_connector.execute_query.return_value = [
            {
                "total_messages": 100,
                "unique_channels": 5,
                "earliest_message": "2026-01-01",
                "latest_message": "2026-01-18",
                "messages_with_media": 50,
            }
        ]

        # Act
        result = data_loader.get_table_stats()

        # Assert
        assert result["total_messages"] == 100
        assert result["unique_channels"] == 5
        assert result["messages_with_media"] == 50

    def test_get_table_stats_error(self, data_loader, mock_db_connector):
        """Test get_table_stats returns empty dict on error."""
        # Arrange
        from psycopg2 import Error

        mock_db_connector.execute_query.side_effect = Error("Database error")

        # Act
        result = data_loader.get_table_stats()

        # Assert
        assert result == {}
