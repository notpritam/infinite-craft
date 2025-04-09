import unittest
import requests
import os
import json
from datetime import datetime

class InfiniteCraftAPITest(unittest.TestCase):
    def setUp(self):
        self.base_url = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
        self.test_user = f"test_user_{datetime.now().strftime('%H%M%S')}"
        print(f"\nTesting with base URL: {self.base_url}")

    def test_01_api_root(self):
        """Test API root endpoint"""
        print("\nTesting API root endpoint...")
        response = requests.get(f"{self.base_url}/api")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Infinite Craft API"})
        print("✅ API root endpoint test passed")

    def test_02_base_elements(self):
        """Test fetching base elements"""
        print("\nTesting base elements endpoint...")
        response = requests.get(f"{self.base_url}/api/elements/base")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)
        # Verify base elements structure
        for element in data:
            self.assertIn('id', element)
            self.assertIn('name', element)
            self.assertIn('emoji', element)
        print(f"✅ Base elements test passed. Found {len(data)} base elements")

    def test_03_discovered_elements(self):
        """Test fetching discovered elements for a new user"""
        print("\nTesting discovered elements endpoint...")
        response = requests.get(f"{self.base_url}/api/elements/discovered?user_id={self.test_user}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        # New user should have access to base elements
        self.assertTrue(len(data) > 0)
        print(f"✅ Discovered elements test passed. Found {len(data)} elements")

    def test_04_combine_elements(self):
        """Test combining elements"""
        print("\nTesting element combination...")
        # First get base elements
        base_response = requests.get(f"{self.base_url}/api/elements/base")
        base_elements = base_response.json()
        
        if len(base_elements) < 2:
            self.fail("Not enough base elements for combination test")
        
        # Try combining first two base elements
        combination_data = {
            "element1_id": base_elements[0]['id'],
            "element2_id": base_elements[1]['id'],
            "user_id": self.test_user
        }
        
        response = requests.post(
            f"{self.base_url}/api/elements/combine",
            json=combination_data
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn('success', result)
        if result['success']:
            self.assertIn('result', result)
            self.assertIn('name', result['result'])
            self.assertIn('emoji', result['result'])
            print(f"✅ Successfully combined {base_elements[0]['name']} + {base_elements[1]['name']} = {result['result']['name']}")
        else:
            print(f"⚠️ Combination did not produce a new element: {result.get('message', 'No message')}")

    def test_05_user_progress(self):
        """Test user progress tracking"""
        print("\nTesting user progress endpoint...")
        response = requests.get(f"{self.base_url}/api/user/progress?user_id={self.test_user}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('user_id', data)
        self.assertIn('discovery_count', data)
        self.assertIn('discovered_elements', data)
        print(f"✅ User progress test passed. Discovery count: {data['discovery_count']}")

    def test_06_reset_progress(self):
        """Test resetting user progress"""
        print("\nTesting reset progress endpoint...")
        response = requests.post(f"{self.base_url}/api/user/reset?user_id={self.test_user}")
        self.assertEqual(response.status_code, 200)
        
        # Verify reset by checking progress
        progress_response = requests.get(f"{self.base_url}/api/user/progress?user_id={self.test_user}")
        progress_data = progress_response.json()
        
        # After reset, user should only have base elements
        base_response = requests.get(f"{self.base_url}/api/elements/base")
        base_elements = base_response.json()
        
        self.assertEqual(len(progress_data['discovered_elements']), len(base_elements))
        print("✅ Reset progress test passed")

if __name__ == '__main__':
    unittest.main(verbosity=2)
