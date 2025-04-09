import requests
import pytest
import json

# Use the public endpoint from frontend/.env
BACKEND_URL = "https://1d0d519f-61bb-444b-a6c1-a4d185287a6a.preview.emergentagent.com"
USER_ID = "test_user"

class TestInfiniteCraftAPI:
    def test_base_elements(self):
        """Test fetching base elements"""
        response = requests.get(f"{BACKEND_URL}/api/elements/base")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4  # Water, Fire, Wind, Earth
        
        # Verify base elements
        element_names = {elem["name"] for elem in data}
        expected_names = {"Water", "Fire", "Wind", "Earth"}
        assert element_names == expected_names

    def test_discovered_elements_initial(self):
        """Test initial discovered elements for new user"""
        response = requests.get(f"{BACKEND_URL}/api/elements/discovered?user_id={USER_ID}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4  # Should start with base elements
        
    def test_user_progress(self):
        """Test user progress endpoint"""
        response = requests.get(f"{BACKEND_URL}/api/user/progress?user_id={USER_ID}")
        assert response.status_code == 200
        data = response.json()
        assert "discovery_count" in data
        assert "discovered_elements" in data
        assert len(data["discovered_elements"]) >= 4  # At least base elements
        
    def test_element_combination(self):
        """Test combining elements"""
        # First get base elements
        base_response = requests.get(f"{BACKEND_URL}/api/elements/base")
        base_elements = base_response.json()
        
        # Try combining first two elements
        combination_data = {
            "element1_id": base_elements[0]["id"],
            "element2_id": base_elements[1]["id"]
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/elements/combine",
            json=combination_data
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        
        # Even if combination fails, response should be valid
        assert isinstance(data["success"], bool)
        if data["success"]:
            assert "result" in data
            assert "name" in data["result"]
            assert "emoji" in data["result"]
    
    def test_reset_progress(self):
        """Test resetting user progress"""
        # Reset progress
        reset_response = requests.post(f"{BACKEND_URL}/api/user/reset?user_id={USER_ID}")
        assert reset_response.status_code == 200
        
        # Verify reset
        progress_response = requests.get(f"{BACKEND_URL}/api/user/progress?user_id={USER_ID}")
        data = progress_response.json()
        assert data["discovery_count"] == 4  # Only base elements
        assert len(data["discovered_elements"]) == 4

if __name__ == "__main__":
    pytest.main([__file__])