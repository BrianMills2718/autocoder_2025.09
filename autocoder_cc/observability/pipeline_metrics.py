#!/usr/bin/env python3
"""
Pipeline Stage Metrics - Track and report on system generation pipeline stages
"""
from typing import Optional, Dict, Any, List
from enum import Enum
import time
from datetime import datetime
from autocoder_cc.observability.structured_logging import get_logger
from autocoder_cc.observability.metrics import get_metrics_collector

logger = get_logger(__name__)
metrics = get_metrics_collector("pipeline_metrics")


class PipelineStage(Enum):
    """Enumeration of pipeline stages for consistent tracking"""
    NATURAL_LANGUAGE_CONVERSION = "natural_language_conversion"
    BLUEPRINT_PARSING = "blueprint_parsing"
    BLUEPRINT_HEALING = "blueprint_healing"
    COMPONENT_GENERATION = "component_generation"
    VALIDATION = "validation"
    DEPLOYMENT = "deployment"
    SYSTEM_STARTUP = "system_startup"


class PipelineStageMetrics:
    """Track metrics for each stage of the system generation pipeline"""

    def __init__(self):
        self.stage_timings: Dict[str, float] = {}
        self.stage_start_times: Dict[str, float] = {}
        self.stage_errors: Dict[str, List[Exception]] = {}
        self.critical_errors_detected = False

    def start_stage(self, stage: PipelineStage) -> None:
        """Mark the start of a pipeline stage"""
        stage_name = stage.value
        self.stage_start_times[stage_name] = time.time()
        logger.info(f"Pipeline stage started: {stage_name}", extra={
            "stage": stage_name,
            "event": "stage_start",
            "timestamp": datetime.utcnow().isoformat()
        })
        metrics.increment(f"pipeline.stage.{stage_name}.started")

    def end_stage(self, stage: PipelineStage, success: bool = True, error: Optional[Exception] = None) -> None:
        """Mark the end of a pipeline stage"""
        stage_name = stage.value

        # Calculate duration
        if stage_name in self.stage_start_times:
            duration = time.time() - self.stage_start_times[stage_name]
            self.stage_timings[stage_name] = duration
            metrics.histogram(f"pipeline.stage.{stage_name}.duration_seconds", duration)

        # Record result
        result = "success" if success else "failure"
        metrics.increment(f"pipeline.stage.{stage_name}.{result}")

        # Log stage completion
        log_data = {
            "stage": stage_name,
            "event": "stage_end",
            "success": success,
            "duration_seconds": self.stage_timings.get(stage_name, 0),
            "timestamp": datetime.utcnow().isoformat()
        }

        if error:
            self.record_stage_error(stage, error)
            log_data["error"] = str(error)
            log_data["error_type"] = type(error).__name__

        if success:
            logger.info(f"Pipeline stage completed: {stage_name}", extra=log_data)
        else:
            logger.error(f"Pipeline stage failed: {stage_name}", extra=log_data)

    def record_stage_error(self, stage: PipelineStage, error: Exception) -> None:
        """Record an error for a specific stage"""
        stage_name = stage.value

        # Store error
        if stage_name not in self.stage_errors:
            self.stage_errors[stage_name] = []
        self.stage_errors[stage_name].append(error)

        # Categorize error
        self._categorize_error(stage, error)

        # Record error metric
        error_type = type(error).__name__
        metrics.increment(f"pipeline.stage.{stage_name}.error.{error_type}")

    def _categorize_error(self, stage: PipelineStage, error: Exception) -> None:
        """Categorize errors by severity and type"""
        error_str = str(error).lower()
        error_type = type(error).__name__

        # Check for critical blueprint parsing errors
        if stage == PipelineStage.BLUEPRINT_PARSING:
            if "blueprint validation failed" in error_str:
                logger.critical(
                    "🚨 SYSTEM-CRITICAL: Blueprint parsing prevents ALL generation",
                    extra={
                        "error": str(error),
                        "error_type": error_type,
                        "impact": "system_generation_blocked",
                        "severity": "critical"
                    }
                )
                self.critical_errors_detected = True
                metrics.increment("pipeline.critical_errors.blueprint_parsing")
            elif "schema_version" in error_str:
                logger.critical(
                    "🚨 SCHEMA ERROR: Blueprint schema version issue",
                    extra={
                        "error": str(error),
                        "error_type": error_type,
                        "impact": "blueprint_validation_failure",
                        "severity": "critical"
                    }
                )
                self.critical_errors_detected = True
                metrics.increment("pipeline.critical_errors.schema_version")

        # Check for model configuration errors
        elif stage == PipelineStage.COMPONENT_GENERATION:
            if "o4-mini" in error_str or "model" in error_str:
                logger.critical(
                    "🚨 CONFIGURATION ERROR: Invalid model configuration",
                    extra={
                        "error": str(error),
                        "error_type": error_type,
                        "impact": "llm_generation_blocked",
                        "severity": "critical"
                    }
                )
                self.critical_errors_detected = True
                metrics.increment("pipeline.critical_errors.model_config")

        # Check for natural language conversion errors
        elif stage == PipelineStage.NATURAL_LANGUAGE_CONVERSION:
            if "natural language translation requires" in error_str:
                logger.critical(
                    "🚨 LLM DEPENDENCY: Natural language conversion unavailable",
                    extra={
                        "error": str(error),
                        "error_type": error_type,
                        "impact": "natural_language_blocked",
                        "severity": "critical"
                    }
                )
                self.critical_errors_detected = True
                metrics.increment("pipeline.critical_errors.llm_dependency")

    def get_pipeline_summary(self) -> Dict[str, Any]:
        """Get a summary of the pipeline execution"""
        total_duration = sum(self.stage_timings.values())

        # Count successes and failures
        stages_attempted = len(self.stage_start_times)
        stages_completed = len([s for s in self.stage_timings.keys()
                               if s not in self.stage_errors])

        summary = {
            "total_duration_seconds": total_duration,
            "stages_attempted": stages_attempted,
            "stages_completed": stages_completed,
            "stages_failed": len(self.stage_errors),
            "critical_errors": self.critical_errors_detected,
            "stage_timings": self.stage_timings,
            "stage_errors": {
                stage: [str(e) for e in errors]
                for stage, errors in self.stage_errors.items()
            }
        }

        # Log summary
        logger.info("Pipeline execution summary", extra=summary)

        # Record summary metrics
        metrics.histogram("pipeline.total_duration_seconds", total_duration)
        metrics.gauge("pipeline.stages_completed", stages_completed)
        metrics.gauge("pipeline.stages_failed", len(self.stage_errors))

        return summary

    def require_stage_success(self, stage: PipelineStage) -> None:
        """Check if a stage completed successfully, raise if not"""
        stage_name = stage.value
        if stage_name in self.stage_errors:
            errors = self.stage_errors[stage_name]
            raise RuntimeError(
                f"Pipeline stage '{stage_name}' failed with {len(errors)} errors: "
                f"{', '.join(str(e) for e in errors[:3])}"
            )


# Global instance for convenience
pipeline_metrics = PipelineStageMetrics()


def track_pipeline_stage(stage: PipelineStage):
    """Decorator to track pipeline stage execution"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            pipeline_metrics.start_stage(stage)
            try:
                result = func(*args, **kwargs)
                pipeline_metrics.end_stage(stage, success=True)
                return result
            except Exception as e:
                pipeline_metrics.end_stage(stage, success=False, error=e)
                raise
        return wrapper
    return decorator

