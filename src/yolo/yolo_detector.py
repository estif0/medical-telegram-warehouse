"""
YOLOv8 Object Detector for medical product images.

This module provides object detection capabilities using YOLOv8
to identify objects in scraped Telegram images.

Example:
    >>> from src.yolo.yolo_detector import YOLODetector
    >>> detector = YOLODetector(model_name="yolov8n.pt")
    >>> results = detector.detect_objects("image.jpg")
    >>> print(results)
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Any
import logging

try:
    from ultralytics import YOLO
    import cv2
    from PIL import Image
except ImportError as e:
    raise ImportError(
        f"Required package not installed: {e}. "
        "Install with: pip install ultralytics opencv-python pillow"
    )

from src.utils.logger import get_logger


class YOLODetector:
    """
    Object detector using YOLOv8 for medical product images.

    Attributes:
        model_name (str): Name of the YOLO model to use
        confidence_threshold (float): Minimum confidence for detections
        model (YOLO): Loaded YOLO model
        logger (Logger): Logger instance

    Example:
        >>> detector = YOLODetector(model_name="yolov8n.pt")
        >>> results = detector.detect_objects("path/to/image.jpg")
        >>> for detection in results:
        ...     print(f"{detection['class']}: {detection['confidence']:.2f}")
    """

    def __init__(
        self, model_name: str = "yolov8n.pt", confidence_threshold: float = 0.25
    ):
        """
        Initialize the YOLO detector.

        Args:
            model_name: YOLO model to use (yolov8n, yolov8s, yolov8m, yolov8l, yolov8x)
            confidence_threshold: Minimum confidence score (0.0-1.0)
        """
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.logger = get_logger(__name__)

        # Load YOLO model
        try:
            self.logger.info(f"Loading YOLO model: {model_name}")
            self.model = YOLO(model_name)
            self.logger.info("YOLO model loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load YOLO model: {e}")
            raise

    def detect_objects(
        self, image_path: str, confidence_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect objects in a single image.

        Args:
            image_path: Path to the image file
            confidence_threshold: Override default confidence threshold

        Returns:
            List of detections, each containing:
                - class: Object class name
                - confidence: Confidence score (0-1)
                - bbox: Bounding box [x1, y1, x2, y2]
                - class_id: Numeric class ID

        Raises:
            FileNotFoundError: If image file doesn't exist
            Exception: If detection fails

        Example:
            >>> detector = YOLODetector()
            >>> results = detector.detect_objects("image.jpg", confidence_threshold=0.5)
            >>> print(f"Found {len(results)} objects")
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        conf_threshold = confidence_threshold or self.confidence_threshold

        try:
            # Run detection
            results = self.model(image_path, conf=conf_threshold, verbose=False)

            # Parse results
            detections = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    detection = {
                        "class": result.names[int(box.cls)],
                        "confidence": float(box.conf),
                        "bbox": box.xyxy[0].tolist(),
                        "class_id": int(box.cls),
                    }
                    detections.append(detection)

            self.logger.debug(f"Detected {len(detections)} objects in {image_path}")
            return detections

        except Exception as e:
            self.logger.error(f"Detection failed for {image_path}: {e}")
            raise

    def batch_detect(
        self, image_paths: List[str], confidence_threshold: Optional[float] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect objects in multiple images.

        Args:
            image_paths: List of image file paths
            confidence_threshold: Override default confidence threshold

        Returns:
            Dictionary mapping image paths to their detection results

        Example:
            >>> detector = YOLODetector()
            >>> images = ["img1.jpg", "img2.jpg"]
            >>> results = detector.batch_detect(images)
            >>> for img, detections in results.items():
            ...     print(f"{img}: {len(detections)} objects")
        """
        results = {}
        total = len(image_paths)

        self.logger.info(f"Processing batch of {total} images")

        for idx, image_path in enumerate(image_paths, 1):
            try:
                detections = self.detect_objects(image_path, confidence_threshold)
                results[image_path] = detections

                if idx % 10 == 0:
                    self.logger.info(f"Processed {idx}/{total} images")

            except Exception as e:
                self.logger.warning(f"Skipping {image_path}: {e}")
                results[image_path] = []

        self.logger.info(f"Batch processing complete: {len(results)} images")
        return results

    def get_detection_summary(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get summary statistics for detection results.

        Args:
            detections: List of detection dictionaries

        Returns:
            Dictionary containing:
                - total_objects: Total number of detected objects
                - unique_classes: List of unique class names
                - class_counts: Count of each class
                - avg_confidence: Average confidence score
                - high_confidence: Count of high confidence (>0.7) detections

        Example:
            >>> detector = YOLODetector()
            >>> detections = detector.detect_objects("image.jpg")
            >>> summary = detector.get_detection_summary(detections)
            >>> print(summary['unique_classes'])
        """
        if not detections:
            return {
                "total_objects": 0,
                "unique_classes": [],
                "class_counts": {},
                "avg_confidence": 0.0,
                "high_confidence": 0,
            }

        # Count classes
        class_counts = {}
        confidences = []

        for det in detections:
            class_name = det["class"]
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
            confidences.append(det["confidence"])

        return {
            "total_objects": len(detections),
            "unique_classes": list(class_counts.keys()),
            "class_counts": class_counts,
            "avg_confidence": sum(confidences) / len(confidences),
            "high_confidence": sum(1 for c in confidences if c > 0.7),
        }

    def detect_and_save(
        self,
        image_path: str,
        output_path: str,
        confidence_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Detect objects and save annotated image.

        Args:
            image_path: Path to input image
            output_path: Path to save annotated image
            confidence_threshold: Override default confidence threshold

        Returns:
            List of detections

        Example:
            >>> detector = YOLODetector()
            >>> results = detector.detect_and_save("input.jpg", "output.jpg")
        """
        conf_threshold = confidence_threshold or self.confidence_threshold

        try:
            # Run detection with save
            results = self.model(image_path, conf=conf_threshold, verbose=False)

            # Save annotated image
            annotated = results[0].plot()
            cv2.imwrite(output_path, annotated)

            # Parse detections
            detections = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    detection = {
                        "class": result.names[int(box.cls)],
                        "confidence": float(box.conf),
                        "bbox": box.xyxy[0].tolist(),
                        "class_id": int(box.cls),
                    }
                    detections.append(detection)

            self.logger.info(f"Saved annotated image to {output_path}")
            return detections

        except Exception as e:
            self.logger.error(f"Failed to detect and save: {e}")
            raise
