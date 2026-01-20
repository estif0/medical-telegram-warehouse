"""
Report endpoints for analytical queries.

This module provides endpoints for generating analytical reports
about products, visual content, and business insights.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import logging

from api.database import get_db
from api.schemas import (
    TopProductsResponse,
    ProductStat,
    VisualContentStatsResponse,
    CategoryStat,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/top-products", response_model=TopProductsResponse)
def get_top_products(
    limit: int = Query(10, ge=1, le=100, description="Number of products to return"),
    db: Session = Depends(get_db),
):
    """
    Get top mentioned products across all channels.

    This endpoint searches message text for product keywords and returns
    statistics about the most frequently mentioned products.

    Args:
        limit: Maximum number of products to return (1-100)
        db: Database session

    Returns:
        TopProductsResponse with product statistics
    """
    try:
        # Common medical product keywords
        keywords = [
            "paracetamol",
            "ibuprofen",
            "aspirin",
            "amoxicillin",
            "vitamin",
            "cream",
            "serum",
            "lotion",
            "oil",
            "soap",
            "shampoo",
            "medicine",
            "tablet",
            "capsule",
            "syrup",
        ]

        products = []

        for keyword in keywords:
            query = text(
                """
                SELECT 
                    :keyword as product_name,
                    COUNT(*) as mention_count,
                    AVG(f.view_count) as avg_views,
                    ARRAY_AGG(DISTINCT c.channel_name) as channels
                FROM staging_marts.fct_messages f
                JOIN staging_marts.dim_channels c ON f.channel_key = c.channel_key
                WHERE LOWER(f.message_text) LIKE LOWER(:pattern)
                GROUP BY product_name
                HAVING COUNT(*) > 0
            """
            )

            result = db.execute(
                query, {"keyword": keyword, "pattern": f"%{keyword}%"}
            ).fetchone()

            if result and result.mention_count > 0:
                products.append(
                    ProductStat(
                        product_name=result.product_name,
                        mention_count=result.mention_count,
                        avg_views=float(result.avg_views or 0),
                        channels=result.channels or [],
                    )
                )

        # Sort by mention count
        products.sort(key=lambda x: x.mention_count, reverse=True)
        products = products[:limit]

        return TopProductsResponse(total_products=len(products), products=products)

    except Exception as e:
        logger.error(f"Error fetching top products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visual-content", response_model=VisualContentStatsResponse)
def get_visual_content_stats(
    channel: Optional[str] = Query(None, description="Filter by channel name"),
    db: Session = Depends(get_db),
):
    """
    Get statistics about visual content and object detection.

    This endpoint provides insights about image categories, detected objects,
    and visual content effectiveness across channels.

    Args:
        channel: Optional channel name filter
        db: Database session

    Returns:
        VisualContentStatsResponse with visual content statistics
    """
    try:
        # Check if detection data exists
        check_query = text(
            """
            SELECT COUNT(*) as count
            FROM information_schema.tables
            WHERE table_schema = 'raw'
            AND table_name = 'image_detections'
        """
        )

        table_exists = db.execute(check_query).fetchone()

        if not table_exists or table_exists.count == 0:
            # Return stats from CSV if table doesn't exist
            return _get_visual_stats_from_csv()

        # Build channel filter
        channel_filter = ""
        params = {}
        if channel:
            channel_filter = "WHERE c.channel_name = :channel"
            params["channel"] = channel

        # Get overall statistics
        stats_query = text(
            f"""
            SELECT 
                COUNT(DISTINCT f.message_id) as total_images,
                COUNT(DISTINCT CASE WHEN det.detected_class IS NOT NULL THEN f.message_id END) as images_with_detections,
                COUNT(det.detected_class) as total_detections
            FROM staging_marts.fct_messages f
            JOIN staging_marts.dim_channels c ON f.channel_key = c.channel_key
            LEFT JOIN raw.image_detections det ON f.message_id = det.message_id
            {channel_filter}
        """
        )

        stats = db.execute(stats_query, params).fetchone()

        # Get category statistics
        category_query = text(
            f"""
            SELECT 
                det.image_category as category,
                COUNT(DISTINCT f.message_id) as count,
                AVG(f.view_count) as avg_views,
                ARRAY_AGG(DISTINCT det.detected_class) FILTER (WHERE det.detected_class IS NOT NULL) as top_objects
            FROM staging_marts.fct_messages f
            JOIN staging_marts.dim_channels c ON f.channel_key = c.channel_key
            LEFT JOIN raw.image_detections det ON f.message_id = det.message_id
            {channel_filter}
            GROUP BY det.image_category
            HAVING det.image_category IS NOT NULL
        """
        )

        categories = []
        total_images = stats.total_images or 1

        for row in db.execute(category_query, params):
            categories.append(
                CategoryStat(
                    category=row.category or "unknown",
                    count=row.count,
                    percentage=round((row.count / total_images) * 100, 1),
                    avg_views=float(row.avg_views or 0),
                    top_objects=row.top_objects[:5] if row.top_objects else [],
                )
            )

        # Get top detected classes
        classes_query = text(
            f"""
            SELECT 
                det.detected_class,
                COUNT(*) as count
            FROM raw.image_detections det
            JOIN staging_marts.fct_messages f ON det.message_id = f.message_id
            JOIN staging_marts.dim_channels c ON f.channel_key = c.channel_key
            {channel_filter}
            WHERE det.detected_class IS NOT NULL
            GROUP BY det.detected_class
            ORDER BY count DESC
            LIMIT 10
        """
        )

        top_classes = {}
        for row in db.execute(classes_query, params):
            top_classes[row.detected_class] = row.count

        return VisualContentStatsResponse(
            total_images=stats.total_images or 0,
            images_with_detections=stats.images_with_detections or 0,
            total_detections=stats.total_detections or 0,
            categories=categories,
            top_detected_classes=top_classes,
        )

    except Exception as e:
        logger.error(f"Error fetching visual content stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_visual_stats_from_csv():
    """Fallback to get stats from CSV file if database table doesn't exist."""
    import pandas as pd
    from pathlib import Path

    try:
        detections_path = Path("data/processed/detections.csv")
        categories_path = Path("data/processed/image_categories.csv")

        if not detections_path.exists() or not categories_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Visual content data not found. Run YOLO detection first.",
            )

        df = pd.read_csv(detections_path)
        cat_df = pd.read_csv(categories_path)

        # Calculate statistics
        total_images = len(cat_df)
        images_with_detections = df[df["detected_class"].notna()][
            "message_id"
        ].nunique()
        total_detections = df["detected_class"].notna().sum()

        # Category statistics
        categories = []
        for category in cat_df["category"].unique():
            cat_count = (cat_df["category"] == category).sum()
            categories.append(
                CategoryStat(
                    category=category,
                    count=int(cat_count),
                    percentage=round((cat_count / total_images) * 100, 1),
                    avg_views=0.0,  # Not available from CSV
                    top_objects=[],
                )
            )

        # Top detected classes
        top_classes = df["detected_class"].value_counts().head(10).to_dict()

        return VisualContentStatsResponse(
            total_images=total_images,
            images_with_detections=images_with_detections,
            total_detections=int(total_detections),
            categories=categories,
            top_detected_classes=top_classes,
        )

    except Exception as e:
        logger.error(f"Error reading CSV files: {e}")
        raise HTTPException(status_code=500, detail=str(e))
