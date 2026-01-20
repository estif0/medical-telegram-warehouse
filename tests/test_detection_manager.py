"""Tests for DetectionManager class."""

import pytest
import csv
import json
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from src.yolo.detection_manager import DetectionManager


class TestDetectionManager:
    """Test suite for DetectionManager class."""

    @pytest.fixture
    def manager(self):
        """Fixture for DetectionManager instance."""
        return DetectionManager()

    @pytest.fixture
    def sample_batch_results(self):
        """Fixture for sample detection results."""
        return {
            "data/raw/images/channel1/123.jpg": [
                {"class": "person", "confidence": 0.9, "bbox": [100, 100, 200, 200]},
                {"class": "bottle", "confidence": 0.8, "bbox": [300, 300, 400, 400]},
            ],
            "data/raw/images/channel2/456.jpg": [
                {"class": "cup", "confidence": 0.7, "bbox": [50, 50, 150, 150]}
            ],
            "data/raw/images/channel1/789.jpg": [],
        }

    def test_init(self, manager):
        """Test initialization."""
        assert manager is not None
        assert manager.logger is not None

    def test_save_results_to_csv(self, manager, sample_batch_results, tmp_path):
        """Test saving detection results to CSV."""
        # Arrange
        output_file = tmp_path / "detections.csv"

        # Act
        manager.save_results_to_csv(sample_batch_results, str(output_file))

        # Assert
        assert output_file.exists()

        with open(output_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should have 3 detections (2 from first image, 1 from second, 1 empty for third)
        assert len(rows) == 4

        # Check first detection
        assert rows[0]["channel_name"] == "channel1"
        assert rows[0]["message_id"] == "123"
        assert rows[0]["detected_class"] == "person"
        assert float(rows[0]["confidence"]) == pytest.approx(0.9)

    def test_save_results_to_csv_empty(self, manager, tmp_path):
        """Test saving empty results to CSV."""
        # Arrange
        output_file = tmp_path / "detections.csv"
        empty_results = {}

        # Act
        manager.save_results_to_csv(empty_results, str(output_file))

        # Assert - file should not be created or be empty
        # Manager logs a warning but doesn't create file

    def test_save_results_to_json(self, manager, sample_batch_results, tmp_path):
        """Test saving detection results to JSON."""
        # Arrange
        output_file = tmp_path / "detections.json"

        # Act
        manager.save_results_to_json(sample_batch_results, str(output_file))

        # Assert
        assert output_file.exists()

        with open(output_file, "r") as f:
            data = json.load(f)

        assert "metadata" in data
        assert "results" in data
        assert data["metadata"]["total_images"] == 3
        assert data["metadata"]["total_detections"] == 3
        assert data["results"] == sample_batch_results

    def test_load_results_from_json(self, manager, sample_batch_results, tmp_path):
        """Test loading detection results from JSON."""
        # Arrange
        input_file = tmp_path / "detections.json"
        test_data = {
            "metadata": {"timestamp": "2025-01-01T00:00:00", "total_images": 3},
            "results": sample_batch_results,
        }

        with open(input_file, "w") as f:
            json.dump(test_data, f)

        # Act
        results = manager.load_results_from_json(str(input_file))

        # Assert
        assert results == sample_batch_results

    def test_load_results_from_json_missing_file(self, manager):
        """Test loading from nonexistent JSON file."""
        # Act & Assert
        with pytest.raises(Exception):
            manager.load_results_from_json("nonexistent.json")

    def test_prepare_for_database(self, manager, sample_batch_results):
        """Test preparing detection results for database insertion."""
        # Arrange
        categories = {
            "data/raw/images/channel1/123.jpg": "promotional",
            "data/raw/images/channel2/456.jpg": "product_display",
            "data/raw/images/channel1/789.jpg": "other",
        }

        # Act
        db_records = manager.prepare_for_database(sample_batch_results, categories)

        # Assert
        # Should have 3 records (one for each detection, empty image excluded)
        assert len(db_records) == 3

        # Check first record
        assert db_records[0]["message_id"] == "123"
        assert db_records[0]["channel_name"] == "channel1"
        assert db_records[0]["detected_class"] == "person"
        assert db_records[0]["confidence"] == 0.9
        assert db_records[0]["image_category"] == "promotional"
        assert "bbox" in db_records[0]
        assert "processed_at" in db_records[0]

    def test_get_statistics(self, manager, sample_batch_results):
        """Test getting statistics about detection results."""
        # Act
        stats = manager.get_statistics(sample_batch_results)

        # Assert
        assert stats["total_images"] == 3
        assert stats["images_with_detections"] == 2
        assert stats["images_without_detections"] == 1
        assert stats["total_detections"] == 3
        assert stats["avg_detections_per_image"] == pytest.approx(1.0)
        assert stats["unique_classes"] == 3
        assert stats["class_counts"] == {"person": 1, "bottle": 1, "cup": 1}
        assert stats["avg_confidence"] == pytest.approx(0.8)

    def test_get_statistics_empty(self, manager):
        """Test getting statistics with no results."""
        # Act
        stats = manager.get_statistics({})

        # Assert
        assert stats["total_images"] == 0
        assert stats["images_with_detections"] == 0
        assert stats["images_without_detections"] == 0
        assert stats["total_detections"] == 0
        assert stats["avg_detections_per_image"] == 0
        assert stats["unique_classes"] == 0
        assert stats["class_counts"] == {}
        assert stats["avg_confidence"] == 0.0

    def test_merge_with_messages(self, manager, tmp_path):
        """Test merging detection results with message data."""
        # Arrange
        input_csv = tmp_path / "detections.csv"
        output_csv = tmp_path / "merged.csv"

        # Create dummy input CSV
        with open(input_csv, "w") as f:
            f.write("message_id,detected_class\n123,person\n")

        # Act
        manager.merge_with_messages(str(input_csv), str(output_csv))

        # Assert
        assert output_csv.exists()

    def test_save_results_csv_extracts_identifiers(self, manager, tmp_path):
        """Test that CSV saving correctly extracts channel and message IDs from paths."""
        # Arrange
        output_file = tmp_path / "detections.csv"
        results = {
            "data/raw/images/my_channel/msg_999.jpg": [
                {"class": "person", "confidence": 0.9, "bbox": [0, 0, 100, 100]}
            ]
        }

        # Act
        manager.save_results_to_csv(results, str(output_file))

        # Assert
        with open(output_file, "r") as f:
            reader = csv.DictReader(f)
            row = next(reader)

        assert row["channel_name"] == "my_channel"
        assert row["message_id"] == "msg_999"

    def test_prepare_for_database_handles_missing_category(self, manager):
        """Test that prepare_for_database handles missing category gracefully."""
        # Arrange
        results = {
            "data/raw/images/channel1/123.jpg": [
                {"class": "person", "confidence": 0.9, "bbox": [0, 0, 100, 100]}
            ]
        }
        categories = {}  # Empty categories

        # Act
        db_records = manager.prepare_for_database(results, categories)

        # Assert
        assert len(db_records) == 1
        assert db_records[0]["image_category"] == "other"  # Default value
