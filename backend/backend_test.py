import pytest
import requests
import uuid
from typing import Dict

class InfiniteCraftTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = f"test_user_{uuid.uuid4()}"

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, data: Dict = None) -> tuple:
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url)
            elif method == 'POST':
                response = requests.post(url, json=data)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                if response.text:
                    print(f"Response: {response.json()}")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                if response.text:
                    print(f"Error: {response.text}")

            return success, response.json() if response.text else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_api_root(self):
        """Test root API endpoint"""
        return self.run_test("API Root", "GET", "", 200)

    def test_get_base_elements(self):
        """Test getting base elements"""
        return self.run_test("Get Base Elements", "GET", "elements/base", 200)

    def test_get_discovered_elements(self):
        """Test getting discovered elements"""
        return self.run_test("Get Discovered Elements", "GET", f"elements/discovered?user_id={self.user_id}", 200)

    def test_combine_elements(self, element1_id: str, element2_id: str):
        """Test combining elements"""
        data = {
            "element1_id": element1_id,
            "element2_id": element2_id
        }
        return self.run_test(
            "Combine Elements",
            "POST",
            f"elements/combine?user_id={self.user_id}",
            200,
            data
        )

    def test_reset_user_progress(self):
        """Test resetting user progress"""
        return self.run_test(
            "Reset User Progress",
            "POST",
            f"user/reset?user_id={self.user_id}",
            200
        )

    def test_get_user_progress(self):
        """Test getting user progress"""
        return self.run_test(
            "Get User Progress",
            "GET",
            f"user/progress?user_id={self.user_id}",
            200
        )

def main():
    # Initialize tester with the backend URL
    tester = InfiniteCraftTester("https://infinite-craft-backend-7cqk.onrender.com")
    
    # Test 1: API Root
    tester.test_api_root()
    
    # Test 2: Get Base Elements
    success, base_elements = tester.test_get_base_elements()
    if not success or not base_elements:
        print("❌ Failed to get base elements, stopping tests")
        return
    
    # Test 3: Get Initial Discovered Elements
    success, discovered = tester.test_get_discovered_elements()
    if not success:
        print("❌ Failed to get discovered elements")
        return
    
    # Test 4: Combine Elements (using first two base elements)
    if len(base_elements) >= 2:
        element1 = base_elements[0]
        element2 = base_elements[1]
        success, result = tester.test_combine_elements(element1['id'], element2['id'])
        if not success:
            print("❌ Failed to combine elements")
            return
    
    # Test 5: Get User Progress
    success, progress = tester.test_get_user_progress()
    if not success:
        print("❌ Failed to get user progress")
        return
    
    # Test 6: Reset User Progress
    success, _ = tester.test_reset_user_progress()
    if not success:
        print("❌ Failed to reset user progress")
        return
    
    # Print final results
    print(f"\n📊 Tests Summary:")
    print(f"Total Tests: {tester.tests_run}")
    print(f"Passed: {tester.tests_passed}")
    print(f"Failed: {tester.tests_run - tester.tests_passed}")
    
    return tester.tests_passed == tester.tests_run

if __name__ == "__main__":
    main()