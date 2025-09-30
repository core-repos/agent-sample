#!/usr/bin/env python3
"""
Test validation agents 10 times for each query to ensure reliability and consistency
"""
import asyncio
import requests
import json
import time
import statistics
from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict

API_URL = "http://localhost:8010/api/bigquery/ask"
HEALTH_URL = "http://localhost:8010/api/bigquery/validation/health"

# Test queries from the queries folder examples
TEST_QUERIES = [
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
    },
    {
        "question": "Create a heatmap of costs by service",
        "expected_visualization": "heatmap",
        "category": "matrix"
    },
    {
        "question": "Generate funnel chart for budget allocation",
        "expected_visualization": "funnel",
        "category": "pipeline"
    }
]

class ValidationTestRunner:
    """Test runner for validation system reliability testing"""

    def __init__(self, num_runs: int = 10):
        self.num_runs = num_runs
        self.results = {}
        self.consistency_metrics = {}

    def test_single_query(self, question: str, visualization_hint: str = None, run_number: int = 1) -> Dict[str, Any]:
        """Test a single query with validation enabled"""
        try:
            payload = {
                "question": question,
                "enable_validation": True,
                "use_cache": False,  # Disable cache to test fresh each time
                "visualization_hint": visualization_hint
            }

            start_time = time.time()
            response = requests.post(API_URL, json=payload, timeout=120)
            execution_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                return {
                    "run_number": run_number,
                    "success": True,
                    "execution_time": execution_time,
                    "data": data,
                    "validation_report": data.get("validation_report", {}),
                    "has_visualization": "visualization" in data,
                    "has_chart_data": "chart_data" in data,
                    "warnings_count": len(data.get("warnings", [])),
                    "sql_query": data.get("sql_query", ""),
                    "visualization_type": data.get("visualization"),
                    "error": None
                }
            else:
                return {
                    "run_number": run_number,
                    "success": False,
                    "execution_time": execution_time,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "data": None
                }
        except Exception as e:
            return {
                "run_number": run_number,
                "success": False,
                "execution_time": 0,
                "error": str(e),
                "data": None
            }

    def run_query_10_times(self, query_info: Dict[str, str]) -> Dict[str, Any]:
        """Run a single query 10 times and collect results"""
        question = query_info["question"]
        expected_viz = query_info.get("expected_visualization")
        category = query_info["category"]

        print(f"\n🔄 Testing 10 times: {question}")
        print(f"   Expected: {expected_viz} | Category: {category}")

        runs = []
        for i in range(1, self.num_runs + 1):
            print(f"   Run {i}/10...", end="", flush=True)

            result = self.test_single_query(question, expected_viz, i)
            runs.append(result)

            if result["success"]:
                print(" ✅")
            else:
                print(f" ❌ {result['error'][:50]}...")

            # Small delay between runs
            time.sleep(1)

        return {
            "query": question,
            "expected_visualization": expected_viz,
            "category": category,
            "runs": runs,
            "summary": self.analyze_query_results(runs)
        }

    def analyze_query_results(self, runs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze results from 10 runs of a single query"""
        successful_runs = [r for r in runs if r["success"]]
        failed_runs = [r for r in runs if not r["success"]]

        success_rate = len(successful_runs) / len(runs)

        # Execution time statistics
        exec_times = [r["execution_time"] for r in successful_runs]
        avg_exec_time = statistics.mean(exec_times) if exec_times else 0
        min_exec_time = min(exec_times) if exec_times else 0
        max_exec_time = max(exec_times) if exec_times else 0

        # Validation statistics
        validation_successes = [r for r in successful_runs if r.get("validation_report", {}).get("success")]
        validation_success_rate = len(validation_successes) / len(successful_runs) if successful_runs else 0

        # Iteration statistics
        total_iterations = []
        sql_iterations = []
        graph_iterations = []

        for run in successful_runs:
            vr = run.get("validation_report", {})
            if vr:
                total_iterations.append(vr.get("total_iterations", 0))
                sql_iterations.append(vr.get("sql_iterations", 0))
                graph_iterations.append(vr.get("graph_iterations", 0))

        # Consistency checks
        sql_queries = [r["sql_query"] for r in successful_runs if r.get("sql_query")]
        visualization_types = [r["visualization_type"] for r in successful_runs if r.get("visualization_type")]

        sql_consistency = len(set(sql_queries)) == 1 if sql_queries else False
        viz_consistency = len(set(visualization_types)) == 1 if visualization_types else False

        return {
            "success_rate": success_rate,
            "successful_runs": len(successful_runs),
            "failed_runs": len(failed_runs),
            "execution_time": {
                "avg": avg_exec_time,
                "min": min_exec_time,
                "max": max_exec_time,
                "std_dev": statistics.stdev(exec_times) if len(exec_times) > 1 else 0
            },
            "validation": {
                "success_rate": validation_success_rate,
                "avg_total_iterations": statistics.mean(total_iterations) if total_iterations else 0,
                "avg_sql_iterations": statistics.mean(sql_iterations) if sql_iterations else 0,
                "avg_graph_iterations": statistics.mean(graph_iterations) if graph_iterations else 0
            },
            "consistency": {
                "sql_query_consistent": sql_consistency,
                "visualization_type_consistent": viz_consistency,
                "unique_sql_queries": len(set(sql_queries)),
                "unique_visualization_types": len(set(visualization_types))
            },
            "errors": [r["error"] for r in failed_runs if r["error"]]
        }

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test queries 10 times each"""
        print("=" * 80)
        print("🧪 VALIDATION RELIABILITY TEST - 10 RUNS PER QUERY")
        print("=" * 80)

        # Health check first
        print("🔍 Checking validation system health...")
        try:
            response = requests.get(HEALTH_URL, timeout=10)
            if response.status_code == 200:
                health = response.json()
                print(f"   Overall: {health.get('overall', 'unknown')}")
                if health.get('overall') != 'healthy':
                    print("⚠️  Warning: Validation system may not be healthy")
            else:
                print(f"⚠️  Health check failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"⚠️  Health check error: {e}")

        print(f"\n📋 Testing {len(TEST_QUERIES)} queries × {self.num_runs} runs = {len(TEST_QUERIES) * self.num_runs} total requests")
        print()

        all_results = []
        start_time = datetime.now()

        for i, query_info in enumerate(TEST_QUERIES, 1):
            print(f"[{i}/{len(TEST_QUERIES)}] Query Category: {query_info['category']}")
            result = self.run_query_10_times(query_info)
            all_results.append(result)

        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()

        # Generate overall analysis
        overall_analysis = self.generate_overall_analysis(all_results, total_duration)

        return {
            "timestamp": start_time.isoformat(),
            "total_duration_seconds": total_duration,
            "test_configuration": {
                "num_queries": len(TEST_QUERIES),
                "runs_per_query": self.num_runs,
                "total_requests": len(TEST_QUERIES) * self.num_runs
            },
            "query_results": all_results,
            "overall_analysis": overall_analysis
        }

    def generate_overall_analysis(self, all_results: List[Dict[str, Any]], total_duration: float) -> Dict[str, Any]:
        """Generate overall analysis across all tests"""

        # Aggregate statistics
        total_requests = len(all_results) * self.num_runs
        total_successful = sum(r["summary"]["successful_runs"] for r in all_results)
        total_failed = sum(r["summary"]["failed_runs"] for r in all_results)
        overall_success_rate = total_successful / total_requests

        # Execution time statistics
        all_exec_times = []
        for result in all_results:
            for run in result["runs"]:
                if run["success"]:
                    all_exec_times.append(run["execution_time"])

        avg_exec_time = statistics.mean(all_exec_times) if all_exec_times else 0

        # Validation statistics
        validation_data = []
        for result in all_results:
            for run in result["runs"]:
                if run["success"] and run.get("validation_report"):
                    validation_data.append(run["validation_report"])

        avg_validation_time = statistics.mean([v.get("execution_time", 0) for v in validation_data]) if validation_data else 0
        avg_total_iterations = statistics.mean([v.get("total_iterations", 0) for v in validation_data]) if validation_data else 0

        # Consistency analysis
        consistency_by_query = {}
        for result in all_results:
            query = result["query"]
            consistency_by_query[query] = result["summary"]["consistency"]

        # Error analysis
        all_errors = []
        for result in all_results:
            all_errors.extend(result["summary"]["errors"])

        error_frequency = defaultdict(int)
        for error in all_errors:
            # Group similar errors
            if "timeout" in error.lower():
                error_frequency["Timeout"] += 1
            elif "connection" in error.lower():
                error_frequency["Connection"] += 1
            elif "http 5" in error.lower():
                error_frequency["Server Error"] += 1
            else:
                error_frequency["Other"] += 1

        return {
            "overall_success_rate": overall_success_rate,
            "total_successful_requests": total_successful,
            "total_failed_requests": total_failed,
            "performance": {
                "avg_execution_time": avg_exec_time,
                "avg_validation_time": avg_validation_time,
                "total_test_duration": total_duration,
                "requests_per_second": total_requests / total_duration if total_duration > 0 else 0
            },
            "validation_stats": {
                "avg_total_iterations": avg_total_iterations,
                "validation_success_rate": len([v for v in validation_data if v.get("success")]) / len(validation_data) if validation_data else 0
            },
            "consistency": {
                "queries_with_consistent_sql": sum(1 for c in consistency_by_query.values() if c["sql_query_consistent"]),
                "queries_with_consistent_viz": sum(1 for c in consistency_by_query.values() if c["visualization_type_consistent"])
            },
            "error_analysis": dict(error_frequency),
            "reliability_score": self.calculate_reliability_score(overall_success_rate, consistency_by_query)
        }

    def calculate_reliability_score(self, success_rate: float, consistency_by_query: Dict) -> float:
        """Calculate overall reliability score (0-100)"""
        # Base score from success rate (70% weight)
        success_score = success_rate * 70

        # Consistency score (30% weight)
        sql_consistent = sum(1 for c in consistency_by_query.values() if c["sql_query_consistent"])
        viz_consistent = sum(1 for c in consistency_by_query.values() if c["visualization_type_consistent"])
        total_queries = len(consistency_by_query)

        if total_queries > 0:
            consistency_score = ((sql_consistent + viz_consistent) / (total_queries * 2)) * 30
        else:
            consistency_score = 0

        return round(success_score + consistency_score, 1)

    def print_summary(self, results: Dict[str, Any]):
        """Print test summary"""
        analysis = results["overall_analysis"]

        print("\n" + "=" * 80)
        print("📊 VALIDATION RELIABILITY REPORT")
        print("=" * 80)

        print(f"🎯 Overall Success Rate: {analysis['overall_success_rate']:.1%}")
        print(f"✅ Successful Requests: {analysis['total_successful_requests']}")
        print(f"❌ Failed Requests: {analysis['total_failed_requests']}")
        print(f"🏆 Reliability Score: {analysis['reliability_score']}/100")

        print(f"\n⚡ Performance:")
        perf = analysis["performance"]
        print(f"   Average Execution Time: {perf['avg_execution_time']:.2f}s")
        print(f"   Average Validation Time: {perf['avg_validation_time']:.2f}s")
        print(f"   Total Test Duration: {perf['total_test_duration']:.1f}s")
        print(f"   Requests Per Second: {perf['requests_per_second']:.2f}")

        print(f"\n🔍 Validation Statistics:")
        val_stats = analysis["validation_stats"]
        print(f"   Average Iterations: {val_stats['avg_total_iterations']:.1f}")
        print(f"   Validation Success Rate: {val_stats['validation_success_rate']:.1%}")

        print(f"\n🔄 Consistency:")
        consistency = analysis["consistency"]
        print(f"   Queries with Consistent SQL: {consistency['queries_with_consistent_sql']}/{len(TEST_QUERIES)}")
        print(f"   Queries with Consistent Visualization: {consistency['queries_with_consistent_viz']}/{len(TEST_QUERIES)}")

        if analysis["error_analysis"]:
            print(f"\n❌ Error Breakdown:")
            for error_type, count in analysis["error_analysis"].items():
                print(f"   {error_type}: {count}")

        print(f"\n📋 Query-by-Query Results:")
        for result in results["query_results"]:
            summary = result["summary"]
            query_short = result["query"][:60] + "..." if len(result["query"]) > 60 else result["query"]
            print(f"   {query_short}")
            print(f"      Success: {summary['successful_runs']}/10 | Consistency: SQL={summary['consistency']['sql_query_consistent']} VIZ={summary['consistency']['visualization_type_consistent']}")

async def main():
    """Main test function"""
    runner = ValidationTestRunner(num_runs=10)

    print("Starting validation reliability test...")
    print("This will test each query 10 times to ensure consistent behavior.")
    print()

    # Run all tests
    results = runner.run_all_tests()

    # Print summary
    runner.print_summary(results)

    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"validation_reliability_test_{timestamp}.json"

    try:
        with open(results_file, 'w') as f:
            json.dump(results, indent=2, fp=f)
        print(f"\n💾 Detailed results saved to: {results_file}")
    except Exception as e:
        print(f"\n⚠️  Could not save results: {e}")

    # Return appropriate exit code
    reliability_score = results["overall_analysis"]["reliability_score"]
    if reliability_score >= 90:
        print(f"\n🎉 Excellent reliability! Score: {reliability_score}/100")
        return 0
    elif reliability_score >= 75:
        print(f"\n✅ Good reliability. Score: {reliability_score}/100")
        return 0
    else:
        print(f"\n⚠️  Reliability needs improvement. Score: {reliability_score}/100")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        exit(1)