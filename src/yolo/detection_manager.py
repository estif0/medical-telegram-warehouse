"""
Detection Results Manager for YOLO detections.

This module handles saving, loading, and database integration of
object detection results.

Example:
    >>> from src.yolo.detection_manager import DetectionManager
    >>> manager = DetectionManager()
    >>> manager.save_results_to_csv(results, "detections.csv")
"""

import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from src.utils.logger import get_logger


class DetectionManager:
    """
    Manage detection results storage and database integration.

    Attributes:
        logger (Logger): Logger instance

    Example:
        >>> manager = DetectionManager()
        >>> results = {
        ...     'img1.jpg': [{'class': 'person', 'confidence': 0.9}]
        ... }
        >>> manager.save_results_to_csv(results, "output.csv")
    """

    def __init__(self):
        """Initialize the detection manager."""
        self.logger = get_logger(__name__)

    def save_results_to_csv(
        self,
        batch_results: Dict[str, List[Dict[str, Any]]],
        output_path: str,
        include_categories: bool = True,
    ) -> None:
        """
        Save detection results to CSV file.

        Args:
            batch_results: Dictionary mapping image paths to detections
            output_path: Path to output CSV file
            include_categories: Whether to include image categories

        Example:
            >>> manager = DetectionManager()
            >>> manager.save_results_to_csv(results, "detections.csv")
        """
        try:
            # Prepare CSV data
            csv_data = []

            for image_path, detections in batch_results.items():
                # Extract message_id from image path
                # Format: data/raw/images/channel_name/message_id.jpg
                image_name = Path(image_path).stem  # Gets message_id
                channel_name = Path(image_path).parent.name

                if not detections:
                    # No detections
                    csv_data.append(
                        {
                            "image_path": image_path,
                            "channel_name": channel_name,
                            "message_id": image_name,
                            "detected_class": None,
                            "confidence": None,
                            "total_objects": 0,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                else:
                    # Add row for each detection
                    for detection in detections:
                        csv_data.append(
                            {
                                "image_path": image_path,
                                "channel_name": channel_name,
                                "message_id": image_name,
                                "detected_class": detection["class"],
                                "confidence": detection["confidence"],
                                "bbox_x1": detection["bbox"][0],
                                "bbox_y1": detection["bbox"][1],
                                "bbox_x2": detection["bbox"][2],
                                "bbox_y2": detection["bbox"][3],
                                "total_objects": len(detections),
                                "timestamp": datetime.now().isoformat(),
                            }
                        )

            # Write to CSV
            if csv_data:
                fieldnames = list(csv_data[0].keys())

                with open(output_path, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(csv_data)

                self.logger.info(
                    f"Saved {len(csv_data)} detection records to {output_path}"
                )
            else:
                self.logger.warning("No detection data to save")

        except Exception as e:
            self.logger.error(f"Failed to save CSV: {e}")
            raise

    def save_results_to_json(
        self, batch_results: Dict[str, List[Dict[str, Any]]], output_path: str
    ) -> None:
        """
        Save detection results to JSON file.

        Args:
            batch_results: Dictionary mapping image paths to detections
            output_path: Path to output JSON file

        Example:
            >>> manager = DetectionManager()
            >>> manager.save_results_to_json(results, "detections.json")
        """
        try:
            output_data = {
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "total_images": len(batch_results),
                    "total_detections": sum(
                        len(dets) for dets in batch_results.values()
                    ),
                },
                "results": batch_results,
            }

            with open(output_path, "w") as f:
                json.dump(output_data, f, indent=2)

            self.logger.info(f"Saved detection results to {output_path}")

        except Exception as e:
            self.logger.error(f"Failed to save JSON: {e}")
            raise

    def load_results_from_json(
        self, input_path: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Load detection results from JSON file.

        Args:
            input_path: Path to input JSON file

        Returns:
            Dictionary mapping image paths to detections

        Example:
            >>> manager = DetectionManager()
            >>> results = manager.load_results_from_json("detections.json")
        """
        try:
            with open(input_path, "r") as f:
                data = json.load(f)

            self.logger.info(f"Loaded detection results from {input_path}")
            return data.get("results", {})

        except Exception as e:
            self.logger.error(f"Failed to load JSON: {e}")
            raise

    def prepare_for_database(
        self, batch_results: Dict[str, List[Dict[str, Any]]], categories: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Prepare detection results for database insertion.

        Args:
            batch_results: Dictionary mapping image paths to detections
            categories: Dictionary mapping image paths to categories

        Returns:
            List of dictionaries ready for database insertion

        Example:
            >>> manager = DetectionManager()
            >>> db_records = manager.prepare_for_database(results, categories)
        """
        db_records = []

        for image_path, detections in batch_results.items():
            # Extract identifiers
            image_name = Path(image_path).stem  # message_id
            channel_name = Path(image_path).parent.name
            category = categories.get(image_path, "other")

            # Create record for each detection
            for detection in detections:
                record = {
                    "message_id": image_name,
                    "channel_name": channel_name,
                    "image_path": image_path,
                    "detected_class": detection["class"],
                    "confidence": detection["confidence"],
                    "image_category": category,
                    "bbox": json.dumps(detection["bbox"]),
                    "processed_at": datetime.now(),
                }
                db_records.append(record)

        self.logger.info(f"Prepared {len(db_records)} records for database")
        return db_records

    def merge_with_messages(self, detections_csv: str, output_csv: str) -> None:
        """
        Merge detection results with message data.

        Args:
            detections_csv: Path to detections CSV
            output_csv: Path to output merged CSV

        Example:
            >>> manager = DetectionManager()
            >>> manager.merge_with_messages("detections.csv", "merged.csv")
        """
        try:
            # This would typically query the database
            # For now, we'll just copy the detections CSV
            import shutil

            shutil.copy(detections_csv, output_csv)

            self.logger.info(f"Merged results saved to {output_csv}")

        except Exception as e:
            self.logger.error(f"Failed to merge: {e}")
            raise

    def get_statistics(
        self, batch_results: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Get statistics about detection results.

        Args:
            batch_results: Dictionary mapping image paths to detections

        Returns:
            Dictionary with statistics

        Example:
            >>> manager = DetectionManager()
            >>> stats = manager.get_statistics(results)
            >>> print(f"Total images: {stats['total_images']}")
        """
        total_images = len(batch_results)
        images_with_detections = sum(1 for dets in batch_results.values() if dets)
        total_detections = sum(len(dets) for dets in batch_results.values())

        # Class counts
        class_counts = {}
        for detections in batch_results.values():
            for det in detections:
                cls = det["class"]
                class_counts[cls] = class_counts.get(cls, 0) + 1

        # Average confidence
        all_confidences = [
            det["confidence"]
            for detections in batch_results.values()
            for det in detections
        ]
        avg_confidence = (
            sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
        )

        return {
            "total_images": total_images,
            "images_with_detections": images_with_detections,
            "images_without_detections": total_images - images_with_detections,
            "total_detections": total_detections,
            "avg_detections_per_image": (
                total_detections / total_images if total_images > 0 else 0
            ),
            "unique_classes": len(class_counts),
            "class_counts": class_counts,
            "avg_confidence": avg_confidence,
        }
