"""
Integration tests for content API endpoints.
"""

import json
import pytest
from unittest.mock import patch
from app.auth import generate_tokens
from tests.factories import ContentFactory, UserFactory, ProcessedContentFactory


class TestContentAPI:
    """Integration tests for content management endpoints"""

    @pytest.fixture
    def auth_headers(self, test_user):
        """Generate auth headers for test user"""
        tokens = generate_tokens(test_user)
        return {
            "HTTP_AUTHORIZATION": f"Bearer {tokens['access_token']}",
        }

    def test_create_content_success(self, api_client, test_user, auth_headers, mock_queue):
        """Test successful content creation"""
        content_data = {
            "name": "Introduction to Python",
            "content": "Python is a high-level programming language...",
        }

        response = api_client.post(
            "/api/content",
            data=json.dumps(content_data),
            content_type="application/json",
            **auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == content_data["name"]
        assert data["content"] == content_data["content"]
        assert data["processed"] is False
        assert "id" in data

        # Verify async task was queued
        mock_queue.enqueue.assert_called_once()

    def test_create_content_with_control_characters(
        self, api_client, auth_headers, mock_queue
    ):
        """Test content creation with control characters (sanitization)"""
        content_data = {
            "name": "Test\x00Content\x0c",
            "content": "Content with\x00control\x1fcharacters",
        }

        response = api_client.post(
            "/api/content",
            data=json.dumps(content_data),
            content_type="application/json",
            **auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "\x00" not in data["name"]
        assert "\x00" not in data["content"]

    def test_create_content_invalid_data(self, api_client, auth_headers):
        """Test content creation with invalid data"""
        response = api_client.post(
            "/api/content",
            data=json.dumps({"name": "No content field"}),
            content_type="application/json",
            **auth_headers
        )

        assert response.status_code == 400
        assert "error" in response.json()

    def test_get_content_success(self, api_client, test_user):
        """Test retrieving content"""
        # Create content for the test user
        content = ContentFactory(user=test_user)
        
        # Generate auth headers for the content owner
        tokens = generate_tokens(test_user)
        auth_headers = {
            "HTTP_AUTHORIZATION": f"Bearer {tokens['access_token']}",
        }

        response = api_client.get(f"/api/content/{content.id}", **auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == content.id
        assert data["name"] == content.name
        assert data["content"] == content.content

    def test_get_content_not_found(self, api_client, auth_headers):
        """Test retrieving non-existent content"""
        response = api_client.get("/api/content/99999", **auth_headers)

        assert response.status_code == 404
        assert "error" in response.json()

    def test_get_deleted_content_not_found(self, api_client, test_user):
        """Test that soft-deleted content is not accessible"""
        content = ContentFactory(user=test_user, is_deleted=True)
        
        # Generate auth headers for the content owner
        tokens = generate_tokens(test_user)
        auth_headers = {
            "HTTP_AUTHORIZATION": f"Bearer {tokens['access_token']}",
        }

        response = api_client.get(f"/api/content/{content.id}", **auth_headers)

        assert response.status_code == 404

    def test_list_contents_success(self, api_client, test_user):
        """Test listing contents for authenticated user"""
        # Create contents for test user
        contents = ContentFactory.create_batch(3, user=test_user)
        # Create content for another user (should not appear)
        other_content = ContentFactory()
        
        # Generate auth headers
        tokens = generate_tokens(test_user)
        auth_headers = {
            "HTTP_AUTHORIZATION": f"Bearer {tokens['access_token']}",
        }

        response = api_client.get("/api/content", **auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3  # Only user's contents

        # Verify ordering by created_at descending
        created_times = [item["created_at"] for item in data]
        assert created_times == sorted(created_times, reverse=True)

    def test_list_contents_pagination(self, api_client, test_user):
        """Test content listing with pagination"""
        ContentFactory.create_batch(15, user=test_user)
        
        # Generate auth headers
        tokens = generate_tokens(test_user)
        auth_headers = {
            "HTTP_AUTHORIZATION": f"Bearer {tokens['access_token']}",
        }

        response = api_client.get("/api/content?limit=5&offset=5", **auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    def test_delete_content_success(self, api_client, test_user):
        """Test content deletion (soft delete)"""
        content = ContentFactory(user=test_user)
        
        # Generate auth headers
        tokens = generate_tokens(test_user)
        auth_headers = {
            "HTTP_AUTHORIZATION": f"Bearer {tokens['access_token']}",
        }

        response = api_client.delete(f"/api/content/{content.id}", **auth_headers)

        assert response.status_code == 200
        assert response.json()["status"] == "success"

        # Verify soft delete
        content.refresh_from_db()
        assert content.is_deleted is True

    def test_delete_content_not_found(self, api_client, auth_headers):
        """Test deleting non-existent content"""
        response = api_client.delete("/api/content/99999", **auth_headers)

        assert response.status_code == 404
        assert "error" in response.json()

    def test_health_check(self, api_client):
        """Test health check endpoint"""
        response = api_client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "service" in data
