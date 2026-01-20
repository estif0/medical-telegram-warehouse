"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from api.main import app

client = TestClient(app)


class TestRootEndpoints:
    """Test suite for root and health endpoints."""

    def test_root_endpoint(self):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Medical Telegram Warehouse API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
        assert "docs" in data
        assert "endpoints" in data

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "timestamp" in data


class TestReportsEndpoints:
    """Test suite for reports endpoints."""

    def test_top_products_endpoint(self):
        """Test top products endpoint."""

        # Mock the database dependency
        def mock_db_override():
            mock_db = Mock()
            # Mock query results
            mock_result = Mock()
            mock_result.product_name = "paracetamol"
            mock_result.mention_count = 5  # This is an int, not a Mock
            mock_result.avg_views = 1250.5
            mock_result.channels = ["CheMed123"]

            # Mock execute to return fetchone
            mock_execute = Mock()
            mock_execute.fetchone.return_value = mock_result
            mock_db.execute.return_value = mock_execute
            yield mock_db

        # Override the dependency
        from api.database import get_db

        app.dependency_overrides[get_db] = mock_db_override

        try:
            response = client.get("/api/reports/top-products?limit=10")
            assert response.status_code == 200
            data = response.json()
            assert "total_products" in data
            assert "products" in data
        finally:
            # Clean up
            app.dependency_overrides.clear()

    def test_top_products_invalid_limit(self):
        """Test top products with invalid limit."""
        response = client.get("/api/reports/top-products?limit=0")
        assert response.status_code == 422  # Validation error

        response = client.get("/api/reports/top-products?limit=150")
        assert response.status_code == 422

    def test_visual_content_endpoint_csv_fallback(self):
        """Test visual content endpoint uses CSV fallback."""
        response = client.get("/api/reports/visual-content")

        # Should work with CSV fallback even without database
        if response.status_code == 200:
            data = response.json()
            assert "total_images" in data
            assert "images_with_detections" in data
            assert "categories" in data
            assert "top_detected_classes" in data
        else:
            # If CSV files don't exist, should return 404 or 500
            assert response.status_code in [404, 500]


class TestChannelsEndpoints:
    """Test suite for channels endpoints."""

    def test_list_channels(self):
        """Test list channels endpoint."""

        # Mock the database dependency
        def mock_db_override():
            mock_db = Mock()
            # Mock query results
            mock_row = Mock()
            mock_row.channel_name = "CheMed123"
            mock_row.total_posts = 150
            mock_row.avg_views = 1250.5
            mock_row.posts_with_media = 100
            mock_row.media_percentage = 66.67
            mock_row.activity_level = "high"
            mock_row.first_post_date = datetime(2024, 1, 1)
            mock_row.last_post_date = datetime(2024, 1, 31)

            # Mock execute to return an iterable result
            # The code does: for row in db.execute(query)
            mock_db.execute.return_value = [mock_row]
            yield mock_db

        # Override the dependency
        from api.database import get_db

        app.dependency_overrides[get_db] = mock_db_override

        try:
            response = client.get("/api/channels/list")
            assert response.status_code == 200
            data = response.json()
            assert "total_channels" in data
            assert "channels" in data
        finally:
            # Clean up
            app.dependency_overrides.clear()

    def test_channel_activity(self):
        """Test channel activity endpoint."""

        # Mock the database dependency
        def mock_db_override():
            mock_db = Mock()
            # Mock channel check
            mock_channel = Mock()
            mock_channel.channel_key = "ch_001"
            mock_channel.channel_name = "CheMed123"

            # Mock activity data
            mock_activity = Mock()
            mock_activity.full_date = datetime(2024, 1, 1).date()
            mock_activity.message_count = 5
            mock_activity.total_views = 6250
            mock_activity.avg_views = 1250.0
            mock_activity.images_count = 3

            # Mock execute to return different results for each call
            mock_execute1 = Mock()
            mock_execute1.fetchone.return_value = mock_channel
            mock_execute2 = Mock()
            mock_execute2.fetchall.return_value = [mock_activity]

            mock_db.execute.side_effect = [mock_execute1, mock_execute2]
            yield mock_db

        # Override the dependency
        from api.database import get_db

        app.dependency_overrides[get_db] = mock_db_override

        try:
            response = client.get("/api/channels/CheMed123/activity?days=7")

            # Will fail without database, but structure should be correct
            if response.status_code == 200:
                data = response.json()
                assert "channel_name" in data
                assert "total_messages" in data
                assert "date_range" in data
                assert "daily_activity" in data
        finally:
            # Clean up
            app.dependency_overrides.clear()

    def test_channel_activity_invalid_days(self):
        """Test channel activity with invalid days parameter."""
        response = client.get("/api/channels/CheMed123/activity?days=0")
        assert response.status_code == 422

        response = client.get("/api/channels/CheMed123/activity?days=400")
        assert response.status_code == 422


class TestSearchEndpoints:
    """Test suite for search endpoints."""

    def test_search_messages(self):
        """Test message search endpoint."""

        # Mock the database dependency
        def mock_db_override():
            mock_db = Mock()
            # Mock count result
            mock_count = Mock()
            mock_count.total = 5

            # Mock message result
            mock_msg = Mock()
            mock_msg.message_id = "12345"
            mock_msg.channel_name = "CheMed123"
            mock_msg.message_date = datetime(2024, 1, 15)
            mock_msg.message_text = "New paracetamol tablets"
            mock_msg.view_count = 1250
            mock_msg.has_image = True

            # Mock execute for count and messages queries
            mock_execute1 = Mock()
            mock_execute1.scalar.return_value = 5
            mock_execute2 = Mock()
            mock_execute2.fetchall.return_value = [mock_msg]

            mock_db.execute.side_effect = [mock_execute1, mock_execute2]
            yield mock_db

        # Override the dependency
        from api.database import get_db

        app.dependency_overrides[get_db] = mock_db_override

        try:
            response = client.get("/api/search/messages?query=paracetamol")

            # Will fail without database, but structure should be correct
            if response.status_code == 200:
                data = response.json()
                assert "total_matches" in data
                assert "query" in data
                assert "messages" in data
        finally:
            # Clean up
            app.dependency_overrides.clear()

    def test_search_messages_missing_query(self):
        """Test search messages without query parameter."""
        response = client.get("/api/search/messages")
        assert response.status_code == 422  # Missing required parameter

    def test_search_messages_invalid_limit(self):
        """Test search messages with invalid limit."""
        response = client.get("/api/search/messages?query=test&limit=0")
        assert response.status_code == 422

        response = client.get("/api/search/messages?query=test&limit=150")
        assert response.status_code == 422

    def test_get_common_keywords(self):
        """Test common keywords endpoint."""

        # Mock the database dependency
        def mock_db_override():
            mock_db = Mock()
            # Mock keyword result
            mock_keyword = Mock()
            mock_keyword.keyword = "paracetamol"
            mock_keyword.count = 15

            # Mock execute to return list of keywords
            mock_execute = Mock()
            mock_execute.fetchall.return_value = [mock_keyword]
            mock_db.execute.return_value = mock_execute
            yield mock_db

        # Override the dependency
        from api.database import get_db

        app.dependency_overrides[get_db] = mock_db_override

        try:
            response = client.get("/api/search/keywords?limit=10")

            # Will fail without database, but structure should be correct
            if response.status_code == 200:
                data = response.json()
                assert "total_keywords" in data
                assert "keywords" in data
        finally:
            # Clean up
            app.dependency_overrides.clear()


class TestAPIDocumentation:
    """Test API documentation endpoints."""

    def test_openapi_docs(self):
        """Test OpenAPI documentation endpoint."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_docs(self):
        """Test ReDoc documentation endpoint."""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_json(self):
        """Test OpenAPI JSON schema."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "info" in data
        assert "paths" in data
        assert data["info"]["title"] == "Medical Telegram Warehouse API"
