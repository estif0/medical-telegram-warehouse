# YOLO Object Detection Module

This module provides object detection and image classification capabilities using YOLOv8 for enriching scraped Telegram images with visual content analysis.

## Files

### `yolo_detector.py`

Object detection using YOLOv8 models. Processes images to detect objects with bounding boxes and confidence scores.

**Key Classes:**
- `YOLODetector`: Wrapper for YOLOv8 model with batch processing support

**Usage:**
```python
from src.yolo.yolo_detector import YOLODetector

detector = YOLODetector(model_name='yolov8n.pt', confidence_threshold=0.25)
detections = detector.detect_objects('image.jpg')
print(f"Found {len(detections)} objects")
```

### `image_classifier.py`

Classifies images into business-relevant categories based on detected objects.

**Categories:**
- `promotional`: Person + product (marketing content)
- `product_display`: Product only (product showcase)
- `lifestyle`: Person only (lifestyle marketing)
- `other`: Neither pattern

**Key Classes:**
- `ImageClassifier`: Categorizes images based on detection patterns

**Usage:**
```python
from src.yolo.image_classifier import ImageClassifier

classifier = ImageClassifier()
category = classifier.classify_image(detections)
print(f"Image category: {category}")
```

### `detection_manager.py`

Manages detection results storage, database integration, and statistical analysis.

**Key Classes:**
- `DetectionManager`: Handles saving/loading results and database preparation

**Usage:**
```python
from src.yolo.detection_manager import DetectionManager

manager = DetectionManager()
manager.save_results_to_csv(batch_results, 'detections.csv')
stats = manager.get_statistics(batch_results)
```

## Dependencies

- `ultralytics` - YOLOv8 framework
- `opencv-python` - Image processing
- `pillow` - Image handling
- `torch` - PyTorch for YOLO models

## Scripts

### `run_yolo_detection.py`

Main script to run YOLO detection pipeline on all images in data lake.

**Usage:**
```bash
# Basic usage
python scripts/run_yolo_detection.py

# Custom options
python scripts/run_yolo_detection.py --input data/raw/images --output results.csv --model yolov8n.pt --confidence 0.3

# Save JSON output
python scripts/run_yolo_detection.py --save-json
```

**Output:**
- `data/processed/detections.csv` - Detection results with bounding boxes
- `data/processed/image_categories.csv` - Image categories summary
- `data/processed/detections.json` - JSON format (optional)

## Testing

Tests are located in `tests/test_yolo_modules.py` and `tests/test_detection_manager.py`.

Run tests:
```bash
pytest tests/test_yolo_modules.py tests/test_detection_manager.py -v
```

**Test Coverage:**
- 14 tests for YOLODetector and ImageClassifier
- 12 tests for DetectionManager
- **Total: 26 tests passing** ✅

## Integration with Data Warehouse

Detection results are integrated into the star schema via the `fct_image_detections` dbt model:

```sql
-- Query examples
SELECT
    detected_class,
    COUNT(*) as count,
    AVG(confidence) as avg_confidence
FROM staging_marts.fct_image_detections
GROUP BY detected_class
ORDER BY count DESC;
```

## Notes

- Uses YOLOv8 nano model (`yolov8n.pt`) by default for speed
- Confidence threshold default is 0.25 (adjustable)
- Supports batch processing with progress logging
- Gracefully handles missing or corrupted images
- Classification based on COCO dataset classes (person, bottle, cup, etc.)
