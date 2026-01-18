"""Tests for DataLakeManager class."""

import json
import pytest
from pathlib import Path
from src.scraper.data_lake_manager import DataLakeManager


class TestDataLakeManager:
    """Test suite for DataLakeManager."""

    @pytest.fixture
    def temp_data_lake(self, tmp_path):
        """Create temporary data lake for testing."""
        return DataLakeManager(base_path=str(tmp_path))

    def test_init_creates_structure(self, temp_data_lake, tmp_path):
        """Test __init__ creates necessary directories."""
        assert (tmp_path / "raw" / "telegram_messages").exists()
        assert (tmp_path / "raw" / "images").exists()
        assert (tmp_path / "processed").exists()

    def test_get_messages_partition_dir(self, temp_data_lake):
        """Test partition directory creation."""
        partition_dir = temp_data_lake.get_messages_partition_dir("2026-01-18")
        assert partition_dir.exists()
        assert partition_dir.name == "2026-01-18"

    def test_get_images_dir(self, temp_data_lake):
        """Test images directory creation."""
        images_dir = temp_data_lake.get_images_dir("test_channel")
        assert images_dir.exists()
        assert images_dir.name == "test_channel"

    def test_save_message_json_success(self, temp_data_lake):
        """Test saving messages to JSON file."""
        messages = [
            {"id": 1, "text": "Hello", "date": "2026-01-18"},
            {"id": 2, "text": "World", "date": "2026-01-18"},
        ]

        file_path = temp_data_lake.save_message_json(
            messages, "test_channel", "2026-01-18"
        )

        assert file_path.exists()
        assert file_path.name == "test_channel.json"

        # Verify content
        with open(file_path, "r") as f:
            saved_data = json.load(f)
        assert len(saved_data) == 2
        assert saved_data[0]["id"] == 1

    def test_save_message_json_empty_raises_error(self, temp_data_lake):
        """Test saving empty messages list raises ValueError."""
        with pytest.raises(ValueError, match="Messages list cannot be empty"):
            temp_data_lake.save_message_json([], "test_channel")

    def test_save_image_success(self, temp_data_lake):
        """Test saving image file."""
        image_data = b"fake_image_data"

        file_path = temp_data_lake.save_image(image_data, "test_channel", 12345)

        assert file_path.exists()
        assert file_path.name == "12345.jpg"

        # Verify content
        with open(file_path, "rb") as f:
            saved_data = f.read()
        assert saved_data == image_data

    def test_write_manifest(self, temp_data_lake):
        """Test writing manifest file."""
        stats = {"channel1": 100, "channel2": 50}

        manifest_path = temp_data_lake.write_manifest("2026-01-18", stats)

        assert manifest_path.exists()
        assert manifest_path.name == "_manifest.json"

        # Verify content
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        assert manifest["date"] == "2026-01-18"
        assert manifest["total_messages"] == 150
        assert manifest["channels"] == stats

    def test_get_scraped_dates(self, temp_data_lake):
        """Test getting list of scraped dates."""
        # Create some date directories
        temp_data_lake.get_messages_partition_dir("2026-01-15")
        temp_data_lake.get_messages_partition_dir("2026-01-16")
        temp_data_lake.get_messages_partition_dir("2026-01-17")

        dates = temp_data_lake.get_scraped_dates()

        assert len(dates) == 3
        assert "2026-01-15" in dates
        assert "2026-01-16" in dates
        assert "2026-01-17" in dates

    def test_validate_structure_success(self, temp_data_lake):
        """Test structure validation succeeds for valid structure."""
        assert temp_data_lake.validate_structure() is True

    def test_validate_structure_fails_on_missing_dir(self, tmp_path):
        """Test structure validation fails if directory missing."""
        dlm = DataLakeManager(base_path=str(tmp_path / "nonexistent"))

        # Remove a required directory
        import shutil

        shutil.rmtree(tmp_path / "nonexistent" / "raw" / "images")

        with pytest.raises(FileNotFoundError, match="Required directory missing"):
            dlm.validate_structure()
