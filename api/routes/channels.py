"""
Channel-specific endpoints.

This module provides endpoints for querying channel activity
and statistics over time.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Path
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from datetime import datetime, timedelta
import logging

from api.database import get_db
from api.schemas import ChannelActivityResponse, ChannelActivityDay

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/channels", tags=["Channels"])


@router.get("/{channel_name}/activity", response_model=ChannelActivityResponse)
def get_channel_activity(
    channel_name: str = Path(..., description="Channel name"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
):
    """
    Get channel activity over time.

    This endpoint provides daily statistics for a specific channel including
    message counts, view metrics, and image usage over a specified period.

    Args:
        channel_name: Name of the channel
        days: Number of days to look back (1-365)
        db: Database session

    Returns:
        ChannelActivityResponse with daily activity statistics
    """
    try:
        # Check if channel exists
        channel_check = text(
            """
            SELECT channel_key, channel_name
            FROM staging_marts.dim_channels
            WHERE channel_name = :channel_name
        """
        )

        channel = db.execute(channel_check, {"channel_name": channel_name}).fetchone()

        if not channel:
            raise HTTPException(
                status_code=404, detail=f"Channel '{channel_name}' not found"
            )

        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        # Get daily activity
        activity_query = text(
            """
            SELECT 
                d.full_date,
                COUNT(f.message_id) as message_count,
                COALESCE(SUM(f.view_count), 0) as total_views,
                COALESCE(AVG(f.view_count), 0) as avg_views,
                COUNT(CASE WHEN f.has_image THEN 1 END) as images_count
            FROM staging_marts.dim_dates d
            LEFT JOIN staging_marts.fct_messages f 
                ON d.date_key = f.date_key 
                AND f.channel_key = :channel_key
            WHERE d.full_date BETWEEN :start_date AND :end_date
            GROUP BY d.full_date
            ORDER BY d.full_date
        """
        )

        daily_activity = []
        total_messages = 0

        for row in db.execute(
            activity_query,
            {
                "channel_key": channel.channel_key,
                "start_date": start_date,
                "end_date": end_date,
            },
        ):
            total_messages += row.message_count
            daily_activity.append(
                ChannelActivityDay(
                    date=row.full_date.isoformat(),
                    message_count=row.message_count,
                    total_views=int(row.total_views),
                    avg_views=float(row.avg_views),
                    images_count=row.images_count,
                )
            )

        return ChannelActivityResponse(
            channel_name=channel_name,
            total_messages=total_messages,
            date_range={"start": start_date.isoformat(), "end": end_date.isoformat()},
            daily_activity=daily_activity,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching channel activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
def list_channels(db: Session = Depends(get_db)):
    """
    Get list of all available channels.

    Args:
        db: Database session

    Returns:
        List of channels with basic statistics
    """
    try:
        query = text(
            """
            SELECT 
                c.channel_name,
                c.total_posts,
                c.avg_views,
                c.first_post_date,
                c.last_post_date,
                c.posts_with_media,
                c.media_percentage,
                c.activity_level
            FROM staging_marts.dim_channels c
            ORDER BY c.total_posts DESC
        """
        )

        channels = []
        for row in db.execute(query):
            channels.append(
                {
                    "channel_name": row.channel_name,
                    "total_posts": row.total_posts,
                    "avg_views": float(row.avg_views or 0),
                    "posts_with_media": row.posts_with_media or 0,
                    "media_percentage": float(row.media_percentage or 0),
                    "activity_level": row.activity_level or "unknown",
                    "first_post_date": (
                        row.first_post_date.isoformat() if row.first_post_date else None
                    ),
                    "last_post_date": (
                        row.last_post_date.isoformat() if row.last_post_date else None
                    ),
                }
            )

        return {"total_channels": len(channels), "channels": channels}

    except Exception as e:
        logger.error(f"Error listing channels: {e}")
        raise HTTPException(status_code=500, detail=str(e))
