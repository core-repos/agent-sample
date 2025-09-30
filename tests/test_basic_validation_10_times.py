#!/usr/bin/env python3
"""
Simple test to run basic validation 10 times with queries from examples
Tests reliability and consistency without complex validation iterations
"""
import requests
import json
import time
import statistics
from datetime import datetime
from typing import Dict, List, Any

API_URL = "http://localhost:8010/api/bigquery/ask"

# Simple test queries (examples from the queries folder concept)
SIMPLE_QUERIES = [
    "What is the total cost?",
    "Show me the top 5 applications by cost",
    "What's the cost breakdown by environment?",
    "Display the daily cost trend for last 30 days"
]

def test_query_with_validation(question: str, run_number: int) -> Dict[str, Any]:
    """Test a single query with validation enabled"""
    try:
        payload = {
            "question": question,
            "enable_validation": True,
            "use_cache": False  # Fresh test each time
        }

        start_time = time.time()
        response = requests.post(API_URL, json=payload, timeout=60)
        execution_time = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            return {
                "run": run_number,
                "success": True,
                "time": round(execution_time, 2),
                "has_answer": bool(data.get("answer")),
                "has_sql": bool(data.get("sql_query")),
                "has_visualization": bool(data.get("visualization")),
                "validation_success": data.get("validation_report", {}).get("success", False),
                "warnings": len(data.get("warnings", [])),
                "error": None
            }
        else:
            return {
                "run": run_number,
                "success": False,
                "time": execution_time,
                "error": f"HTTP {response.status_code}"
            }
    except Exception as e:
        return {
            "run": run_number,
            "success": False,
            "time": 0,
            "error": str(e)
        }

def run_query_10_times(question: str) -> Dict[str, Any]:
    """Run a single query 10 times and analyze results"""
    print(f"\n🔄 Testing 10 times: {question}")

    results = []
    for i in range(1, 11):
        print(f"  Run {i:2d}/10... ", end="", flush=True)

        result = test_query_with_validation(question, i)
        results.append(result)

        if result["success"]:
            print(f"✅ {result['time']}s")
        else:
            print(f"❌ {result['error']}")

        time.sleep(0.5)  # Brief pause between tests

    # Analyze results
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    success_rate = len(successful) / len(results)

    if successful:
        avg_time = statistics.mean([r["time"] for r in successful])
        min_time = min([r["time"] for r in successful])
        max_time = max([r["time"] for r in successful])

        # Check consistency
        has_answer_count = sum(1 for r in successful if r.get("has_answer", False))
        has_sql_count = sum(1 for r in successful if r.get("has_sql", False))
        has_viz_count = sum(1 for r in successful if r.get("has_visualization", False))
        validation_success_count = sum(1 for r in successful if r.get("validation_success", False))
    else:
        avg_time = min_time = max_time = 0
        has_answer_count = has_sql_count = has_viz_count = validation_success_count = 0

    return {
        "query": question,
        "success_rate": success_rate,
        "successful_runs": len(successful),
        "failed_runs": len(failed),
        "avg_time": round(avg_time, 2),
        "min_time": round(min_time, 2),
        "max_time": round(max_time, 2),
        "consistency": {
            "answer_rate": has_answer_count / len(successful) if successful else 0,
            "sql_rate": has_sql_count / len(successful) if successful else 0,
            "visualization_rate": has_viz_count / len(successful) if successful else 0,
            "validation_success_rate": validation_success_count / len(successful) if successful else 0
        },
        "errors": [r["error"] for r in failed if r["error"]]
    }

def main():
    """Run all tests"""
    print("=" * 80)
    print("🧪 VALIDATION SYSTEM - 10 TIMES RELIABILITY TEST")
    print("=" * 80)
    print(f"Testing {len(SIMPLE_QUERIES)} queries × 10 runs = {len(SIMPLE_QUERIES) * 10} total requests")

    start_time = datetime.now()
    all_results = []

    for i, query in enumerate(SIMPLE_QUERIES, 1):
        print(f"\n[{i}/{len(SIMPLE_QUERIES)}] Query: {query}")
        result = run_query_10_times(query)
        all_results.append(result)

    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()

    # Overall analysis
    print("\n" + "=" * 80)
    print("📊 RELIABILITY TEST RESULTS")
    print("=" * 80)

    total_requests = len(SIMPLE_QUERIES) * 10
    total_successful = sum(r["successful_runs"] for r in all_results)
    total_failed = sum(r["failed_runs"] for r in all_results)
    overall_success_rate = total_successful / total_requests

    print(f"🎯 Overall Success Rate: {overall_success_rate:.1%} ({total_successful}/{total_requests})")
    print(f"⏱️  Total Test Duration: {total_duration:.1f} seconds")
    print(f"📈 Average Requests/Second: {total_requests/total_duration:.2f}")

    # Performance stats
    all_avg_times = [r["avg_time"] for r in all_results if r["avg_time"] > 0]
    if all_avg_times:
        overall_avg_time = statistics.mean(all_avg_times)
        print(f"⚡ Average Response Time: {overall_avg_time:.2f} seconds")

    print(f"\n📋 Query-by-Query Results:")
    for result in all_results:
        query_short = result["query"][:50] + "..." if len(result["query"]) > 50 else result["query"]
        print(f"  {query_short}")
        print(f"    Success: {result['successful_runs']}/10 ({result['success_rate']:.0%}) | Avg Time: {result['avg_time']}s")

        consistency = result["consistency"]
        print(f"    Consistency: Answer={consistency['answer_rate']:.0%} SQL={consistency['sql_rate']:.0%} Viz={consistency['visualization_rate']:.0%} Validation={consistency['validation_success_rate']:.0%}")

        if result["errors"]:
            unique_errors = list(set(result["errors"]))
            print(f"    Errors: {', '.join(unique_errors[:2])}")

    # Reliability score
    reliability_score = overall_success_rate * 100

    print(f"\n🏆 RELIABILITY SCORE: {reliability_score:.1f}/100")

    if reliability_score >= 90:
        print("🎉 EXCELLENT - Validation system is highly reliable!")
        status = "excellent"
    elif reliability_score >= 75:
        print("✅ GOOD - Validation system is reliable")
        status = "good"
    elif reliability_score >= 50:
        print("⚠️  FAIR - Validation system has some issues")
        status = "fair"
    else:
        print("❌ POOR - Validation system needs significant improvement")
        status = "poor"

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = {
        "timestamp": timestamp,
        "test_summary": {
            "total_requests": total_requests,
            "total_successful": total_successful,
            "total_failed": total_failed,
            "success_rate": overall_success_rate,
            "reliability_score": reliability_score,
            "status": status,
            "duration_seconds": total_duration
        },
        "query_results": all_results
    }

    try:
        filename = f"validation_10x_test_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n💾 Detailed results saved to: {filename}")
    except Exception as e:
        print(f"\n⚠️  Could not save results: {e}")

    # Return appropriate exit code
    if reliability_score >= 75:
        return 0
    else:
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)