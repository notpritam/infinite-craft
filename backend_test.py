import requests
import unittest
import uuid

class InfiniteCraftAPITest(unittest.TestCase):
    def setUp(self):
        self.base_url = "https://infinite-craft-backend-ashy.vercel.app/api"
        self.test_user = f"test_user_{uuid.uuid4().hex[:8]}"

    def test_1_base_elements(self):
        """Test fetching base elements"""
        print("\nTesting base elements API...")
        response = requests.get(f"{self.base_url}/elements/base")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data) > 0)
        print(f"✅ Found {len(data)} base elements")

    def test_2_user_progress(self):
        """Test user progress functionality"""
        print("\nTesting user progress API...")
        response = requests.get(f"{self.base_url}/user/progress?user_id={self.test_user}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("discovery_count", data)
        print("✅ User progress API working")

    def test_3_discovered_elements(self):
        """Test discovered elements functionality"""
        print("\nTesting discovered elements API...")
        response = requests.get(f"{self.base_url}/elements/discovered?user_id={self.test_user}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(isinstance(data, list))
        print(f"✅ Found {len(data)} discovered elements")

    def test_4_element_combination(self):
        """Test element combination functionality"""
        print("\nTesting element combination API...")
        
        # First get base elements
        base_response = requests.get(f"{self.base_url}/elements/base")
        base_elements = base_response.json()
        
        if len(base_elements) >= 2:
            # Try to combine first two base elements
            combination_data = {
                "element1_id": base_elements[0]["id"],
                "element2_id": base_elements[1]["id"],
                "user_id": self.test_user
            }
            
            response = requests.post(
                f"{self.base_url}/elements/combine",
                json=combination_data
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("success", data)
            print("✅ Element combination API working")
        else:
            print("⚠️ Not enough base elements to test combination")

    def test_5_reset_progress(self):
        """Test resetting user progress"""
        print("\nTesting reset progress API...")
        response = requests.post(f"{self.base_url}/user/reset?user_id={self.test_user}")
        self.assertEqual(response.status_code, 200)
        print("✅ Reset progress API working")

if __name__ == "__main__":
    unittest.main(verbosity=2)
