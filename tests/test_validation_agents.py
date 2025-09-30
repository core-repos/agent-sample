#!/usr/bin/env python3
"""
Test validation agents with example queries from the queries/ folder
"""
import asyncio
import requests
import json
import time
from typing import Dict, List
from datetime import datetime

API_URL = "http://localhost:8010/api/bigquery/ask"
HEALTH_URL = "http://localhost:8010/api/bigquery/validation/health"
EXAMPLES_URL = "http://localhost:8010/api/bigquery/validation/examples"

async def test_validation_health():
    """Test validation system health"""
    print("🔍 Testing Validation System Health")
    print("-" * 50)

    try:
        response = requests.get(HEALTH_URL, timeout=10)
        health = response.json()

        print(f"Overall Status: {health.get('overall', 'unknown')}")
        print(f"SQL Validator: {health.get('sql_validator', 'unknown')}")
        print(f"Graph Validator: {health.get('graph_validator', 'unknown')}")
        print(f"Database Connection: {health.get('database_connection', 'unknown')}")

        return health.get('overall') == 'healthy'
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_query_with_validation(question: str, enable_validation: bool = True, visualization_hint: str = None) -> Dict:
    """Test a single query with validation enabled"""
    try:
        payload = {
            "question": question,
            "enable_validation": enable_validation,
            "use_cache": False  # Disable cache for testing
        }

        if visualization_hint:
            payload["visualization_hint"] = visualization_hint

        start_time = time.time()
        response = requests.post(API_URL, json=payload, timeout=120)  # Extended timeout for validation
        execution_time = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "data": data,
                "execution_time": execution_time,
                "status_code": response.status_code
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "execution_time": execution_time,
                "status_code": response.status_code
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "execution_time": 0,
            "status_code": None
        }

def compare_validation_results(question: str, visualization_hint: str = None):
    """Compare results with and without validation"""
    print(f"🔄 Comparing: {question}")
    print("   Visualization hint:", visualization_hint or "None")

    # Test without validation
    print("   Testing without validation...")
    result_no_validation = test_query_with_validation(question, enable_validation=False, visualization_hint=visualization_hint)

    # Test with validation
    print("   Testing with validation...")
    result_with_validation = test_query_with_validation(question, enable_validation=True, visualization_hint=visualization_hint)

    # Compare results
    comparison = {
        "question": question,
        "visualization_hint": visualization_hint,
        "without_validation": {
            "success": result_no_validation["success"],
            "execution_time": result_no_validation["execution_time"],
            "has_visualization": "visualization" in result_no_validation.get("data", {}),
            "has_chart_data": "chart_data" in result_no_validation.get("data", {}),
            "error": result_no_validation.get("error")
        },
        "with_validation": {
            "success": result_with_validation["success"],
            "execution_time": result_with_validation["execution_time"],
            "has_visualization": "visualization" in result_with_validation.get("data", {}),
            "has_chart_data": "chart_data" in result_with_validation.get("data", {}),
            "validation_report": result_with_validation.get("data", {}).get("validation_report"),
            "warnings": result_with_validation.get("data", {}).get("warnings"),
            "error": result_with_validation.get("error")
        }
    }

    # Print summary
    print(f"   ✅ Without validation: {result_no_validation['success']} ({result_no_validation['execution_time']:.1f}s)")
    print(f"   🔍 With validation: {result_with_validation['success']} ({result_with_validation['execution_time']:.1f}s)")

    if result_with_validation["success"] and result_with_validation["data"].get("validation_report"):
        vr = result_with_validation["data"]["validation_report"]
        print(f"   📊 Validation: {vr.get('success', False)} | Iterations: {vr.get('total_iterations', 0)} | SQL: {vr.get('sql_iterations', 0)} | Graph: {vr.get('graph_iterations', 0)}")

    if result_with_validation.get("data", {}).get("warnings"):
        print(f"   ⚠️  Warnings: {len(result_with_validation['data']['warnings'])}")

    print()
    return comparison

async def main():
    """Main test function"""
    print("=" * 80)
    print("🧪 VALIDATION AGENTS TEST SUITE")
    print("=" * 80)
    print()

    # Health check first
    health_ok = await test_validation_health()
    print()

    if not health_ok:
        print("❌ Health check failed. Please ensure the backend is running and validation is enabled.")
        return 1

    # Get validation examples
    try:
        response = requests.get(EXAMPLES_URL, timeout=10)
        if response.status_code == 200:
            examples = response.json().get("validation_examples", [])
            print(f"📋 Found {len(examples)} validation examples")
        else:
            examples = []
            print("⚠️  Could not fetch validation examples, using defaults")
    except:
        examples = []
        print("⚠️  Could not fetch validation examples, using defaults")

    # Default test queries if no examples found
    if not examples:
        examples = [
            {
                "question": "What is the total cost?",
                "expected_visualization": "indicator",
                "category": "aggregation"
            },
            {
                "question": "Show me the top 5 applications by cost",
                "expected_visualization": "bar",
                "category": "ranking"
            },
            {
                "question": "What's the cost breakdown by environment?",
                "expected_visualization": "pie",
                "category": "distribution"
            },
            {
                "question": "Display the daily cost trend for last 30 days",
                "expected_visualization": "line",
                "category": "trend"
            },
            {
                "question": "Show cost correlation between applications",
                "expected_visualization": "scatter",
                "category": "correlation"
            }
        ]

    print()
    print("🔬 RUNNING VALIDATION TESTS")
    print("=" * 80)

    results = []
    successful_tests = 0
    total_tests = len(examples)

    for i, example in enumerate(examples, 1):
        print(f"[{i}/{total_tests}] Testing: {example['question']}")

        question = example["question"]
        expected_viz = example.get("expected_visualization")

        result = compare_validation_results(question, expected_viz)
        results.append(result)

        # Count successful validation
        if result["with_validation"]["success"]:
            successful_tests += 1

        # Add delay between tests
        time.sleep(2)

    print("=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)

    print(f"Tests Passed with Validation: {successful_tests}/{total_tests}")
    print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    print()

    # Detailed analysis
    validation_improvements = 0
    validation_issues = 0
    iteration_stats = []

    for result in results:
        without_val = result["without_validation"]
        with_val = result["with_validation"]

        # Check if validation improved results
        if with_val["success"] and not without_val["success"]:
            validation_improvements += 1
        elif not with_val["success"] and without_val["success"]:
            validation_issues += 1

        # Collect iteration stats
        if with_val.get("validation_report"):
            vr = with_val["validation_report"]
            iteration_stats.append({
                "total": vr.get("total_iterations", 0),
                "sql": vr.get("sql_iterations", 0),
                "graph": vr.get("graph_iterations", 0)
            })

    print(f"Validation Improvements: {validation_improvements}")
    print(f"Validation Issues: {validation_issues}")

    if iteration_stats:
        avg_total = sum(s["total"] for s in iteration_stats) / len(iteration_stats)
        avg_sql = sum(s["sql"] for s in iteration_stats) / len(iteration_stats)
        avg_graph = sum(s["graph"] for s in iteration_stats) / len(iteration_stats)

        print(f"Average Iterations - Total: {avg_total:.1f} | SQL: {avg_sql:.1f} | Graph: {avg_graph:.1f}")

    print()
    print("📋 DETAILED RESULTS")
    print("-" * 50)

    for result in results:
        print(f"Query: {result['question'][:60]}...")
        print(f"  Expected: {result.get('visualization_hint', 'auto')}")

        with_val = result["with_validation"]
        if with_val["success"] and with_val.get("validation_report"):
            vr = with_val["validation_report"]
            print(f"  Validation: ✅ {vr.get('total_iterations', 0)} iterations ({vr.get('execution_time', 0):.1f}s)")
        elif with_val["success"]:
            print(f"  Validation: ✅ No validation report")
        else:
            print(f"  Validation: ❌ {with_val.get('error', 'Unknown error')}")

        if with_val.get("warnings"):
            print(f"  Warnings: {len(with_val['warnings'])}")

        print()

    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"validation_test_results_{timestamp}.json"

    try:
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "summary": {
                    "total_tests": total_tests,
                    "successful_tests": successful_tests,
                    "success_rate": (successful_tests/total_tests)*100,
                    "validation_improvements": validation_improvements,
                    "validation_issues": validation_issues,
                    "average_iterations": {
                        "total": avg_total if iteration_stats else 0,
                        "sql": avg_sql if iteration_stats else 0,
                        "graph": avg_graph if iteration_stats else 0
                    } if iteration_stats else None
                },
                "detailed_results": results
            }, indent=2)
        print(f"💾 Detailed results saved to: {results_file}")
    except Exception as e:
        print(f"⚠️  Could not save results: {e}")

    if successful_tests == total_tests:
        print("\n🎉 All validation tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total_tests - successful_tests} test(s) failed")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        exit(1)