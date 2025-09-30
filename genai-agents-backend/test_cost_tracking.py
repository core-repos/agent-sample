#!/usr/bin/env python3
"""
Test script for Cost Tracking API functionality
"""
import requests
import json
import sys
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8010"
COST_TRACKING_BASE = f"{BASE_URL}/api/cost-tracking"

def test_endpoint(url, method="GET", data=None, description=""):
    """Test an API endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"URL: {url}")
    print(f"Method: {method}")

    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
        else:
            print(f"Unsupported method: {method}")
            return False

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            if isinstance(result, dict) and len(result) > 0:
                print("Response preview:")
                for key, value in list(result.items())[:3]:  # Show first 3 keys
                    if isinstance(value, (list, dict)):
                        print(f"  {key}: {type(value).__name__} with {len(value)} items")
                    else:
                        print(f"  {key}: {value}")
            return True
        else:
            print(f"❌ Failed! Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Connection Error - Server not running on port 8010")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚀 Cost Tracking API Test Suite")
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")

    # Test basic server health
    if not test_endpoint(f"{BASE_URL}/health", description="Basic Health Check"):
        print("❌ Server is not responding. Exiting.")
        sys.exit(1)

    # Test cost tracking endpoints
    tests = [
        # Dashboard Summary (GET)
        {
            "url": f"{COST_TRACKING_BASE}/dashboard-summary",
            "method": "GET",
            "description": "Dashboard Summary"
        },

        # Optimization Recommendations (GET)
        {
            "url": f"{COST_TRACKING_BASE}/optimization-recommendations",
            "method": "GET",
            "description": "Cost Optimization Recommendations"
        },

        # Anomaly Detection (POST)
        {
            "url": f"{COST_TRACKING_BASE}/anomaly-detection",
            "method": "POST",
            "data": {
                "days_back": 30,
                "sensitivity": 2.0,
                "group_by": "cloud"
            },
            "description": "Cost Anomaly Detection"
        },

        # Threshold Monitoring - Budget (POST)
        {
            "url": f"{COST_TRACKING_BASE}/threshold-monitoring",
            "method": "POST",
            "data": {
                "threshold_type": "budget",
                "threshold_value": 1000000.0,
                "scope": "cto"
            },
            "description": "Budget Threshold Monitoring"
        },

        # Threshold Monitoring - Daily Limit (POST)
        {
            "url": f"{COST_TRACKING_BASE}/threshold-monitoring",
            "method": "POST",
            "data": {
                "threshold_type": "daily_limit",
                "threshold_value": 10000.0,
                "scope": "cloud"
            },
            "description": "Daily Limit Threshold Monitoring"
        },

        # Cost Forecast (POST)
        {
            "url": f"{COST_TRACKING_BASE}/forecast",
            "method": "POST",
            "data": {
                "forecast_days": 30,
                "group_by": "cloud",
                "include_confidence_interval": True
            },
            "description": "Cost Forecasting"
        }
    ]

    # Run all tests
    passed = 0
    total = len(tests)

    for test in tests:
        success = test_endpoint(
            test["url"],
            test["method"],
            test.get("data"),
            test["description"]
        )
        if success:
            passed += 1

    # Summary
    print(f"\n{'='*60}")
    print(f"📊 Test Results Summary")
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())