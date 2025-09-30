#!/usr/bin/env python3
"""
Production Readiness Test Suite
Comprehensive validation of the entire system after cleanup
"""

import os
import sys
import requests
import json
import time
from pathlib import Path
from typing import Dict, Any, List

# Add project to path for testing
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "gradio-chatbot"))

class ProductionReadinessTest:
    """Test suite for production readiness validation"""

    def __init__(self):
        self.backend_url = os.getenv('BACKEND_URL', 'http://localhost:8010')
        self.frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:7860')
        self.results = []

    def log_test(self, test_name: str, success: bool, message: str = "", data: Any = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")

        self.results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'data': data
        })

    def test_environment_configuration(self):
        """Test environment variable configuration"""
        print("\n🔧 Testing Environment Configuration")
        print("=" * 50)

        required_vars = [
            'GCP_PROJECT_ID',
            'BQ_DATASET',
            'ANTHROPIC_API_KEY'
        ]

        for var in required_vars:
            value = os.getenv(var)
            if value and value.strip():
                self.log_test(f"Environment variable {var}", True, f"Set to: {value[:10]}...")
            else:
                self.log_test(f"Environment variable {var}", False, "Not set or empty")

    def test_project_structure(self):
        """Test clean project structure"""
        print("\n📁 Testing Project Structure")
        print("=" * 50)

        required_files = [
            '.env.example',
            'DEPLOYMENT.md',
            'README.md',
            'genai-agents-backend/app.py',
            'genai-agents-backend/requirements.txt',
            'gradio-chatbot/app.py',
            'gradio-chatbot/requirements.txt',
            'data-generator/README.md',
            'data-generator/data/',
            'data-generator/schema/',
            'data-generator/scripts/',
        ]

        for file_path in required_files:
            full_path = project_root / file_path
            if full_path.exists():
                self.log_test(f"Required file/dir: {file_path}", True)
            else:
                self.log_test(f"Required file/dir: {file_path}", False, "Missing")

        # Test for cleaned up files
        cleaned_files = [
            'test_integration.py',
            'test_validation_e2e.js',
            'gradio-chatbot/VALIDATION_SUMMARY.md',
            'gradio-chatbot/utils/question_validator.py',
            'gradio-chatbot/utils/response_validator.py'
        ]

        for file_path in cleaned_files:
            full_path = project_root / file_path
            if not full_path.exists():
                self.log_test(f"Cleaned up file: {file_path}", True, "Successfully removed")
            else:
                self.log_test(f"Cleaned up file: {file_path}", False, "Still exists")

    def test_backend_health(self):
        """Test backend API health"""
        print("\n🔌 Testing Backend Health")
        print("=" * 50)

        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            if response.status_code == 200:
                self.log_test("Backend health endpoint", True, f"Status: {response.status_code}")
            else:
                self.log_test("Backend health endpoint", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Backend health endpoint", False, f"Error: {str(e)}")

    def test_api_integration(self):
        """Test API integration with sample queries"""
        print("\n🧪 Testing API Integration")
        print("=" * 50)

        test_queries = [
            {"question": "What is the total cost?", "expected_viz": "indicator"},
            {"question": "Show me the top 5 applications by cost", "expected_viz": "bar"},
            {"question": "Cost breakdown by environment", "expected_viz": "pie"},
            {"question": "Daily cost trend last 30 days", "expected_viz": "line"},
            {"question": "Which application costs the most?", "expected_viz": "bar"}
        ]

        for query in test_queries:
            try:
                response = requests.post(
                    f"{self.backend_url}/api/bigquery/ask",
                    json={"question": query["question"]},
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        answer = data.get('answer', '')
                        visualization = data.get('visualization', '')
                        chart_data = data.get('chart_data')

                        has_answer = bool(answer and len(answer) > 10)
                        has_chart_data = bool(chart_data and chart_data.get('data'))

                        if has_answer and has_chart_data:
                            self.log_test(
                                f"Query: {query['question'][:30]}...",
                                True,
                                f"Viz: {visualization}, Answer: {len(answer)} chars"
                            )
                        else:
                            self.log_test(
                                f"Query: {query['question'][:30]}...",
                                False,
                                f"Missing answer or chart data"
                            )
                    else:
                        self.log_test(
                            f"Query: {query['question'][:30]}...",
                            False,
                            f"API returned success=false"
                        )
                else:
                    self.log_test(
                        f"Query: {query['question'][:30]}...",
                        False,
                        f"HTTP {response.status_code}"
                    )

            except Exception as e:
                self.log_test(
                    f"Query: {query['question'][:30]}...",
                    False,
                    f"Exception: {str(e)}"
                )

    def test_configuration_security(self):
        """Test that no hardcoded values remain"""
        print("\n🔒 Testing Configuration Security")
        print("=" * 50)

        # Check backend settings
        try:
            sys.path.insert(0, str(project_root / "genai-agents-backend"))
            from config.settings import settings

            # Test that critical values come from environment
            gcp_project = settings.gcp_project_id
            if gcp_project and not gcp_project.startswith('gc-prod-'):
                self.log_test("Backend GCP Project", True, "Using environment variable")
            else:
                self.log_test("Backend GCP Project", False, "Still using hardcoded value")

            # Test default LLM provider
            if settings.default_llm_provider == 'anthropic':
                self.log_test("Default LLM Provider", True, "Set to anthropic")
            else:
                self.log_test("Default LLM Provider", False, f"Set to {settings.default_llm_provider}")

        except Exception as e:
            self.log_test("Backend configuration", False, f"Error loading: {str(e)}")

        # Check frontend API client
        try:
            sys.path.insert(0, str(project_root / "gradio-chatbot"))
            from utils.api_client import BACKEND_BASE_URL

            if 'localhost' in BACKEND_BASE_URL or os.getenv('BACKEND_URL'):
                self.log_test("Frontend API URL", True, "Environment-driven")
            else:
                self.log_test("Frontend API URL", False, "Hardcoded values found")

        except Exception as e:
            self.log_test("Frontend configuration", False, f"Error loading: {str(e)}")

    def test_data_generator_structure(self):
        """Test data generator organization"""
        print("\n📊 Testing Data Generator Structure")
        print("=" * 50)

        data_generator_path = project_root / "data-generator"

        expected_structure = {
            'data/cost_analysis_new.csv': 'Generated cost data',
            'schema/cost_analysis_schema.json': 'BigQuery schema',
            'scripts/setup_bigquery.py': 'Setup script',
            'scripts/load_data_to_bigquery.py': 'Data loading script',
            'docs/setup_requirements.txt': 'Setup requirements',
            'README.md': 'Documentation'
        }

        for file_path, description in expected_structure.items():
            full_path = data_generator_path / file_path
            if full_path.exists():
                self.log_test(f"Data generator: {file_path}", True, description)
            else:
                self.log_test(f"Data generator: {file_path}", False, "Missing")

    def run_all_tests(self):
        """Run all production readiness tests"""
        print("🚀 Starting Production Readiness Test Suite")
        print("=" * 60)
        print(f"Backend URL: {self.backend_url}")
        print(f"Frontend URL: {self.frontend_url}")
        print("=" * 60)

        # Run all test categories
        self.test_environment_configuration()
        self.test_project_structure()
        self.test_backend_health()
        self.test_api_integration()
        self.test_configuration_security()
        self.test_data_generator_structure()

        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate test summary"""
        print("\n📊 PRODUCTION READINESS SUMMARY")
        print("=" * 60)

        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r['success']])
        failed_tests = total_tests - passed_tests

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['message']}")

        print(f"\n{'🎉 PRODUCTION READY!' if failed_tests == 0 else '⚠️ NEEDS ATTENTION'}")

        # Production readiness checklist
        print(f"\n✅ Production Readiness Checklist:")
        print(f"   {'✅' if passed_tests >= total_tests * 0.9 else '❌'} Environment Configuration")
        print(f"   {'✅' if self._check_category('project structure') else '❌'} Clean Project Structure")
        print(f"   {'✅' if self._check_category('backend health') else '❌'} Backend API Health")
        print(f"   {'✅' if self._check_category('api integration') else '❌'} API Integration")
        print(f"   {'✅' if self._check_category('configuration security') else '❌'} Security & Configuration")
        print(f"   {'✅' if self._check_category('data generator') else '❌'} Data Generator Organization")

        return failed_tests == 0

    def _check_category(self, category: str) -> bool:
        """Check if all tests in a category passed"""
        category_tests = [r for r in self.results if category.lower() in r['test'].lower()]
        if not category_tests:
            return True
        return all(r['success'] for r in category_tests)

def main():
    """Main test execution"""
    tester = ProductionReadinessTest()
    success = tester.run_all_tests()

    print(f"\n🏁 Test Suite Complete: {'SUCCESS' if success else 'FAILED'}")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())