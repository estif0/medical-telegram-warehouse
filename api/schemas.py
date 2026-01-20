"""
Pydantic models for API request/response validation.

This module defines schemas for all API endpoints to ensure
data validation and provide automatic API documentation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ProductStat(BaseModel):
    """Statistics for a product mention."""

    product_name: str = Field(..., description="Product or keyword")
    mention_count: int = Field(..., description="Number of mentions")
    avg_views: float = Field(..., description="Average views per mention")
    channels: List[str] = Field(..., description="Channels mentioning the product")

    class Config:
        json_schema_extra = {
            "example": {
                "product_name": "paracetamol",
                "mention_count": 15,
                "avg_views": 1250.5,
                "channels": ["CheMed123", "tikvahpharma"],
            }
        }


class TopProductsResponse(BaseModel):
    """Response for top products endpoint."""

    total_products: int = Field(..., description="Total number of products found")
    products: List[ProductStat] = Field(..., description="List of product statistics")

    class Config:
        json_schema_extra = {
            "example": {
                "total_products": 3,
                "products": [
                    {
                        "product_name": "paracetamol",
                        "mention_count": 15,
                        "avg_views": 1250.5,
                        "channels": ["CheMed123"],
                    }
                ],
            }
        }


class ChannelActivityDay(BaseModel):
    """Activity data for a single day."""

    date: str = Field(..., description="Date (YYYY-MM-DD)")
    message_count: int = Field(..., description="Number of messages")
    total_views: int = Field(..., description="Total views")
    avg_views: float = Field(..., description="Average views per message")
    images_count: int = Field(..., description="Number of messages with images")


class ChannelActivityResponse(BaseModel):
    """Response for channel activity endpoint."""

    channel_name: str = Field(..., description="Channel name")
    total_messages: int = Field(..., description="Total messages in period")
    date_range: dict = Field(..., description="Start and end dates")
    daily_activity: List[ChannelActivityDay] = Field(
        ..., description="Daily statistics"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "channel_name": "CheMed123",
                "total_messages": 150,
                "date_range": {"start": "2024-01-01", "end": "2024-01-31"},
                "daily_activity": [
                    {
                        "date": "2024-01-01",
                        "message_count": 5,
                        "total_views": 6250,
                        "avg_views": 1250.0,
                        "images_count": 3,
                    }
                ],
            }
        }


class Message(BaseModel):
    """Message search result."""

    message_id: str = Field(..., description="Message ID")
    channel_name: str = Field(..., description="Channel name")
    message_date: datetime = Field(..., description="Message date")
    message_text: str = Field(..., description="Message text")
    view_count: Optional[int] = Field(None, description="View count")
    has_image: bool = Field(..., description="Whether message has an image")

    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "12345",
                "channel_name": "CheMed123",
                "message_date": "2024-01-15T10:30:00",
                "message_text": "New paracetamol tablets available",
                "view_count": 1250,
                "has_image": True,
            }
        }


class MessageSearchResponse(BaseModel):
    """Response for message search endpoint."""

    total_matches: int = Field(..., description="Total number of matching messages")
    query: str = Field(..., description="Search query used")
    messages: List[Message] = Field(..., description="List of matching messages")

    class Config:
        json_schema_extra = {
            "example": {
                "total_matches": 15,
                "query": "paracetamol",
                "messages": [
                    {
                        "message_id": "12345",
                        "channel_name": "CheMed123",
                        "message_date": "2024-01-15T10:30:00",
                        "message_text": "New paracetamol tablets available",
                        "view_count": 1250,
                        "has_image": True,
                    }
                ],
            }
        }


class CategoryStat(BaseModel):
    """Statistics for an image category."""

    category: str = Field(..., description="Image category")
    count: int = Field(..., description="Number of images")
    percentage: float = Field(..., description="Percentage of total")
    avg_views: float = Field(..., description="Average views for this category")
    top_objects: List[str] = Field(..., description="Most detected objects")


class VisualContentStatsResponse(BaseModel):
    """Response for visual content statistics endpoint."""

    total_images: int = Field(..., description="Total images analyzed")
    images_with_detections: int = Field(..., description="Images with detected objects")
    total_detections: int = Field(..., description="Total objects detected")
    categories: List[CategoryStat] = Field(..., description="Statistics by category")
    top_detected_classes: dict = Field(
        ..., description="Most frequently detected objects"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_images": 207,
                "images_with_detections": 143,
                "total_detections": 543,
                "categories": [
                    {
                        "category": "product_display",
                        "count": 52,
                        "percentage": 25.1,
                        "avg_views": 1200.5,
                        "top_objects": ["bottle", "cup"],
                    }
                ],
                "top_detected_classes": {"bottle": 226, "person": 173},
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="API status")
    database: str = Field(..., description="Database connection status")
    timestamp: datetime = Field(..., description="Current timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "database": "connected",
                "timestamp": "2024-01-20T10:30:00",
            }
        }
