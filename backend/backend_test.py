import pytest
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the backend URL from environment variable or use default
BACKEND_URL = "https://infinite-craft-backend-5ybw.onrender.com"
USER_ID = "test_user"

class TestInfiniteCraftAPI:
    def setup_method(self):
        """Setup before each test"""
        self.base_url = BACKEND_URL
        self.headers = {'Content-Type': 'application/json'}
        
        # Reset user progress before each test
        self.reset_user_progress()

    def reset_user_progress(self):
        """Reset user progress to initial state"""
        try:
            response = requests.post(
                f"{self.base_url}/api/user/reset",
                params={"user_id": USER_ID}
            )
            assert response.status_code == 200
            logger.info("User progress reset successfully")
        except Exception as e:
            logger.error(f"Error resetting user progress: {e}")
            raise

    def test_get_base_elements(self):
        """Test fetching base elements"""
        try:
            response = requests.get(f"{self.base_url}/api/elements/base")
            assert response.status_code == 200
            data = response.json()
            
            # Verify we have the expected base elements
            assert len(data) >= 4  # Should have at least Water, Fire, Wind, Earth
            base_names = {elem["name"] for elem in data}
            expected_names = {"Water", "Fire", "Wind", "Earth"}
            assert expected_names.issubset(base_names)
            
            logger.info("✅ Base elements test passed")
        except Exception as e:
            logger.error(f"❌ Base elements test failed: {e}")
            raise

    def test_get_discovered_elements(self):
        """Test fetching discovered elements"""
        try:
            response = requests.get(
                f"{self.base_url}/api/elements/discovered",
                params={"user_id": USER_ID}
            )
            assert response.status_code == 200
            data = response.json()
            
            # Initially should only have base elements
            assert len(data) >= 4
            logger.info("✅ Discovered elements test passed")
        except Exception as e:
            logger.error(f"❌ Discovered elements test failed: {e}")
            raise

    def test_combine_elements(self):
        """Test combining elements (Water + Fire = Steam)"""
        try:
            # First get base elements
            response = requests.get(f"{self.base_url}/api/elements/base")
            base_elements = response.json()
            
            # Find Water and Fire elements
            water = next(elem for elem in base_elements if elem["name"] == "Water")
            fire = next(elem for elem in base_elements if elem["name"] == "Fire")
            
            # Combine Water and Fire
            response = requests.post(
                f"{self.base_url}/api/elements/combine",
                json={
                    "element1_id": water["id"],
                    "element2_id": fire["id"],
                    "user_id": USER_ID
                }
            )
            assert response.status_code == 200
            data = response.json()
            
            # Verify combination was successful
            assert data["success"] == True
            assert data["result"]["name"] == "Steam"
            logger.info("✅ Element combination test passed")
            
            # Verify discovery was added
            response = requests.get(
                f"{self.base_url}/api/user/progress",
                params={"user_id": USER_ID}
            )
            progress = response.json()
            assert progress["discovery_count"] > 4  # Should be more than base elements
            logger.info("✅ Discovery counter test passed")
            
        except Exception as e:
            logger.error(f"❌ Element combination test failed: {e}")
            raise

    def test_user_progress(self):
        """Test user progress tracking"""
        try:
            # Get initial progress
            response = requests.get(
                f"{self.base_url}/api/user/progress",
                params={"user_id": USER_ID}
            )
            initial_progress = response.json()
            initial_count = initial_progress["discovery_count"]
            
            # Get base elements and combine some
            base_response = requests.get(f"{self.base_url}/api/elements/base")
            base_elements = base_response.json()
            
            # Combine first two elements
            response = requests.post(
                f"{self.base_url}/api/elements/combine",
                json={
                    "element1_id": base_elements[0]["id"],
                    "element2_id": base_elements[1]["id"],
                    "user_id": USER_ID
                }
            )
            
            # Check updated progress
            response = requests.get(
                f"{self.base_url}/api/user/progress",
                params={"user_id": USER_ID}
            )
            updated_progress = response.json()
            
            # Verify discovery count increased
            assert updated_progress["discovery_count"] > initial_count
            logger.info("✅ User progress test passed")
            
        except Exception as e:
            logger.error(f"❌ User progress test failed: {e}")
            raise

if __name__ == "__main__":
    # Run the tests
    test = TestInfiniteCraftAPI()
    test.setup_method()
    
    try:
        test.test_get_base_elements()
        test.test_get_discovered_elements()
        test.test_combine_elements()
        test.test_user_progress()
        logger.info("🎉 All backend tests passed successfully!")
    except Exception as e:
        logger.error(f"❌ Tests failed: {e}")
