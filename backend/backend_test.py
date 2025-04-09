import requests
import unittest
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_URL = "https://1d0d519f-61bb-444b-a6c1-a4d185287a6a.preview.emergentagent.com"

class InfiniteCraftAPITest(unittest.TestCase):
    def setUp(self):
        self.base_url = f"{BACKEND_URL}/api"
        self.test_user = "test_user_123"

    def test_1_base_elements(self):
        """Test fetching base elements"""
        try:
            response = requests.get(f"{self.base_url}/elements/base")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Log the raw data for debugging
            logger.info("Base elements response: %s", json.dumps(data, indent=2))
            
            # Check we have the expected base elements
            self.assertTrue(len(data) > 0)
            
            # Verify each base element has required fields
            for element in data:
                self.assertIn("id", element)
                self.assertIn("name", element)
                self.assertIn("emoji", element)
                
            logger.info("Base elements test passed")
            return data
        except Exception as e:
            logger.error("Error in test_base_elements: %s", str(e))
            raise

    def test_2_element_combination(self):
        """Test combining elements"""
        try:
            # First get base elements
            base_elements = self.test_1_base_elements()
            
            if len(base_elements) < 2:
                logger.error("Not enough base elements to test combination")
                return
            
            # Try to combine first two base elements
            element1 = base_elements[0]
            element2 = base_elements[1]
            
            logger.info("Attempting to combine: %s + %s", 
                       f"{element1['emoji']} {element1['name']}", 
                       f"{element2['emoji']} {element2['name']}")
            
            response = requests.post(
                f"{self.base_url}/elements/combine",
                json={
                    "element1_id": element1["id"],
                    "element2_id": element2["id"],
                    "user_id": self.test_user
                }
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Log the combination result
            logger.info("Combination result: %s", json.dumps(data, indent=2))
            
            # Verify the response format
            self.assertIn("success", data)
            if data["success"]:
                self.assertIn("result", data)
                result = data["result"]
                self.assertIn("id", result)
                self.assertIn("name", result)
                self.assertIn("emoji", result)
            
            logger.info("Element combination test passed")
        except Exception as e:
            logger.error("Error in test_element_combination: %s", str(e))
            raise

    def test_3_user_progress(self):
        """Test user progress tracking"""
        try:
            response = requests.get(f"{self.base_url}/user/progress?user_id={self.test_user}")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Log the progress data
            logger.info("User progress: %s", json.dumps(data, indent=2))
            
            # Verify the response format
            self.assertIn("user_id", data)
            self.assertIn("discovery_count", data)
            self.assertIn("discovered_elements", data)
            
            # Verify the user has at least the base elements
            self.assertGreater(data["discovery_count"], 0)
            
            logger.info("User progress test passed")
        except Exception as e:
            logger.error("Error in test_user_progress: %s", str(e))
            raise

if __name__ == "__main__":
    unittest.main(verbosity=2)
