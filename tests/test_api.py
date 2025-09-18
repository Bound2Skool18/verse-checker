"""
Unit tests for the Bible Verse Checker API.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestAPI:
    """Test cases for API endpoints."""
    
    def test_root_endpoint(self):
        """Test the root endpoint returns basic information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "endpoints" in data
    
    def test_health_endpoint(self):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_check_endpoint_valid_quote(self):
        """Test checking a valid Bible quote."""
        response = client.post("/check", json={"quote": "For God so loved the world"})
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        required_fields = ["match", "score", "reference", "text"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Check data types
        assert isinstance(data["match"], bool)
        assert isinstance(data["score"], (int, float))
        assert isinstance(data["reference"], str)
        assert isinstance(data["text"], str)
        assert 0.0 <= data["score"] <= 1.0, "Score should be between 0 and 1"
    
    def test_check_endpoint_exact_match(self):
        """Test with an exact Bible verse match."""
        exact_verse = "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life."
        response = client.post("/check", json={"quote": exact_verse})
        assert response.status_code == 200
        data = response.json()
        
        assert data["match"] is True, "Exact match should be True"
        assert data["score"] > 0.9, "Exact match should have high similarity score"
        assert "John 3:16" in data["reference"], "Should identify John 3:16"
    
    def test_check_endpoint_partial_quote(self):
        """Test with a partial Bible quote."""
        response = client.post("/check", json={"quote": "The Lord is my shepherd"})
        assert response.status_code == 200
        data = response.json()
        
        # Should find Psalm 23:1
        assert data["score"] > 0.7, "Partial match should have good similarity"
        assert "Psalm" in data["reference"], "Should identify a Psalm"
    
    def test_check_endpoint_non_biblical_quote(self):
        """Test with a non-biblical quote."""
        response = client.post("/check", json={"quote": "To be or not to be, that is the question"})
        assert response.status_code == 200
        data = response.json()
        
        assert data["match"] is False, "Non-biblical quote should not match"
        assert data["score"] < 0.7, "Non-biblical quote should have low similarity"
    
    def test_check_endpoint_empty_quote(self):
        """Test with an empty quote."""
        response = client.post("/check", json={"quote": ""})
        assert response.status_code == 200
        data = response.json()
        
        assert data["match"] is False
        assert data["score"] == 0.0
        assert "Empty quote" in data.get("message", "")
    
    def test_check_endpoint_whitespace_quote(self):
        """Test with whitespace-only quote."""
        response = client.post("/check", json={"quote": "   "})
        assert response.status_code == 200
        data = response.json()
        
        assert data["match"] is False
        assert data["score"] == 0.0
    
    def test_check_endpoint_long_quote(self):
        """Test with a very long quote (should be rejected)."""
        long_quote = "a" * 1001  # Longer than max_length of 1000
        response = client.post("/check", json={"quote": long_quote})
        assert response.status_code == 422  # Validation error
    
    def test_check_endpoint_missing_quote(self):
        """Test with missing quote field."""
        response = client.post("/check", json={})
        assert response.status_code == 422  # Validation error
    
    def test_check_endpoint_invalid_json(self):
        """Test with invalid JSON."""
        response = client.post("/check", 
                             headers={"Content-Type": "application/json"},
                             content="{invalid json}")
        assert response.status_code == 422
    
    def test_check_endpoint_wrong_field_name(self):
        """Test with wrong field name."""
        response = client.post("/check", json={"text": "For God so loved the world"})
        assert response.status_code == 422  # Should require 'quote' field

class TestBiblicalQuotes:
    """Test with various biblical quotes to verify accuracy."""
    
    @pytest.mark.parametrize("quote,expected_book,expected_score_min", [
        ("I can do all things through Christ", "Philippians", 0.7),
        ("Trust in the Lord with all your heart", "Proverbs", 0.7),
        ("Faith is the substance of things hoped for", "Hebrews", 0.7),
        ("Love is patient, love is kind", "Corinthians", 0.6),  # Paraphrase
        ("In the beginning was the Word", "John", 0.0),  # Not in our dataset
    ])
    def test_various_quotes(self, quote, expected_book, expected_score_min):
        """Test various biblical quotes."""
        response = client.post("/check", json={"quote": quote})
        assert response.status_code == 200
        data = response.json()
        
        if expected_score_min > 0:
            assert data["score"] >= expected_score_min, f"Score too low for '{quote}'"
            if data["match"]:
                assert expected_book in data["reference"], f"Expected {expected_book} in reference"

class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_invalid_http_method(self):
        """Test using wrong HTTP method."""
        response = client.get("/check")
        assert response.status_code == 405  # Method not allowed
    
    def test_wrong_content_type(self):
        """Test with wrong content type."""
        response = client.post("/check", 
                             headers={"Content-Type": "text/plain"},
                             content="For God so loved the world")
        assert response.status_code == 422

if __name__ == "__main__":
    pytest.main([__file__, "-v"])