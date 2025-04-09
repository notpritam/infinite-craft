import requests
import pytest
import uuid

class TestInfiniteCraftAPI:
    def __init__(self):
        self.base_url = "https://infinite-craft-backend-ashy.vercel.app/api"
        self.test_user_id = f"test_user_{uuid.uuid4()}"
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0
        }

    def run_test(self, test_name, test_func):
        """Helper to run tests and track results"""
        self.test_results["total_tests"] += 1
        print(f"\n🧪 Running test: {test_name}")
        try:
            test_func()
            self.test_results["passed_tests"] += 1
            print(f"✅ Test passed: {test_name}")
            return True
        except Exception as e:
            self.test_results["failed_tests"] += 1
            print(f"❌ Test failed: {test_name}")
            print(f"Error: {str(e)}")
            return False

    def test_get_base_elements(self):
        """Test fetching base elements"""
        def test():
            response = requests.get(f"{self.base_url}/elements/base")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0
            # Verify base elements structure
            for element in data:
                assert "id" in element
                assert "name" in element
                assert "emoji" in element
            print(f"Found {len(data)} base elements")
        
        self.run_test("Get Base Elements", test)

    def test_get_discovered_elements(self):
        """Test fetching discovered elements"""
        def test():
            response = requests.get(f"{self.base_url}/elements/discovered?user_id={self.test_user_id}")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            # New user should have base elements
            assert len(data) > 0
            print(f"Found {len(data)} discovered elements")
        
        self.run_test("Get Discovered Elements", test)

    def test_combine_elements(self):
        """Test combining two elements"""
        def test():
            # First get base elements
            base_response = requests.get(f"{self.base_url}/elements/base")
            base_elements = base_response.json()
            assert len(base_elements) >= 2
            
            # Try combining first two base elements
            element1 = base_elements[0]
            element2 = base_elements[1]
            
            combine_data = {
                "element1_id": element1["id"],
                "element2_id": element2["id"]
            }
            
            response = requests.post(
                f"{self.base_url}/elements/combine?user_id={self.test_user_id}",
                json=combine_data
            )
            assert response.status_code == 200
            data = response.json()
            assert "success" in data
            assert data["success"] == True
            assert "result" in data
            result = data["result"]
            assert "id" in result
            assert "name" in result
            assert "emoji" in result
            print(f"Successfully combined {element1['name']} + {element2['name']} = {result['name']}")
        
        self.run_test("Combine Elements", test)

    def test_user_progress(self):
        """Test user progress tracking"""
        def test():
            response = requests.get(f"{self.base_url}/user/progress?user_id={self.test_user_id}")
            assert response.status_code == 200
            data = response.json()
            assert "user_id" in data
            assert "discovery_count" in data
            assert "discovered_elements" in data
            assert isinstance(data["discovered_elements"], list)
            print(f"User has discovered {data['discovery_count']} elements")
        
        self.run_test("User Progress", test)

    def test_reset_progress(self):
        """Test resetting user progress"""
        def test():
            # Reset progress
            reset_response = requests.post(f"{self.base_url}/user/reset?user_id={self.test_user_id}")
            assert reset_response.status_code == 200
            
            # Verify reset
            progress_response = requests.get(f"{self.base_url}/user/progress?user_id={self.test_user_id}")
            data = progress_response.json()
            
            # After reset, should only have base elements
            base_response = requests.get(f"{self.base_url}/elements/base")
            base_elements = base_response.json()
            assert len(data["discovered_elements"]) == len(base_elements)
            print("Successfully reset user progress")
        
        self.run_test("Reset Progress", test)

    def run_all_tests(self):
        """Run all tests and print summary"""
        print("\n🚀 Starting Infinite Craft API Tests...")
        
        self.test_get_base_elements()
        self.test_get_discovered_elements()
        self.test_combine_elements()
        self.test_user_progress()
        self.test_reset_progress()
        
        print("\n📊 Test Summary:")
        print(f"Total Tests: {self.test_results['total_tests']}")
        print(f"Passed: {self.test_results['passed_tests']}")
        print(f"Failed: {self.test_results['failed_tests']}")
        
        return self.test_results["failed_tests"] == 0

if __name__ == "__main__":
    tester = TestInfiniteCraftAPI()
    success = tester.run_all_tests()
    exit(0 if success else 1)
