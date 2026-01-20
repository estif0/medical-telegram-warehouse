"""
Search endpoints for querying messages.

This module provides search functionality for finding messages
by keywords, dates, and other criteria.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import logging

from api.database import get_db
from api.schemas import MessageSearchResponse, Message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["Search"])


@router.get("/messages", response_model=MessageSearchResponse)
def search_messages(
    query: str = Query(..., min_length=1, description="Search query"),
    channel: Optional[str] = Query(None, description="Filter by channel name"),
    has_image: Optional[bool] = Query(None, description="Filter by image presence"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results to return"),
    db: Session = Depends(get_db),
):
    """
    Search messages by keyword.

    This endpoint searches message text for the specified query and returns
    matching messages with their metadata.

    Args:
        query: Search query (required)
        channel: Optional channel name filter
        has_image: Optional filter for images
        limit: Maximum number of results (1-100)
        db: Database session

    Returns:
        MessageSearchResponse with matching messages
    """
    try:
        # Build filters
        filters = ["LOWER(f.message_text) LIKE LOWER(:pattern)"]
        params = {"pattern": f"%{query}%", "limit": limit}

        if channel:
            filters.append("c.channel_name = :channel")
            params["channel"] = channel

        if has_image is not None:
            filters.append("f.has_image = :has_image")
            params["has_image"] = has_image

        where_clause = " AND ".join(filters)

        # Get total count
        count_query = text(
            f"""
            SELECT COUNT(*) as total
            FROM staging_marts.fct_messages f
            JOIN staging_marts.dim_channels c ON f.channel_key = c.channel_key
            JOIN staging_marts.dim_dates d ON f.date_key = d.date_key
            WHERE {where_clause}
        """
        )

        total = db.execute(count_query, params).fetchone().total

        # Get messages
        search_query = text(
            f"""
            SELECT 
                f.message_id,
                c.channel_name,
                d.full_date as message_date,
                f.message_text,
                f.view_count,
                f.has_image
            FROM staging_marts.fct_messages f
            JOIN staging_marts.dim_channels c ON f.channel_key = c.channel_key
            JOIN staging_marts.dim_dates d ON f.date_key = d.date_key
            WHERE {where_clause}
            ORDER BY f.view_count DESC NULLS LAST, d.full_date DESC
            LIMIT :limit
        """
        )

        messages = []
        for row in db.execute(search_query, params):
            messages.append(
                Message(
                    message_id=row.message_id,
                    channel_name=row.channel_name,
                    message_date=row.message_date,
                    message_text=row.message_text or "",
                    view_count=row.view_count,
                    has_image=row.has_image or False,
                )
            )

        return MessageSearchResponse(
            total_matches=total, query=query, messages=messages
        )

    except Exception as e:
        logger.error(f"Error searching messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keywords")
def get_common_keywords(
    limit: int = Query(20, ge=1, le=100, description="Number of keywords to return"),
    db: Session = Depends(get_db),
):
    """
    Get most common keywords from messages.

    This endpoint extracts and returns the most frequently occurring
    keywords from message text across all channels.

    Args:
        limit: Maximum number of keywords (1-100)
        db: Database session

    Returns:
        Dictionary with keyword frequencies
    """
    try:
        # Medical/pharmaceutical keywords to search for
        keywords = [
            "paracetamol",
            "ibuprofen",
            "aspirin",
            "amoxicillin",
            "medicine",
            "tablet",
            "capsule",
            "syrup",
            "cream",
            "lotion",
            "serum",
            "oil",
            "vitamin",
            "supplement",
            "drug",
            "pharmacy",
            "prescription",
            "treatment",
            "therapy",
            "diagnosis",
            "health",
            "wellness",
            "care",
            "medical",
            "clinical",
            "doctor",
            "patient",
        ]

        keyword_counts = []

        for keyword in keywords:
            query = text(
                """
                SELECT 
                    :keyword as keyword,
                    COUNT(*) as count
                FROM staging_marts.fct_messages
                WHERE LOWER(message_text) LIKE LOWER(:pattern)
            """
            )

            result = db.execute(
                query, {"keyword": keyword, "pattern": f"%{keyword}%"}
            ).fetchone()

            if result and result.count > 0:
                keyword_counts.append(
                    {"keyword": result.keyword, "count": result.count}
                )

        # Sort by count
        keyword_counts.sort(key=lambda x: x["count"], reverse=True)
        keyword_counts = keyword_counts[:limit]

        return {"total_keywords": len(keyword_counts), "keywords": keyword_counts}

    except Exception as e:
        logger.error(f"Error fetching keywords: {e}")
        raise HTTPException(status_code=500, detail=str(e))
