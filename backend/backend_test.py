import pytest
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the backend URL from environment variable
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')

@pytest.mark.asyncio
async def test_base_elements():
    """Test fetching base elements"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BACKEND_URL}/api/elements/base")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 4  # Should have 4 base elements
        
        # Check each base element has required fields
        for element in data:
            assert "id" in element
            assert "name" in element
            assert "emoji" in element

@pytest.mark.asyncio
async def test_discovered_elements():
    """Test fetching discovered elements for a user"""
    test_user = "test_user_1"
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BACKEND_URL}/api/elements/discovered?user_id={test_user}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # New user should have access to base elements
        assert len(data) >= 4

@pytest.mark.asyncio
async def test_element_combination():
    """Test combining two elements"""
    async with httpx.AsyncClient() as client:
        # First get base elements
        response = await client.get(f"{BACKEND_URL}/api/elements/base")
        base_elements = response.json()
        
        # Try combining first two base elements
        combination_data = {
            "element1_id": base_elements[0]["id"],
            "element2_id": base_elements[1]["id"],
            "user_id": "test_user_1"
        }
        
        response = await client.post(
            f"{BACKEND_URL}/api/elements/combine",
            json=combination_data
        )
        assert response.status_code == 200
        result = response.json()
        assert result["success"] == True
        assert "result" in result
        assert "name" in result["result"]
        assert "emoji" in result["result"]

@pytest.mark.asyncio
async def test_user_progress():
    """Test user progress tracking"""
    test_user = "test_user_1"
    async with httpx.AsyncClient() as client:
        # Get initial progress
        response = await client.get(f"{BACKEND_URL}/api/user/progress?user_id={test_user}")
        assert response.status_code == 200
        initial_progress = response.json()
        assert "discovery_count" in initial_progress
        
        # Reset progress
        response = await client.post(f"{BACKEND_URL}/api/user/reset?user_id={test_user}")
        assert response.status_code == 200
        
        # Check progress after reset
        response = await client.get(f"{BACKEND_URL}/api/user/progress?user_id={test_user}")
        reset_progress = response.json()
        assert reset_progress["discovery_count"] == 4  # Should only have base elements

if __name__ == "__main__":
    pytest.main(["-v", "backend_test.py"])
