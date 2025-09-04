#!/usr/bin/env python3
"""
Dedicated GitHub Actions Integration Module
Provides proper GitHub Actions annotations, outputs, and workflow integration
"""

import os
import sys
import json
import uuid
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum


class AnnotationType(Enum):
    """GitHub Actions annotation types"""
    ERROR = "error"
    WARNING = "warning"
    NOTICE = "notice"
    DEBUG = "debug"


class SeverityLevel(Enum):
    """Severity levels for annotations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class GitHubAnnotation:
    """Structured GitHub Actions annotation"""
    type: AnnotationType
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    title: Optional[str] = None
    severity: Optional[SeverityLevel] = None
    
    def __post_init__(self):
        """Validate annotation parameters"""
        if not self.message:
            raise ValueError("Annotation message cannot be empty")
        
        if self.line is not None and self.line < 1:
            raise ValueError("Line number must be positive")
        
        if self.column is not None and self.column < 1:
            raise ValueError("Column number must be positive")
        
        if self.end_line is not None:
            if self.line is None:
                raise ValueError("end_line requires line to be set")
            if self.end_line < self.line:
                raise ValueError("end_line must be >= line")
        
        if self.end_column is not None:
            if self.column is None:
                raise ValueError("end_column requires column to be set")
    
    def format(self) -> str:
        """Format annotation for GitHub Actions output"""
        # Build annotation command
        command_parts = [f"::{self.type.value}"]
        
        # Add properties
        properties = []
        
        if self.file:
            properties.append(f"file={self.file}")
        
        if self.line is not None:
            properties.append(f"line={self.line}")
        
        if self.column is not None:
            properties.append(f"col={self.column}")
        
        if self.end_line is not None:
            properties.append(f"endLine={self.end_line}")
        
        if self.end_column is not None:
            properties.append(f"endColumn={self.end_column}")
        
        if self.title:
            properties.append(f"title={self._escape_property(self.title)}")
        
        if properties:
            command_parts.append(" " + ",".join(properties))
        
        command_parts.append(f"::{self._escape_data(self.message)}")
        
        return "".join(command_parts)
    
    def _escape_property(self, value: str) -> str:
        """Escape property values for GitHub Actions"""
        return value.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A').replace(',', '%2C').replace(':', '%3A')
    
    def _escape_data(self, value: str) -> str:
        """Escape data values for GitHub Actions"""
        return value.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')


@dataclass
class WorkflowOutput:
    """GitHub Actions workflow output"""
    name: str
    value: str
    
    def __post_init__(self):
        """Validate output parameters"""
        if not self.name:
            raise ValueError("Output name cannot be empty")
        
        if not self.name.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Output name must contain only alphanumeric characters, hyphens, and underscores")
    
    def set(self):
        """Set GitHub Actions output"""
        if 'GITHUB_OUTPUT' in os.environ:
            # GitHub Actions new output format
            output_file = os.environ['GITHUB_OUTPUT']
            delimiter = f"ghadelimiter_{uuid.uuid4()}"
            
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(f"{self.name}<<{delimiter}\n")
                f.write(f"{self.value}\n")
                f.write(f"{delimiter}\n")
        else:
            # Fallback to echo format (deprecated but still works)
            escaped_value = self.value.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
            print(f"::set-output name={self.name}::{escaped_value}")


@dataclass
class WorkflowSummary:
    """GitHub Actions job summary"""
    content: str
    append: bool = False
    
    def write(self):
        """Write job summary"""
        if 'GITHUB_STEP_SUMMARY' in os.environ:
            summary_file = os.environ['GITHUB_STEP_SUMMARY']
            mode = 'a' if self.append else 'w'
            
            with open(summary_file, mode, encoding='utf-8') as f:
                f.write(self.content)
        else:
            # Fallback: print to stdout
            print("## Job Summary")
            print(self.content)


class GitHubActionsReporter:
    """Comprehensive GitHub Actions integration and reporting system"""
    
    def __init__(self, workflow_name: str = None):
        self.workflow_name = workflow_name or "Unknown Workflow"
        self.annotations: List[GitHubAnnotation] = []
        self.outputs: Dict[str, str] = {}
        self.summary_sections: List[str] = []
        
        # Detect GitHub Actions environment
        self.is_github_actions = self._detect_github_actions_environment()
        
        # Initialize workflow context
        self.context = self._get_workflow_context()
    
    def _detect_github_actions_environment(self) -> bool:
        """Detect if running in GitHub Actions environment"""
        return 'GITHUB_ACTIONS' in os.environ or 'CI' in os.environ
    
    def _get_workflow_context(self) -> Dict[str, Any]:
        """Get GitHub Actions workflow context"""
        return {
            'repository': os.environ.get('GITHUB_REPOSITORY'),
            'ref': os.environ.get('GITHUB_REF'),
            'sha': os.environ.get('GITHUB_SHA'),
            'actor': os.environ.get('GITHUB_ACTOR'),
            'workflow': os.environ.get('GITHUB_WORKFLOW'),
            'job': os.environ.get('GITHUB_JOB'),
            'run_id': os.environ.get('GITHUB_RUN_ID'),
            'run_number': os.environ.get('GITHUB_RUN_NUMBER'),
            'workspace': os.environ.get('GITHUB_WORKSPACE'),
            'event_name': os.environ.get('GITHUB_EVENT_NAME')
        }
    
    def error(self, 
              message: str, 
              file: str = None, 
              line: int = None,
              column: int = None,
              title: str = None) -> GitHubAnnotation:
        """Create and output error annotation"""
        annotation = GitHubAnnotation(
            type=AnnotationType.ERROR,
            message=message,
            file=file,
            line=line,
            column=column,
            title=title,
            severity=SeverityLevel.HIGH
        )
        
        self.annotations.append(annotation)
        print(annotation.format(), file=sys.stderr)
        return annotation
    
    def warning(self, 
                message: str, 
                file: str = None, 
                line: int = None,
                column: int = None,
                title: str = None) -> GitHubAnnotation:
        """Create and output warning annotation"""
        annotation = GitHubAnnotation(
            type=AnnotationType.WARNING,
            message=message,
            file=file,
            line=line,
            column=column,
            title=title,
            severity=SeverityLevel.MEDIUM
        )
        
        self.annotations.append(annotation)
        print(annotation.format())
        return annotation
    
    def notice(self, 
               message: str, 
               file: str = None, 
               line: int = None,
               column: int = None,
               title: str = None) -> GitHubAnnotation:
        """Create and output notice annotation"""
        annotation = GitHubAnnotation(
            type=AnnotationType.NOTICE,
            message=message,
            file=file,
            line=line,
            column=column,
            title=title,
            severity=SeverityLevel.LOW
        )
        
        self.annotations.append(annotation)
        print(annotation.format())
        return annotation
    
    def debug(self, message: str) -> GitHubAnnotation:
        """Create and output debug annotation"""
        annotation = GitHubAnnotation(
            type=AnnotationType.DEBUG,
            message=message,
            severity=SeverityLevel.LOW
        )
        
        self.annotations.append(annotation)
        if self.is_github_actions:
            print(annotation.format())
        return annotation
    
    def set_output(self, name: str, value: Union[str, int, float, bool, Dict, List]):
        """Set workflow output for downstream jobs"""
        # Convert value to string
        if isinstance(value, (dict, list)):
            str_value = json.dumps(value)
        elif isinstance(value, bool):
            str_value = "true" if value else "false"
        else:
            str_value = str(value)
        
        output = WorkflowOutput(name=name, value=str_value)
        output.set()
        
        self.outputs[name] = str_value
        return output
    
    def add_summary_section(self, title: str, content: str, level: int = 2):
        """Add section to job summary"""
        header = "#" * level
        section = f"{header} {title}\n\n{content}\n\n"
        self.summary_sections.append(section)
    
    def add_summary_table(self, 
                         title: str, 
                         headers: List[str], 
                         rows: List[List[str]], 
                         level: int = 2):
        """Add table to job summary"""
        header = "#" * level
        table_content = f"{header} {title}\n\n"
        
        # Create markdown table
        table_content += "| " + " | ".join(headers) + " |\n"
        table_content += "| " + " | ".join(["---"] * len(headers)) + " |\n"
        
        for row in rows:
            table_content += "| " + " | ".join(str(cell) for cell in row) + " |\n"
        
        table_content += "\n"
        self.summary_sections.append(table_content)
    
    def add_summary_code_block(self, 
                              title: str, 
                              code: str, 
                              language: str = "text",
                              level: int = 2):
        """Add code block to job summary"""
        header = "#" * level
        code_content = f"{header} {title}\n\n```{language}\n{code}\n```\n\n"
        self.summary_sections.append(code_content)
    
    def write_summary(self, title: str = None):
        """Write complete job summary"""
        summary_title = title or f"{self.workflow_name} Summary"
        
        content = f"# {summary_title}\n\n"
        content += f"**Timestamp:** {datetime.now(timezone.utc).isoformat()}\n\n"
        
        # Add workflow context if available
        if self.context['repository']:
            content += f"**Repository:** {self.context['repository']}\n"
        if self.context['ref']:
            content += f"**Ref:** {self.context['ref']}\n"
        if self.context['sha']:
            content += f"**SHA:** `{self.context['sha'][:8]}`\n"
        
        content += "\n"
        
        # Add summary sections
        for section in self.summary_sections:
            content += section
        
        # Add annotations summary
        if self.annotations:
            content += "## Annotations Summary\n\n"
            
            error_count = sum(1 for a in self.annotations if a.type == AnnotationType.ERROR)
            warning_count = sum(1 for a in self.annotations if a.type == AnnotationType.WARNING)
            notice_count = sum(1 for a in self.annotations if a.type == AnnotationType.NOTICE)
            
            content += f"- **Errors:** {error_count}\n"
            content += f"- **Warnings:** {warning_count}\n"
            content += f"- **Notices:** {notice_count}\n\n"
        
        # Add outputs summary
        if self.outputs:
            content += "## Workflow Outputs\n\n"
            for name, value in self.outputs.items():
                content += f"- **{name}:** `{value}`\n"
            content += "\n"
        
        summary = WorkflowSummary(content=content)
        summary.write()
        
        return content
    
    def group_start(self, name: str):
        """Start collapsible group in logs"""
        if self.is_github_actions:
            print(f"::group::{name}")
    
    def group_end(self):
        """End collapsible group in logs"""
        if self.is_github_actions:
            print("::endgroup::")
    
    def mask_value(self, value: str):
        """Mask sensitive value in logs"""
        if self.is_github_actions:
            print(f"::add-mask::{value}")
    
    def stop_commands(self, token: str = None):
        """Stop processing workflow commands"""
        stop_token = token or hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:16]
        if self.is_github_actions:
            print(f"::stop-commands::{stop_token}")
        return stop_token
    
    def resume_commands(self, token: str):
        """Resume processing workflow commands"""
        if self.is_github_actions:
            print(f"::{token}::")
    
    def save_state(self, name: str, value: str):
        """Save state for post job"""
        if 'GITHUB_STATE' in os.environ:
            state_file = os.environ['GITHUB_STATE']
            with open(state_file, 'a', encoding='utf-8') as f:
                f.write(f"{name}={value}\n")
        else:
            print(f"::save-state name={name}::{value}")
    
    def get_annotations_by_type(self, annotation_type: AnnotationType) -> List[GitHubAnnotation]:
        """Get annotations by type"""
        return [a for a in self.annotations if a.type == annotation_type]
    
    def get_annotations_by_file(self, file_path: str) -> List[GitHubAnnotation]:
        """Get annotations for specific file"""
        return [a for a in self.annotations if a.file == file_path]
    
    def get_annotation_summary(self) -> Dict[str, Any]:
        """Get summary of all annotations"""
        # Convert annotations to JSON-serializable format
        serializable_annotations = []
        for annotation in self.annotations:
            annotation_dict = asdict(annotation)
            # Convert enum to string
            annotation_dict['type'] = annotation.type.value
            if annotation.severity:
                annotation_dict['severity'] = annotation.severity.value
            serializable_annotations.append(annotation_dict)
        
        return {
            'total_annotations': len(self.annotations),
            'errors': len(self.get_annotations_by_type(AnnotationType.ERROR)),
            'warnings': len(self.get_annotations_by_type(AnnotationType.WARNING)),
            'notices': len(self.get_annotations_by_type(AnnotationType.NOTICE)),
            'debug': len(self.get_annotations_by_type(AnnotationType.DEBUG)),
            'files_with_annotations': len(set(a.file for a in self.annotations if a.file)),
            'annotations': serializable_annotations
        }
    
    def export_annotations(self, file_path: str):
        """Export annotations to JSON file"""
        summary = self.get_annotation_summary()
        summary['workflow_context'] = self.context
        summary['export_timestamp'] = datetime.now(timezone.utc).isoformat()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
    
    def validate_environment(self) -> Dict[str, Any]:
        """Validate GitHub Actions environment"""
        validation_result = {
            'is_github_actions': self.is_github_actions,
            'required_vars_present': True,
            'optional_vars_present': True,
            'missing_required': [],
            'missing_optional': [],
            'warnings': []
        }
        
        # Required environment variables
        required_vars = ['GITHUB_WORKSPACE', 'GITHUB_REPOSITORY']
        for var in required_vars:
            if var not in os.environ:
                validation_result['required_vars_present'] = False
                validation_result['missing_required'].append(var)
        
        # Optional but recommended environment variables
        optional_vars = ['GITHUB_SHA', 'GITHUB_REF', 'GITHUB_ACTOR', 'GITHUB_WORKFLOW']
        for var in optional_vars:
            if var not in os.environ:
                validation_result['optional_vars_present'] = False
                validation_result['missing_optional'].append(var)
        
        # Check for output file availability
        if 'GITHUB_OUTPUT' not in os.environ:
            validation_result['warnings'].append("GITHUB_OUTPUT not available, using deprecated set-output")
        
        if 'GITHUB_STEP_SUMMARY' not in os.environ:
            validation_result['warnings'].append("GITHUB_STEP_SUMMARY not available, summary will be printed to stdout")
        
        return validation_result


def create_documentation_health_reporter(workflow_name: str = "Documentation Health Check") -> GitHubActionsReporter:
    """Create a pre-configured reporter for documentation health workflows"""
    reporter = GitHubActionsReporter(workflow_name)
    
    # Validate environment
    env_validation = reporter.validate_environment()
    
    if not env_validation['is_github_actions']:
        reporter.warning("Not running in GitHub Actions environment, some features may not work")
    
    if not env_validation['required_vars_present']:
        for var in env_validation['missing_required']:
            reporter.warning(f"Required environment variable missing: {var}")
    
    for warning in env_validation['warnings']:
        reporter.notice(warning)
    
    return reporter


if __name__ == "__main__":
    # Example usage and testing
    reporter = create_documentation_health_reporter()
    
    # Example annotations
    reporter.notice("Documentation health check starting")
    reporter.warning("Some documentation files are incomplete", file="docs/api.md", line=42)
    reporter.error("Critical documentation issue found", file="README.md", line=1, title="Missing required section")
    
    # Example outputs
    reporter.set_output("health_score", 85)
    reporter.set_output("issues_found", 3)
    reporter.set_output("validation_passed", False)
    
    # Example summary
    reporter.add_summary_section("Health Check Results", "Documentation health score: 85/100")
    reporter.add_summary_table("Issues Found", 
                              ["File", "Line", "Issue", "Severity"],
                              [["README.md", "1", "Missing section", "High"],
                               ["docs/api.md", "42", "Incomplete content", "Medium"]])
    
    reporter.write_summary()
    
    # Export annotations for analysis
    reporter.export_annotations("annotations.json")
    
    print("\nAnnotation Summary:")
    print(json.dumps(reporter.get_annotation_summary(), indent=2))