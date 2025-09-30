"""
Pipeline Factory - Creates configured pipeline instances
"""
from .pipeline_service import PipelineService
from .base_step import ParallelStep
from .steps import (
    InputProcessingStep,
    SQLGenerationStep,
    SQLValidationStep,
    SQLExecutionStep,
    VisualizationDetectionStep,
    ChartDataExtractionStep,
    DataValidationStep,
    ResponseFormattingStep
)

class PipelineFactory:
    """Factory for creating different pipeline configurations"""

    @staticmethod
    def create_standard_pipeline() -> PipelineService:
        """
        Create the standard BigQuery analytics pipeline

        Pipeline Flow:
        1. Input Processing
        2. SQL Generation
        3. SQL Validation (conditional)
        4. SQL Execution
        5. Parallel: Visualization Detection + Chart Data Extraction
        6. Data Validation (conditional)
        7. Response Formatting
        """
        pipeline = PipelineService()

        # Step 1: Process user input
        pipeline.add_step(InputProcessingStep())

        # Step 2: Generate SQL query
        pipeline.add_step(SQLGenerationStep())

        # Step 3: Validate SQL (conditional)
        pipeline.add_step(SQLValidationStep())

        # Step 4: Execute SQL
        pipeline.add_step(SQLExecutionStep())

        # Step 5: Parallel visualization processing
        viz_parallel_step = ParallelStep(
            name="visualization_processing",
            sub_steps=[
                VisualizationDetectionStep(),
                ChartDataExtractionStep()
            ],
            description="Parallel visualization detection and data extraction"
        )
        pipeline.add_step(viz_parallel_step)

        # Step 6: Validate chart data (conditional)
        pipeline.add_step(DataValidationStep())

        # Step 7: Format final response
        pipeline.add_step(ResponseFormattingStep())

        return pipeline

    @staticmethod
    def create_simple_pipeline() -> PipelineService:
        """
        Create a simple pipeline without validation

        Pipeline Flow:
        1. Input Processing
        2. SQL Generation
        3. SQL Execution
        4. Visualization Detection
        5. Chart Data Extraction
        6. Response Formatting
        """
        pipeline = PipelineService()

        pipeline.add_step(InputProcessingStep())
        pipeline.add_step(SQLGenerationStep())
        pipeline.add_step(SQLExecutionStep())
        pipeline.add_step(VisualizationDetectionStep())
        pipeline.add_step(ChartDataExtractionStep())
        pipeline.add_step(ResponseFormattingStep())

        return pipeline

    @staticmethod
    def create_validation_heavy_pipeline() -> PipelineService:
        """
        Create a pipeline with comprehensive validation

        Pipeline Flow:
        1. Input Processing
        2. SQL Generation
        3. SQL Validation (always enabled)
        4. SQL Execution
        5. Visualization Detection
        6. Chart Data Extraction
        7. Data Validation (always enabled)
        8. Response Formatting
        """
        pipeline = PipelineService()

        pipeline.add_step(InputProcessingStep())
        pipeline.add_step(SQLGenerationStep())

        # Force validation on
        sql_validation = SQLValidationStep()
        sql_validation.should_execute = lambda data: True  # Always execute
        pipeline.add_step(sql_validation)

        pipeline.add_step(SQLExecutionStep())
        pipeline.add_step(VisualizationDetectionStep())
        pipeline.add_step(ChartDataExtractionStep())

        # Force data validation on
        data_validation = DataValidationStep()
        data_validation.should_execute = lambda data: True  # Always execute
        pipeline.add_step(data_validation)

        pipeline.add_step(ResponseFormattingStep())

        return pipeline

    @staticmethod
    def create_custom_pipeline(
        enable_sql_validation: bool = True,
        enable_data_validation: bool = True,
        use_parallel_processing: bool = True
    ) -> PipelineService:
        """
        Create a custom pipeline with specific configurations

        Args:
            enable_sql_validation: Enable SQL validation step
            enable_data_validation: Enable data validation step
            use_parallel_processing: Use parallel processing for visualization steps
        """
        pipeline = PipelineService()

        # Always include core steps
        pipeline.add_step(InputProcessingStep())
        pipeline.add_step(SQLGenerationStep())

        # Conditional SQL validation
        if enable_sql_validation:
            pipeline.add_step(SQLValidationStep())

        pipeline.add_step(SQLExecutionStep())

        # Visualization processing (parallel or sequential)
        if use_parallel_processing:
            viz_parallel_step = ParallelStep(
                name="visualization_processing",
                sub_steps=[
                    VisualizationDetectionStep(),
                    ChartDataExtractionStep()
                ],
                description="Parallel visualization processing"
            )
            pipeline.add_step(viz_parallel_step)
        else:
            pipeline.add_step(VisualizationDetectionStep())
            pipeline.add_step(ChartDataExtractionStep())

        # Conditional data validation
        if enable_data_validation:
            pipeline.add_step(DataValidationStep())

        pipeline.add_step(ResponseFormattingStep())

        return pipeline

    @staticmethod
    def get_available_pipelines() -> dict:
        """Get list of available pipeline configurations"""
        return {
            "standard": {
                "name": "Standard Pipeline",
                "description": "Full featured pipeline with conditional validation",
                "steps": 8,
                "parallel_processing": True,
                "validation": "conditional"
            },
            "simple": {
                "name": "Simple Pipeline",
                "description": "Basic pipeline without validation",
                "steps": 6,
                "parallel_processing": False,
                "validation": "none"
            },
            "validation_heavy": {
                "name": "Validation Heavy Pipeline",
                "description": "Pipeline with comprehensive validation",
                "steps": 8,
                "parallel_processing": False,
                "validation": "comprehensive"
            },
            "custom": {
                "name": "Custom Pipeline",
                "description": "Configurable pipeline with custom options",
                "steps": "variable",
                "parallel_processing": "configurable",
                "validation": "configurable"
            }
        }