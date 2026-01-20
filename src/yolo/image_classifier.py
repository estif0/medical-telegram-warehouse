"""
Image Classifier for medical product images.

This module classifies images based on detected objects into categories
relevant for medical business analysis.

Example:
    >>> from src.yolo.image_classifier import ImageClassifier
    >>> classifier = ImageClassifier()
    >>> category = classifier.classify_image(detections)
    >>> print(category)  # 'promotional', 'product_display', etc.
"""

from typing import List, Dict, Any
import logging

from src.utils.logger import get_logger


class ImageClassifier:
    """
    Classify images based on YOLO detection results.

    Categories:
        - promotional: Images with person AND product (marketing content)
        - product_display: Product/bottle without person (product showcase)
        - lifestyle: Person without clear product (lifestyle content)
        - other: Neither pattern detected

    Example:
        >>> classifier = ImageClassifier()
        >>> detections = [
        ...     {'class': 'person', 'confidence': 0.9},
        ...     {'class': 'bottle', 'confidence': 0.8}
        ... ]
        >>> category = classifier.classify_image(detections)
        >>> print(category)  # 'promotional'
    """

    # YOLO class names relevant to medical/pharmaceutical content
    PERSON_CLASSES = {"person"}
    PRODUCT_CLASSES = {"bottle", "cup", "bowl", "vase", "potted plant"}
    MEDICAL_RELEVANT = {"bottle", "cup", "cell phone", "book"}

    def __init__(self):
        """Initialize the image classifier."""
        self.logger = get_logger(__name__)

    def classify_image(self, detections: List[Dict[str, Any]]) -> str:
        """
        Classify image based on detected objects.

        Args:
            detections: List of detection dictionaries from YOLODetector

        Returns:
            Category string: 'promotional', 'product_display', 'lifestyle', or 'other'

        Example:
            >>> classifier = ImageClassifier()
            >>> detections = [{'class': 'bottle', 'confidence': 0.85}]
            >>> category = classifier.classify_image(detections)
            >>> print(category)  # 'product_display'
        """
        if not detections:
            return "other"

        # Get unique detected classes
        detected_classes = {det["class"].lower() for det in detections}

        # Check for person presence
        has_person = bool(detected_classes & self.PERSON_CLASSES)

        # Check for product presence
        has_product = bool(detected_classes & self.PRODUCT_CLASSES)

        # Classification logic
        if has_person and has_product:
            return "promotional"
        elif has_product and not has_person:
            return "product_display"
        elif has_person and not has_product:
            return "lifestyle"
        else:
            return "other"

    def get_dominant_objects(
        self, detections: List[Dict[str, Any]], top_n: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get the most prominent objects based on confidence scores.

        Args:
            detections: List of detection dictionaries
            top_n: Number of top objects to return

        Returns:
            List of top N detections sorted by confidence

        Example:
            >>> classifier = ImageClassifier()
            >>> dominant = classifier.get_dominant_objects(detections, top_n=3)
            >>> for obj in dominant:
            ...     print(f"{obj['class']}: {obj['confidence']:.2f}")
        """
        if not detections:
            return []

        # Sort by confidence (descending)
        sorted_detections = sorted(
            detections, key=lambda x: x["confidence"], reverse=True
        )

        return sorted_detections[:top_n]

    def get_classification_confidence(self, detections: List[Dict[str, Any]]) -> float:
        """
        Get confidence score for the classification.

        Args:
            detections: List of detection dictionaries

        Returns:
            Average confidence of relevant detected objects

        Example:
            >>> classifier = ImageClassifier()
            >>> confidence = classifier.get_classification_confidence(detections)
            >>> print(f"Classification confidence: {confidence:.2f}")
        """
        if not detections:
            return 0.0

        # Get confidences of relevant objects (person, product)
        relevant_classes = self.PERSON_CLASSES | self.PRODUCT_CLASSES
        relevant_confidences = [
            det["confidence"]
            for det in detections
            if det["class"].lower() in relevant_classes
        ]

        if not relevant_confidences:
            # Use average of all detections if no relevant classes found
            return sum(det["confidence"] for det in detections) / len(detections)

        return sum(relevant_confidences) / len(relevant_confidences)

    def get_detailed_classification(
        self, detections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get detailed classification with metadata.

        Args:
            detections: List of detection dictionaries

        Returns:
            Dictionary containing:
                - category: Classification category
                - confidence: Classification confidence
                - dominant_objects: Top 3 detected objects
                - has_person: Boolean indicating person presence
                - has_product: Boolean indicating product presence
                - total_objects: Total number of detected objects

        Example:
            >>> classifier = ImageClassifier()
            >>> details = classifier.get_detailed_classification(detections)
            >>> print(f"Category: {details['category']}")
            >>> print(f"Confidence: {details['confidence']:.2f}")
        """
        category = self.classify_image(detections)
        confidence = self.get_classification_confidence(detections)
        dominant = self.get_dominant_objects(detections, top_n=3)

        detected_classes = {det["class"].lower() for det in detections}
        has_person = bool(detected_classes & self.PERSON_CLASSES)
        has_product = bool(detected_classes & self.PRODUCT_CLASSES)

        return {
            "category": category,
            "confidence": confidence,
            "dominant_objects": [
                {"class": obj["class"], "confidence": obj["confidence"]}
                for obj in dominant
            ],
            "has_person": has_person,
            "has_product": has_product,
            "total_objects": len(detections),
            "unique_classes": list(detected_classes),
        }

    def classify_batch(
        self, batch_detections: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, str]:
        """
        Classify multiple images in batch.

        Args:
            batch_detections: Dictionary mapping image paths to detection lists

        Returns:
            Dictionary mapping image paths to categories

        Example:
            >>> classifier = ImageClassifier()
            >>> batch = {
            ...     'img1.jpg': [{'class': 'person', 'confidence': 0.9}],
            ...     'img2.jpg': [{'class': 'bottle', 'confidence': 0.8}]
            ... }
            >>> categories = classifier.classify_batch(batch)
            >>> for img, cat in categories.items():
            ...     print(f"{img}: {cat}")
        """
        results = {}

        for image_path, detections in batch_detections.items():
            category = self.classify_image(detections)
            results[image_path] = category

        self.logger.info(f"Classified {len(results)} images")
        return results

    def get_category_statistics(
        self, batch_detections: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Get statistics about classification categories in a batch.

        Args:
            batch_detections: Dictionary mapping image paths to detection lists

        Returns:
            Dictionary with category counts and percentages

        Example:
            >>> classifier = ImageClassifier()
            >>> stats = classifier.get_category_statistics(batch_detections)
            >>> print(stats['promotional'])  # {'count': 5, 'percentage': 33.3}
        """
        categories = self.classify_batch(batch_detections)

        category_counts = {}
        for category in categories.values():
            category_counts[category] = category_counts.get(category, 0) + 1

        total = len(categories)
        statistics = {}

        for category, count in category_counts.items():
            statistics[category] = {
                "count": count,
                "percentage": (count / total * 100) if total > 0 else 0,
            }

        return statistics
