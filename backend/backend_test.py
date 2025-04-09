import pytest
import requests
import json
from datetime import datetime

class InfiniteCraftTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = f"test_user_{datetime.now().strftime('%H%M%S')}"

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params={'user_id': self.user_id} if 'user' in endpoint else None)
            elif method == 'POST':
                if data:
                    response = requests.post(url, json=data, headers=headers)
                else:
                    response = requests.post(url, params={'user_id': self.user_id}, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                return success, response.json()
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_base_elements(self):
        """Test getting base elements"""
        success, response = self.run_test(
            "Get Base Elements",
            "GET",
            "elements/base",
            200
        )
        if success:
            print(f"Found {len(response)} base elements")
            return response
        return []

    def test_discovered_elements(self):
        """Test getting discovered elements"""
        success, response = self.run_test(
            "Get Discovered Elements",
            "GET", 
            "elements/discovered",
            200
        )
        if success:
            print(f"Found {len(response)} discovered elements")
            return response
        return []

    def test_combine_elements(self, element1_id, element2_id):
        """Test combining elements"""
        success, response = self.run_test(
            "Combine Elements",
            "POST",
            "elements/combine",
            200,
            data={
                "element1_id": element1_id,
                "element2_id": element2_id
            }
        )
        if success and response.get('success'):
            print(f"Successfully combined elements into: {response['result']['name']}")
            return response['result']
        return None

    def test_reset_progress(self):
        """Test resetting user progress"""
        success, response = self.run_test(
            "Reset User Progress",
            "POST",
            "user/reset",
            200
        )
        return success

    def test_get_progress(self):
        """Test getting user progress"""
        success, response = self.run_test(
            "Get User Progress",
            "GET",
            "user/progress",
            200
        )
        if success:
            print(f"User has discovered {response['discovery_count']} elements")
            return response
        return None

def main():
    # Get backend URL from environment variable
    backend_url = "https://infinite-craft-backend-7tk2rvprxa-uc.a.run.app"
    
    # Setup tester
    tester = InfiniteCraftTester(backend_url)
    
    # Run tests
    print("\n🚀 Starting Infinite Craft API Tests...")
    
    # Test 1: Get base elements
    base_elements = tester.test_base_elements()
    if not base_elements:
        print("❌ Base elements test failed, stopping tests")
        return 1

    # Test 2: Get discovered elements (should be same as base initially)
    discovered = tester.test_discovered_elements()
    if not discovered:
        print("❌ Discovered elements test failed")
        return 1

    # Test 3: Combine first two base elements
    if len(base_elements) >= 2:
        result = tester.test_combine_elements(
            base_elements[0]['id'],
            base_elements[1]['id']
        )
        if not result:
            print("❌ Element combination failed")
            return 1

    # Test 4: Get progress after combination
    progress = tester.test_get_progress()
    if not progress:
        print("❌ Get progress test failed")
        return 1

    # Test 5: Reset progress
    if not tester.test_reset_progress():
        print("❌ Reset progress test failed")
        return 1

    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

@pytest.fixture
def tester():
    backend_url = "https://infinite-craft-backend-7tk2rvprxa-uc.a.run.app"
    return InfiniteCraftTester(backend_url)

def test_infinite_craft_api(tester):
    """Test the complete Infinite Craft API flow"""
    
    # Test 1: Get base elements
    base_elements = tester.test_base_elements()
    assert base_elements, "Failed to get base elements"

    # Test 2: Get discovered elements (should be same as base initially)
    discovered = tester.test_discovered_elements()
    assert discovered, "Failed to get discovered elements"

    # Test 3: Combine first two base elements
    if len(base_elements) >= 2:
        result = tester.test_combine_elements(
            base_elements[0]['id'],
            base_elements[1]['id']
        )
        assert result, "Failed to combine elements"

    # Test 4: Get progress after combination
    progress = tester.test_get_progress()
    assert progress, "Failed to get user progress"

    # Test 5: Reset progress
    assert tester.test_reset_progress(), "Failed to reset progress"

if __name__ == "__main__":
    pytest.main(["-v", __file__])
