"""Tests for YOLO modules (simplified)."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.yolo.yolo_detector import YOLODetector
from src.yolo.image_classifier import ImageClassifier


class TestYOLODetector:
    """Test suite for YOLODetector class."""

    @patch("src.yolo.yolo_detector.YOLO")
    def test_init_default_model(self, mock_yolo_class):
        """Test initialization with default model."""
        mock_model = Mock()
        mock_yolo_class.return_value = mock_model

        detector = YOLODetector()

        mock_yolo_class.assert_called_once_with("yolov8n.pt")
        assert detector.model == mock_model
        assert detector.confidence_threshold == 0.25

    @patch("src.yolo.yolo_detector.YOLO")
    def test_init_custom_parameters(self, mock_yolo_class):
        """Test initialization with custom parameters."""
        mock_model = Mock()
        mock_yolo_class.return_value = mock_model

        detector = YOLODetector(model_name="yolov8s.pt", confidence_threshold=0.5)

        mock_yolo_class.assert_called_once_with("yolov8s.pt")
        assert detector.confidence_threshold == 0.5

    @patch("src.yolo.yolo_detector.YOLO")
    def test_get_detection_summary(self, mock_yolo_class):
        """Test getting detection summary statistics."""
        mock_model = Mock()
        mock_yolo_class.return_value = mock_model
        detector = YOLODetector()

        detections = [
            {"class": "person", "confidence": 0.9},
            {"class": "bottle", "confidence": 0.8},
            {"class": "person", "confidence": 0.7},
        ]

        summary = detector.get_detection_summary(detections)

        assert summary["total_objects"] == 3
        assert len(summary["unique_classes"]) == 2
        assert "person" in summary["unique_classes"]
        assert "bottle" in summary["unique_classes"]
        assert summary["class_counts"] == {"person": 2, "bottle": 1}
        assert summary["avg_confidence"] == pytest.approx(0.8)

    @patch("src.yolo.yolo_detector.YOLO")
    def test_get_detection_summary_empty(self, mock_yolo_class):
        """Test getting summary with no detections."""
        mock_model = Mock()
        mock_yolo_class.return_value = mock_model
        detector = YOLODetector()

        summary = detector.get_detection_summary([])

        assert summary["total_objects"] == 0
        assert len(summary["unique_classes"]) == 0
        assert summary["class_counts"] == {}
        assert summary["avg_confidence"] == 0.0


class TestImageClassifier:
    """Test suite for ImageClassifier class."""

    def test_init(self):
        """Test initialization."""
        classifier = ImageClassifier()
        assert classifier is not None

    def test_classify_promotional(self):
        """Test classification of promotional content (person + product)."""
        classifier = ImageClassifier()
        detections = [
            {"class": "person", "confidence": 0.9},
            {"class": "bottle", "confidence": 0.8},
        ]

        category = classifier.classify_image(detections)

        assert category == "promotional"

    def test_classify_product_display(self):
        """Test classification of product display (product only)."""
        classifier = ImageClassifier()
        detections = [
            {"class": "bottle", "confidence": 0.9},
            {"class": "cup", "confidence": 0.8},
        ]

        category = classifier.classify_image(detections)

        assert category == "product_display"

    def test_classify_lifestyle(self):
        """Test classification of lifestyle content (person only)."""
        classifier = ImageClassifier()
        detections = [{"class": "person", "confidence": 0.9}]

        category = classifier.classify_image(detections)

        assert category == "lifestyle"

    def test_classify_other(self):
        """Test classification of other content."""
        classifier = ImageClassifier()
        detections = [{"class": "car", "confidence": 0.9}]

        category = classifier.classify_image(detections)

        assert category == "other"

    def test_classify_empty_detections(self):
        """Test classification with no detections."""
        classifier = ImageClassifier()

        category = classifier.classify_image([])

        assert category == "other"

    def test_get_dominant_objects(self):
        """Test getting dominant objects sorted by confidence."""
        classifier = ImageClassifier()
        detections = [
            {"class": "person", "confidence": 0.9},
            {"class": "bottle", "confidence": 0.8},
            {"class": "cup", "confidence": 0.7},
        ]

        top_objects = classifier.get_dominant_objects(detections, top_n=2)

        assert len(top_objects) == 2
        assert top_objects[0]["class"] == "person"
        assert top_objects[1]["class"] == "bottle"

    def test_get_classification_confidence(self):
        """Test getting classification confidence score."""
        classifier = ImageClassifier()
        detections = [
            {"class": "person", "confidence": 0.9},
            {"class": "bottle", "confidence": 0.7},
        ]

        confidence = classifier.get_classification_confidence(detections)

        assert confidence == pytest.approx(0.8)

    def test_classify_batch(self):
        """Test batch classification."""
        classifier = ImageClassifier()
        batch_results = {
            "img1.jpg": [
                {"class": "person", "confidence": 0.9},
                {"class": "bottle", "confidence": 0.8},
            ],
            "img2.jpg": [{"class": "bottle", "confidence": 0.9}],
        }

        categories = classifier.classify_batch(batch_results)

        assert categories["img1.jpg"] == "promotional"
        assert categories["img2.jpg"] == "product_display"

    def test_get_category_statistics(self):
        """Test getting category distribution statistics."""
        classifier = ImageClassifier()
        batch_results = {
            "img1.jpg": [
                {"class": "person", "confidence": 0.9},
                {"class": "bottle", "confidence": 0.8},
            ],
            "img2.jpg": [{"class": "bottle", "confidence": 0.9}],
            "img3.jpg": [{"class": "person", "confidence": 0.9}],
            "img4.jpg": [],
        }

        stats = classifier.get_category_statistics(batch_results)

        assert "promotional" in stats
        assert "product_display" in stats
        assert "lifestyle" in stats
        assert "other" in stats
        assert stats["promotional"]["count"] == 1
        assert stats["product_display"]["count"] == 1
        assert stats["lifestyle"]["count"] == 1
        assert stats["other"]["count"] == 1
