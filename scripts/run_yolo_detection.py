#!/usr/bin/env python3
"""
Run YOLO object detection on downloaded Telegram images.

This script processes all images in the data lake, detects objects,
classifies images, and saves results for database integration.

Usage:
    python scripts/run_yolo_detection.py
    python scripts/run_yolo_detection.py --confidence 0.5
    python scripts/run_yolo_detection.py --output results.csv
"""

import sys
import argparse
from pathlib import Path
from typing import List

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.yolo.yolo_detector import YOLODetector
from src.yolo.image_classifier import ImageClassifier
from src.yolo.detection_manager import DetectionManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


def find_images(base_path: str = "data/raw/images") -> List[str]:
    """
    Find all images in the data lake.

    Args:
        base_path: Base path to images directory

    Returns:
        List of image file paths
    """
    base_dir = Path(base_path)

    if not base_dir.exists():
        logger.error(f"Images directory not found: {base_path}")
        return []

    # Find all jpg/jpeg/png files
    image_extensions = ["*.jpg", "*.jpeg", "*.png"]
    image_files = []

    for ext in image_extensions:
        image_files.extend(base_dir.rglob(ext))

    return [str(img) for img in image_files]


def main():
    """Main function to run YOLO detection pipeline."""
    parser = argparse.ArgumentParser(
        description="Run YOLO object detection on Telegram images"
    )
    parser.add_argument(
        "--input",
        default="data/raw/images",
        help="Input directory containing images (default: data/raw/images)",
    )
    parser.add_argument(
        "--output",
        default="data/processed/detections.csv",
        help="Output CSV file for results (default: data/processed/detections.csv)",
    )
    parser.add_argument(
        "--model",
        default="yolov8n.pt",
        choices=["yolov8n.pt", "yolov8s.pt", "yolov8m.pt"],
        help="YOLO model to use (default: yolov8n.pt)",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.25,
        help="Confidence threshold (0.0-1.0, default: 0.25)",
    )
    parser.add_argument(
        "--save-json", action="store_true", help="Also save results as JSON"
    )

    args = parser.parse_args()

    # Validate confidence
    if not 0.0 <= args.confidence <= 1.0:
        logger.error("Confidence must be between 0.0 and 1.0")
        return 1

    # Find images
    logger.info(f"Searching for images in {args.input}")
    image_paths = find_images(args.input)

    if not image_paths:
        logger.error("No images found")
        return 1

    logger.info(f"Found {len(image_paths)} images")

    # Initialize components
    logger.info(f"Loading YOLO model: {args.model}")
    detector = YOLODetector(model_name=args.model, confidence_threshold=args.confidence)

    classifier = ImageClassifier()
    manager = DetectionManager()

    # Run detection
    logger.info("Running object detection...")
    batch_results = detector.batch_detect(image_paths)

    # Classify images
    logger.info("Classifying images...")
    categories = classifier.classify_batch(batch_results)

    # Get statistics
    det_stats = manager.get_statistics(batch_results)
    cat_stats = classifier.get_category_statistics(batch_results)

    logger.info("\n=== Detection Statistics ===")
    logger.info(f"Total images: {det_stats['total_images']}")
    logger.info(f"Images with detections: {det_stats['images_with_detections']}")
    logger.info(f"Total objects detected: {det_stats['total_detections']}")
    logger.info(f"Average confidence: {det_stats['avg_confidence']:.2f}")
    logger.info(f"Unique classes: {det_stats['unique_classes']}")

    logger.info("\n=== Top Detected Classes ===")
    sorted_classes = sorted(
        det_stats["class_counts"].items(), key=lambda x: x[1], reverse=True
    )[:10]
    for cls, count in sorted_classes:
        logger.info(f"  {cls}: {count}")

    logger.info("\n=== Image Categories ===")
    for category, stats in cat_stats.items():
        logger.info(f"  {category}: {stats['count']} ({stats['percentage']:.1f}%)")

    # Save results
    logger.info(f"\nSaving results to {args.output}")

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save CSV
    manager.save_results_to_csv(batch_results, args.output)

    # Save JSON if requested
    if args.save_json:
        json_output = output_path.with_suffix(".json")
        manager.save_results_to_json(batch_results, str(json_output))
        logger.info(f"Saved JSON to {json_output}")

    # Save category summary
    category_output = output_path.parent / "image_categories.csv"
    import csv

    with open(category_output, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["image_path", "category", "channel_name", "message_id"])
        for image_path, category in categories.items():
            message_id = Path(image_path).stem
            channel_name = Path(image_path).parent.name
            writer.writerow([image_path, category, channel_name, message_id])

    logger.info(f"Saved category summary to {category_output}")

    logger.info("\n✅ YOLO detection complete!")
    logger.info(f"Results saved to: {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
