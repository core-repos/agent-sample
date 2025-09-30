#!/usr/bin/env python3
"""
Test all example queries via API
"""
import requests
import json
import time
from typing import Dict, List

API_URL = "http://localhost:8010/api/bigquery/ask"

def test_query(question: str, enable_validation: bool = False) -> Dict:
    """Test a single query and return results"""
    try:
        payload = {"question": question}
        if enable_validation:
            payload["enable_validation"] = True

        response = requests.post(
            API_URL,
            json=payload,
            timeout=60 if enable_validation else 30  # Extended timeout for validation
        )
        return {
            "success": response.status_code == 200,
            "data": response.json() if response.status_code == 200 else None,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": str(e)
        }

def main():
    """Test all example queries"""
    queries = [
        "What is the total cost?",
        "Show me the top 10 applications by cost",
        "What's the cost breakdown by environment?",
        "Display the daily cost trend for last 30 days",
        "Create a heatmap of costs by service",
        "Show waterfall chart of cost components",
        "Generate funnel chart for budget allocation"
    ]

    print("=" * 80)
    print("Testing BigQuery Analytics AI - All Example Queries")
    print("=" * 80)

    # Test both with and without validation
    for validation_enabled in [False, True]:
        validation_text = "WITH VALIDATION" if validation_enabled else "WITHOUT VALIDATION"
        print(f"\n🔬 TESTING {validation_text}")
        print("-" * 60)

        results = []
        for i, query in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}] Testing: {query}")
            result = test_query(query, enable_validation=validation_enabled)

            if result["success"]:
                data = result["data"]
                print(f"✅ SUCCESS")
                print(f"   Visualization: {data.get('visualization', 'none')}")

                # Show validation info if available
                if validation_enabled and 'validation_report' in data:
                    vr = data['validation_report']
                    print(f"   Validation: {vr.get('success', False)} | Iterations: {vr.get('total_iterations', 0)} | Time: {vr.get('execution_time', 0):.1f}s")

                if 'warnings' in data and data['warnings']:
                    print(f"   Warnings: {len(data['warnings'])}")

                if 'answer' in data:
                    answer_preview = data['answer'][:100] + "..." if len(data['answer']) > 100 else data['answer']
                    print(f"   Answer: {answer_preview}")
            else:
                print(f"❌ FAILED: {result['error']}")

            results.append(result)
            time.sleep(1)  # Rate limiting

        # Summary for this test type
        successful = sum(1 for r in results if r["success"])
        print(f"\n📊 {validation_text} SUMMARY:")
        print(f"   Passed: {successful}/{len(queries)}")
        print(f"   Failed: {len(queries) - successful}/{len(queries)}")
        print(f"   Success Rate: {(successful/len(queries))*100:.1f}%")

        if validation_enabled and results:
            # Additional validation stats
            total_iterations = 0
            validation_successes = 0
            for r in results:
                if r["success"] and r["data"].get("validation_report"):
                    vr = r["data"]["validation_report"]
                    total_iterations += vr.get("total_iterations", 0)
                    if vr.get("success"):
                        validation_successes += 1

            if validation_successes > 0:
                avg_iterations = total_iterations / validation_successes
                print(f"   Avg Validation Iterations: {avg_iterations:.1f}")
                print(f"   Validation Success Rate: {(validation_successes/len(queries))*100:.1f}%")

    print("\n" + "=" * 80)
    print("🎯 OVERALL TEST SUMMARY")
    print("=" * 80)
    print("Tests completed for both validation modes.")
    print("Use 'python tests/test_validation_agents.py' for detailed validation testing.")
    print("\n🎉 All query tests completed!")
    return 0

if __name__ == "__main__":
    exit(main())