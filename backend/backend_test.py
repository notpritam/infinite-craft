import requests
import pytest
import os
from datetime import datetime

BACKEND_URL = "https://1d0d519f-61bb-444b-a6c1-a4d185287a6a.preview.emergentagent.com"

class TestInfiniteCraftAPI:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_user = f"test_user_{datetime.now().strftime('%H%M%S')}"
        self.test_results = []

    def log_test(self, name, success, message=""):
        self.test_results.append({
            "name": name,
            "success": success,
            "message": message
        })
        status = "✅" if success else "❌"
        print(f"{status} {name}: {message}")

    def test_base_elements(self):
        try:
            response = requests.get(f"{self.base_url}/api/elements/base")
            success = response.status_code == 200 and len(response.json()) > 0
            self.log_test(
                "Base Elements API",
                success,
                f"Found {len(response.json())} base elements" if success else "Failed to get base elements"
            )
            return response.json() if success else []
        except Exception as e:
            self.log_test("Base Elements API", False, str(e))
            return []

    def test_discovered_elements(self):
        try:
            response = requests.get(f"{self.base_url}/api/elements/discovered?user_id={self.test_user}")
            success = response.status_code == 200
            self.log_test(
                "Discovered Elements API",
                success,
                f"Found {len(response.json())} discovered elements" if success else "Failed to get discovered elements"
            )
            return response.json() if success else []
        except Exception as e:
            self.log_test("Discovered Elements API", False, str(e))
            return []

    def test_user_progress(self):
        try:
            response = requests.get(f"{self.base_url}/api/user/progress?user_id={self.test_user}")
            success = response.status_code == 200 and "discovery_count" in response.json()
            self.log_test(
                "User Progress API",
                success,
                f"Discovery count: {response.json().get('discovery_count')}" if success else "Failed to get user progress"
            )
            return response.json() if success else None
        except Exception as e:
            self.log_test("User Progress API", False, str(e))
            return None

    def test_element_combination(self, element1_id, element2_id):
        try:
            response = requests.post(
                f"{self.base_url}/api/elements/combine",
                json={
                    "element1_id": element1_id,
                    "element2_id": element2_id,
                    "user_id": self.test_user
                }
            )
            data = response.json()
            success = response.status_code == 200 and data.get("success", False)
            self.log_test(
                "Element Combination API",
                success,
                f"Created: {data['result']['name']}" if success else data.get("message", "Combination failed")
            )
            return data if success else None
        except Exception as e:
            self.log_test("Element Combination API", False, str(e))
            return None

    def test_reset_progress(self):
        try:
            response = requests.post(f"{self.base_url}/api/user/reset?user_id={self.test_user}")
            success = response.status_code == 200
            self.log_test(
                "Reset Progress API",
                success,
                "Successfully reset progress" if success else "Failed to reset progress"
            )
            return success
        except Exception as e:
            self.log_test("Reset Progress API", False, str(e))
            return False

def main():
    print("\n🧪 Starting Infinite Craft API Tests...")
    tester = TestInfiniteCraftAPI()

    # Test base elements
    base_elements = tester.test_base_elements()
    
    # Test discovered elements
    discovered_elements = tester.test_discovered_elements()
    
    # Test user progress
    progress = tester.test_user_progress()
    
    # Test element combination if we have base elements
    if len(base_elements) >= 2:
        tester.test_element_combination(
            base_elements[0]["id"],
            base_elements[1]["id"]
        )
    
    # Test reset progress
    tester.test_reset_progress()
    
    # Print summary
    print("\n📊 Test Summary:")
    total_tests = len(tester.test_results)
    passed_tests = sum(1 for test in tester.test_results if test["success"])
    print(f"Passed: {passed_tests}/{total_tests} tests")
    
    return 0 if passed_tests == total_tests else 1

if __name__ == "__main__":
    main()