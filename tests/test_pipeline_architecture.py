#!/usr/bin/env python3
"""
Test the new pipeline architecture
"""
import requests
import json
import time
from typing import Dict, List
from datetime import datetime

# API URLs
PIPELINE_URL = "http://localhost:8010/api/pipeline/execute"
PIPELINE_HEALTH_URL = "http://localhost:8010/api/pipeline/health"
PIPELINE_TYPES_URL = "http://localhost:8010/api/pipeline/types"
LEGACY_URL = "http://localhost:8010/api/bigquery/ask"

# Test queries
TEST_QUERIES = [
    {
        "question": "What is the total cost?",
        "expected_visualization": "indicator",
        "pipeline_type": "standard"
    },
    {
        "question": "Show me the top 5 applications by cost",
        "expected_visualization": "bar",
        "pipeline_type": "standard"
    },
    {
        "question": "What's the cost breakdown by environment?",
        "expected_visualization": "pie",
        "pipeline_type": "simple"
    },
    {
        "question": "Display the daily cost trend for last 30 days",
        "expected_visualization": "line",
        "pipeline_type": "validation_heavy"
    }
]

def test_pipeline_health():
    """Test pipeline system health"""
    print("🔍 Testing Pipeline Health")
    print("-" * 50)

    try:
        response = requests.get(PIPELINE_HEALTH_URL, timeout=10)
        if response.status_code == 200:
            health = response.json()
            print(f"Pipeline System: {health.get('pipeline_system', 'unknown')}")
            print(f"Available Types: {health.get('available_types', [])}")

            # Check standard pipeline health
            std_health = health.get('standard_pipeline', {})
            print(f"Standard Pipeline: {std_health.get('pipeline_status', 'unknown')}")

            return health.get('pipeline_system') == 'healthy'
        else:
            print(f"❌ Health check failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_pipeline_types():
    """Test available pipeline types"""
    print("\n📋 Testing Pipeline Types")
    print("-" * 50)

    try:
        response = requests.get(PIPELINE_TYPES_URL, timeout=10)
        if response.status_code == 200:
            types_data = response.json()
            pipelines = types_data.get('available_pipelines', {})

            print(f"Available Pipeline Types: {len(pipelines)}")
            for name, info in pipelines.items():
                print(f"  {name}: {info.get('description', 'No description')}")

            return len(pipelines) > 0
        else:
            print(f"❌ Failed to get pipeline types: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Pipeline types error: {e}")
        return False

def test_pipeline_query(query_info: Dict) -> Dict:
    """Test a single query with pipeline"""
    question = query_info["question"]
    pipeline_type = query_info["pipeline_type"]
    expected_viz = query_info.get("expected_visualization")

    print(f"\n🔄 Testing Pipeline Query: {question}")
    print(f"   Pipeline Type: {pipeline_type}")
    print(f"   Expected Visualization: {expected_viz}")

    try:
        payload = {
            "question": question,
            "pipeline_type": pipeline_type,
            "enable_validation": True,
            "use_cache": False,
            "visualization_hint": expected_viz
        }

        start_time = time.time()
        response = requests.post(PIPELINE_URL, json=payload, timeout=120)
        execution_time = time.time() - start_time

        if response.status_code == 200:
            data = response.json()

            print(f"   ✅ SUCCESS ({execution_time:.2f}s)")

            # Show pipeline metadata
            pipeline_meta = data.get("pipeline_metadata", {})
            print(f"   Pipeline Steps: {pipeline_meta.get('total_steps', 'unknown')}")

            # Show step results
            step_results = pipeline_meta.get('step_results', [])
            for step in step_results:
                status_emoji = "✅" if step['status'] == 'success' else "⚠️" if step['status'] == 'skipped' else "❌"
                print(f"     {status_emoji} {step['step']}: {step['status']} ({step['execution_time']:.2f}s)")

            # Show final result info
            final_data = data.get("data", {})
            if "final_response" in final_data:
                final_response = final_data["final_response"]
                print(f"   Has SQL: {bool(final_response.get('sql_query'))}")
                print(f"   Has Visualization: {bool(final_response.get('visualization'))}")
                print(f"   Has Chart Data: {bool(final_response.get('chart_data'))}")

            return {
                "success": True,
                "execution_time": execution_time,
                "data": data
            }
        else:
            print(f"   ❌ FAILED: HTTP {response.status_code}")
            print(f"   Error: {response.text}")
            return {
                "success": False,
                "execution_time": execution_time,
                "error": f"HTTP {response.status_code}: {response.text}"
            }

    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        return {
            "success": False,
            "execution_time": 0,
            "error": str(e)
        }

def test_legacy_vs_pipeline(question: str):
    """Compare legacy API vs pipeline API"""
    print(f"\n🔄 Comparing Legacy vs Pipeline: {question}")
    print("-" * 60)

    # Test legacy API
    print("   Testing Legacy API...")
    try:
        legacy_payload = {
            "question": question,
            "enable_validation": True,
            "use_cache": False
        }
        start_time = time.time()
        legacy_response = requests.post(LEGACY_URL, json=legacy_payload, timeout=60)
        legacy_time = time.time() - start_time

        if legacy_response.status_code == 200:
            print(f"     ✅ Legacy Success ({legacy_time:.2f}s)")
            legacy_success = True
        else:
            print(f"     ❌ Legacy Failed: HTTP {legacy_response.status_code}")
            legacy_success = False
    except Exception as e:
        print(f"     ❌ Legacy Exception: {e}")
        legacy_success = False

    # Test pipeline API
    print("   Testing Pipeline API...")
    try:
        pipeline_payload = {
            "question": question,
            "pipeline_type": "standard",
            "enable_validation": True,
            "use_cache": False
        }
        start_time = time.time()
        pipeline_response = requests.post(PIPELINE_URL, json=pipeline_payload, timeout=60)
        pipeline_time = time.time() - start_time

        if pipeline_response.status_code == 200:
            print(f"     ✅ Pipeline Success ({pipeline_time:.2f}s)")
            pipeline_success = True
        else:
            print(f"     ❌ Pipeline Failed: HTTP {pipeline_response.status_code}")
            pipeline_success = False
    except Exception as e:
        print(f"     ❌ Pipeline Exception: {e}")
        pipeline_success = False

    # Compare results
    if legacy_success and pipeline_success:
        time_diff = abs(legacy_time - pipeline_time)
        faster = "Legacy" if legacy_time < pipeline_time else "Pipeline"
        print(f"   📊 Both succeeded - {faster} was {time_diff:.2f}s faster")
    elif pipeline_success:
        print(f"   🎯 Pipeline succeeded, Legacy failed")
    elif legacy_success:
        print(f"   ⚠️  Legacy succeeded, Pipeline failed")
    else:
        print(f"   ❌ Both failed")

def main():
    """Main test function"""
    print("=" * 80)
    print("🧪 PIPELINE ARCHITECTURE TEST SUITE")
    print("=" * 80)

    # Health check
    health_ok = test_pipeline_health()
    if not health_ok:
        print("\n❌ Pipeline health check failed. Please ensure the backend is running.")
        return 1

    # Test pipeline types
    types_ok = test_pipeline_types()
    if not types_ok:
        print("\n❌ Pipeline types test failed.")
        return 1

    print("\n" + "=" * 80)
    print("🚀 TESTING PIPELINE QUERIES")
    print("=" * 80)

    # Test each query with different pipeline types
    results = []
    for query_info in TEST_QUERIES:
        result = test_pipeline_query(query_info)
        results.append(result)
        time.sleep(1)  # Brief pause between tests

    print("\n" + "=" * 80)
    print("🔄 LEGACY vs PIPELINE COMPARISON")
    print("=" * 80)

    # Compare legacy vs pipeline for a few queries
    comparison_queries = [
        "What is the total cost?",
        "Show me the top 5 applications by cost"
    ]

    for question in comparison_queries:
        test_legacy_vs_pipeline(question)
        time.sleep(1)

    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)

    successful_tests = sum(1 for r in results if r["success"])
    total_tests = len(results)

    print(f"Pipeline Tests Passed: {successful_tests}/{total_tests}")
    print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")

    if successful_tests == total_tests:
        print("\n🎉 All pipeline tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total_tests - successful_tests} test(s) failed")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        exit(1)