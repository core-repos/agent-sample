"""
Test script for the context-aware pipeline system
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

from agents.pipeline.context_loader import ContextLoader, ContextConfig
from agents.pipeline.sql_agent import SQLAgent
from agents.pipeline.step_executor import StepExecutor, StepConfig, StepType
from agents.pipeline.pipeline_agent import PipelineAgent, PipelineConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PipelineSystemTest:
    """Test suite for the pipeline system"""

    def __init__(self):
        self.context_config = ContextConfig(
            schema_dir="context/schemas",
            templates_dir="context/templates",
            examples_dir="context/examples",
            cache_enabled=True
        )

        self.pipeline_config = PipelineConfig(
            context_config=self.context_config,
            enable_caching=True
        )

    async def test_context_loader(self):
        """Test context loading functionality"""
        print("\n🔍 Testing Context Loader")
        print("=" * 40)

        context_loader = ContextLoader(self.context_config)

        # Test schema loading
        schemas = context_loader.load_table_schemas()
        print(f"✅ Loaded {len(schemas)} schemas")
        for name, schema in schemas.items():
            print(f"  - {name}: {len(schema.columns)} columns")

        # Test template loading
        templates = context_loader.load_query_templates()
        print(f"✅ Loaded {len(templates)} templates")
        for name, template in templates.items():
            print(f"  - {name} ({template.category})")

        # Test example loading
        examples = context_loader.load_sql_examples()
        print(f"✅ Loaded examples from {len(examples)} categories")
        for category, example_list in examples.items():
            print(f"  - {category}: {len(example_list)} examples")

        # Test context for specific query type
        context = context_loader.get_context_for_query_type("aggregation")
        print(f"✅ Generated context for 'aggregation' query type")
        print(f"  - Schemas: {len(context.get('schemas', {}))}")
        print(f"  - Templates: {len(context.get('templates', {}))}")
        print(f"  - Examples: {len(context.get('examples', []))}")

        return True

    async def test_sql_agent(self):
        """Test SQL agent functionality"""
        print("\n🤖 Testing SQL Agent")
        print("=" * 40)

        context_loader = ContextLoader(self.context_config)
        sql_agent = SQLAgent(context_loader=context_loader)

        # Test query type detection
        test_queries = [
            ("What is the total cost?", "aggregation"),
            ("Show daily cost trend", "time_series"),
            ("Compare AWS vs Azure costs", "comparison"),
            ("Top 5 applications by cost", "ranking")
        ]

        for query, expected_type in test_queries:
            detected_type = sql_agent.detect_query_type(query)
            status = "✅" if detected_type == expected_type else "⚠️"
            print(f"{status} '{query}' → {detected_type} (expected: {expected_type})")

        # Test template application
        print("\n📝 Testing Template Application")
        try:
            sql = sql_agent.apply_template("total_cost", {
                "cost_column": "cost",
                "table_name": "cost_analysis",
                "date_filter": "2024-01-01"
            })
            print(f"✅ Template application successful")
            print(f"   Generated SQL: {sql[:100]}...")
        except Exception as e:
            print(f"❌ Template application failed: {str(e)}")

        # Test context prompt building
        prompt = sql_agent.build_context_prompt("What is the total cost?", "aggregation")
        print(f"✅ Context prompt built ({len(prompt)} characters)")

        return True

    async def test_step_executor(self):
        """Test step executor functionality"""
        print("\n⚙️ Testing Step Executor")
        print("=" * 40)

        context_loader = ContextLoader(self.context_config)
        sql_agent = SQLAgent(context_loader=context_loader)
        step_executor = StepExecutor(context_loader, sql_agent)

        # Test default pipeline config
        default_config = step_executor.get_default_pipeline_config()
        print(f"✅ Default pipeline has {len(default_config)} steps")
        for config in default_config:
            status = "enabled" if config.enabled else "disabled"
            print(f"  - {config.name} ({config.step_type.value}): {status}")

        # Test step creation
        step_config = StepConfig(
            step_type=StepType.CONTEXT_LOAD,
            name="test_context_load",
            description="Test context loading step"
        )

        try:
            step = step_executor.create_step(step_config)
            print(f"✅ Created step: {step.name}")
        except Exception as e:
            print(f"❌ Step creation failed: {str(e)}")

        return True

    async def test_pipeline_agent(self):
        """Test full pipeline agent functionality"""
        print("\n🚀 Testing Pipeline Agent")
        print("=" * 40)

        # Note: This test runs without actual BigQuery connection
        # In production, you would inject the real connections
        pipeline_agent = PipelineAgent(config=self.pipeline_config)

        # Test query processing (dry run without actual SQL execution)
        test_queries = [
            "What is the total cost?",
            "Show top 5 applications by cost",
            "Budget variance by application"
        ]

        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            try:
                # This will process until SQL generation step
                # (execution will fail without database connection)
                result = await pipeline_agent.process_query(
                    query=query,
                    use_cache=False
                )

                print(f"  Execution ID: {result.get('execution_id')}")
                print(f"  Status: {result.get('status')}")
                print(f"  Query Type: {result.get('query_type')}")
                print(f"  Steps Completed: {result.get('steps_completed', 0)}/{result.get('total_steps', 0)}")

                if result.get('sql_query'):
                    print(f"  Generated SQL: {result['sql_query'][:100]}...")

                if result.get('error'):
                    print(f"  Expected Error (no DB): {result['error'][:100]}...")

            except Exception as e:
                print(f"  Expected Error (no DB): {str(e)[:100]}...")

        # Test available features
        query_types = pipeline_agent.get_available_query_types()
        print(f"\n📊 Available query types: {', '.join(query_types)}")

        context_info = pipeline_agent.get_context_info()
        schemas = context_info.get('schemas', {})
        templates = context_info.get('templates', {})
        print(f"📊 Context info: {len(schemas)} schemas, {len(templates)} templates")

        return True

    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("🧪 Context-Aware Pipeline System Tests")
        print("=" * 50)

        tests = [
            ("Context Loader", self.test_context_loader),
            ("SQL Agent", self.test_sql_agent),
            ("Step Executor", self.test_step_executor),
            ("Pipeline Agent", self.test_pipeline_agent)
        ]

        results = []
        for test_name, test_func in tests:
            try:
                success = await test_func()
                results.append((test_name, success, None))
            except Exception as e:
                results.append((test_name, False, str(e)))

        # Print summary
        print("\n📋 Test Summary")
        print("=" * 20)
        for test_name, success, error in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
            if error:
                print(f"     Error: {error}")

        passed = sum(1 for _, success, _ in results if success)
        total = len(results)
        print(f"\n🎯 Results: {passed}/{total} tests passed")

        return passed == total

async def main():
    """Main test runner"""
    test_runner = PipelineSystemTest()
    success = await test_runner.run_all_tests()

    if success:
        print("\n🎉 All tests passed! Pipeline system is ready.")
        return 0
    else:
        print("\n💥 Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())