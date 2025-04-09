import pytest
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get backend URL from frontend .env
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1].strip('"').strip("'")
            break

@pytest.mark.asyncio
async def test_base_elements():
    """Test fetching base elements"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BACKEND_URL}/api/elements/base")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 4  # Should have 4 base elements
        
        # Verify base elements
        element_names = {elem["name"] for elem in data}
        assert element_names == {"Water", "Fire", "Wind", "Earth"}

@pytest.mark.asyncio
async def test_discovered_elements():
    """Test fetching discovered elements"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BACKEND_URL}/api/elements/discovered?user_id=test_user")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Initially should have base elements
        assert len(data) >= 4

@pytest.mark.asyncio
async def test_combine_elements():
    """Test combining elements"""
    async with httpx.AsyncClient() as client:
        # First get base elements
        response = await client.get(f"{BACKEND_URL}/api/elements/base")
        base_elements = response.json()
        
        # Find Water and Fire elements
        water = next(elem for elem in base_elements if elem["name"] == "Water")
        fire = next(elem for elem in base_elements if elem["name"] == "Fire")
        
        # Try to combine Water and Fire
        response = await client.post(
            f"{BACKEND_URL}/api/elements/combine",
            json={
                "element1_id": water["id"],
                "element2_id": fire["id"],
                "user_id": "test_user"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "result" in data
        assert data["result"]["name"] == "Steam"  # Expected result

@pytest.mark.asyncio
async def test_user_progress():
    """Test user progress tracking"""
    async with httpx.AsyncClient() as client:
        # Get initial progress
        response = await client.get(f"{BACKEND_URL}/api/user/progress?user_id=test_user")
        assert response.status_code == 200
        initial_data = response.json()
        assert "discovery_count" in initial_data
        
        # Reset progress
        response = await client.post(f"{BACKEND_URL}/api/user/reset?user_id=test_user")
        assert response.status_code == 200
        
        # Verify reset
        response = await client.get(f"{BACKEND_URL}/api/user/progress?user_id=test_user")
        reset_data = response.json()
        assert reset_data["discovery_count"] == 4  # Should have only base elements

if __name__ == "__main__":
    pytest.main([__file__, "-v"])