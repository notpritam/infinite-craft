import requests
import unittest
import uuid
from datetime import datetime

class InfiniteCraftAPITester(unittest.TestCase):
    def setUp(self):
        self.base_url = "https://infinite-craft-backend-ashy.vercel.app"
        self.user_id = f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def test_01_base_elements(self):
        """Test if base elements are available"""
        print("\n🔍 Testing base elements API...")
        response = requests.get(f"{self.base_url}/api/elements/base")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify we have exactly 4 base elements
        self.assertEqual(len(data), 4)
        
        # Check if all required base elements exist
        element_names = {elem["name"] for elem in data}
        required_elements = {"Water", "Fire", "Wind", "Earth"}
        self.assertEqual(element_names, required_elements)
        
        # Check if each element has required fields
        for element in data:
            self.assertIn("id", element)
            self.assertIn("name", element)
            self.assertIn("emoji", element)
        
        print("✅ Base elements test passed")

    def test_02_discovered_elements_for_new_user(self):
        """Test if a new user gets base elements as discovered elements"""
        print("\n🔍 Testing discovered elements for new user...")
        response = requests.get(f"{self.base_url}/api/elements/discovered?user_id={self.user_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # New user should have exactly 4 base elements
        self.assertEqual(len(data), 4)
        print("✅ Discovered elements test passed")

    def test_03_combine_elements(self):
        """Test element combination functionality"""
        print("\n🔍 Testing element combination...")
        
        # First get base elements
        response = requests.get(f"{self.base_url}/api/elements/base")
        base_elements = response.json()
        
        # Try combining first two elements
        element1 = base_elements[0]
        element2 = base_elements[1]
        
        combination_data = {
            "element1_id": element1["id"],
            "element2_id": element2["id"],
            "user_id": self.user_id
        }
        
        response = requests.post(
            f"{self.base_url}/api/elements/combine",
            json=combination_data
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify combination response structure
        self.assertIn("success", data)
        self.assertTrue(data["success"])
        self.assertIn("result", data)
        self.assertIn("message", data)
        
        # Verify result element structure
        result_element = data["result"]
        self.assertIn("id", result_element)
        self.assertIn("name", result_element)
        self.assertIn("emoji", result_element)
        
        print("✅ Element combination test passed")

    def test_04_user_progress(self):
        """Test user progress tracking"""
        print("\n🔍 Testing user progress...")
        response = requests.get(f"{self.base_url}/api/user/progress?user_id={self.user_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify progress data structure
        self.assertIn("user_id", data)
        self.assertIn("discovery_count", data)
        self.assertIn("discovered_elements", data)
        
        # New user should have at least 4 discoveries (base elements)
        self.assertGreaterEqual(data["discovery_count"], 4)
        print("✅ User progress test passed")

    def test_05_reset_progress(self):
        """Test resetting user progress"""
        print("\n🔍 Testing progress reset...")
        response = requests.post(f"{self.base_url}/api/user/reset?user_id={self.user_id}")
        self.assertEqual(response.status_code, 200)
        
        # Verify user has only base elements after reset
        response = requests.get(f"{self.base_url}/api/elements/discovered?user_id={self.user_id}")
        data = response.json()
        self.assertEqual(len(data), 4)  # Should only have base elements
        print("✅ Progress reset test passed")

if __name__ == "__main__":
    unittest.main(argv=[''], verbosity=2)
