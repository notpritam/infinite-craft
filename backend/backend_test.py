import requests
import pytest
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get backend URL from frontend .env
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if 'REACT_APP_BACKEND_URL' in line:
            BACKEND_URL = line.split('=')[1].strip().strip('"')
            break

class TestInfiniteCraftAPI:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_user_id = "test_user_123"
        self.base_elements = None
        self.element1_id = None
        self.element2_id = None

    def test_api_root(self):
        """Test the root API endpoint"""
        response = requests.get(f"{self.base_url}/api")
        assert response.status_code == 200
        assert "message" in response.json()
        logger.info("✅ Root API endpoint test passed")

    def test_get_base_elements(self):
        """Test getting base elements"""
        response = requests.get(f"{self.base_url}/api/elements/base")
        assert response.status_code == 200
        elements = response.json()
        assert len(elements) > 0
        assert all(["id" in elem and "name" in elem and "emoji" in elem for elem in elements])
        self.base_elements = elements
        self.element1_id = elements[0]["id"]  # Store for combination test
        self.element2_id = elements[1]["id"]  # Store for combination test
        logger.info(f"✅ Base elements test passed. Found {len(elements)} elements")

    def test_get_discovered_elements(self):
        """Test getting discovered elements for a user"""
        response = requests.get(f"{self.base_url}/api/elements/discovered?user_id={self.test_user_id}")
        assert response.status_code == 200
        elements = response.json()
        assert len(elements) > 0  # Should at least have base elements
        logger.info(f"✅ Discovered elements test passed. Found {len(elements)} elements")

    def test_combine_elements(self):
        """Test combining two elements"""
        if not self.element1_id or not self.element2_id:
            self.test_get_base_elements()

        data = {
            "element1_id": self.element1_id,
            "element2_id": self.element2_id
        }
        response = requests.post(
            f"{self.base_url}/api/elements/combine?user_id={self.test_user_id}",
            json=data
        )
        assert response.status_code == 200
        result = response.json()
        assert "success" in result
        if result["success"]:
            assert "result" in result
            assert "name" in result["result"]
            assert "emoji" in result["result"]
            logger.info(f"✅ Element combination test passed. Created: {result['result']['emoji']} {result['result']['name']}")
        else:
            logger.info("✅ Element combination test passed with expected failure response")

    def test_user_progress(self):
        """Test getting user progress"""
        response = requests.get(f"{self.base_url}/api/user/progress?user_id={self.test_user_id}")
        assert response.status_code == 200
        progress = response.json()
        assert "user_id" in progress
        assert "discovery_count" in progress
        assert "discovered_elements" in progress
        assert progress["discovery_count"] > 0
        logger.info(f"✅ User progress test passed. Discoveries: {progress['discovery_count']}")

    def test_reset_user_progress(self):
        """Test resetting user progress"""
        response = requests.post(f"{self.base_url}/api/user/reset?user_id={self.test_user_id}")
        assert response.status_code == 200
        assert "message" in response.json()

        # Verify reset by checking progress
        progress_response = requests.get(f"{self.base_url}/api/user/progress?user_id={self.test_user_id}")
        progress = progress_response.json()
        assert progress["discovery_count"] == 4  # Should only have base elements
        logger.info("✅ Reset user progress test passed")

    def run_all_tests(self):
        """Run all API tests"""
        try:
            logger.info("\n🔍 Starting Infinite Craft API Tests...")
            
            self.test_api_root()
            self.test_get_base_elements()
            self.test_get_discovered_elements()
            self.test_combine_elements()
            self.test_user_progress()
            self.test_reset_user_progress()
            
            logger.info("\n✨ All API tests completed successfully!")
            return True
        except Exception as e:
            logger.error(f"\n❌ Test failed: {str(e)}")
            return False

if __name__ == "__main__":
    tester = TestInfiniteCraftAPI()
    tester.run_all_tests()