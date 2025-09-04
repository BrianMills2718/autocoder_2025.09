#!/usr/bin/env python3
"""
Gemini Debug Review Tool

This tool is specifically designed for debugging runtime errors and system issues.
It analyzes error logs, stack traces, and system state to provide actionable debugging guidance.

Use cases:
- Runtime error analysis
- System configuration issues
- Dependency problems
- Performance bottlenecks
- Integration failures
"""

import os
import sys
import argparse
import subprocess
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
import google.generativeai as genai
from dotenv import load_dotenv

# Add config directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "config"))

try:
    from gemini_review_config import ReviewConfig, find_config_file, create_default_config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

# Load environment variables
load_dotenv()

class GeminiDebugReviewer:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """Initialize the debug reviewer with API key."""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key not found. Set GEMINI_API_KEY in .env file or pass it as argument.")
        
        # Get model name from env or use default
        self.model_name = model_name or os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
        print(f"🔧 Using model: {self.model_name}")
        
    def collect_system_info(self, project_path: str = ".") -> Dict[str, Any]:
        """Collect system information for debugging."""
        print("📊 Collecting system information...")
        
        system_info = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "project_path": str(Path(project_path).resolve()),
            "python_version": sys.version,
            "platform": sys.platform,
            "environment_variables": {}
        }
        
        # Collect relevant environment variables
        relevant_vars = ['PYTHONPATH', 'PATH', 'GEMINI_API_KEY', 'OPENAI_API_KEY', 'NODE_PATH']
        for var in relevant_vars:
            if var in os.environ:
                system_info["environment_variables"][var] = os.environ[var]
        
        # Check for common configuration files
        config_files = [
            "requirements.txt", "setup.py", "pyproject.toml", 
            ".env", ".env.example", "pytest.ini", "Dockerfile"
        ]
        
        system_info["config_files"] = {}
        for config_file in config_files:
            config_path = Path(project_path) / config_file
            if config_path.exists():
                system_info["config_files"][config_file] = {
                    "exists": True,
                    "size": config_path.stat().st_size,
                    "modified": time.ctime(config_path.stat().st_mtime)
                }
            else:
                system_info["config_files"][config_file] = {"exists": False}
        
        return system_info
    
    def collect_error_logs(self, log_paths: Optional[List[str]] = None) -> str:
        """Collect error logs from specified paths or common locations."""
        print("📋 Collecting error logs...")
        
        if not log_paths:
            # Common log file locations
            log_paths = [
                "*.log", "logs/*.log", "*.err", "error.log", 
                "pytest.log", "test.log", "validation.log"
            ]
        
        collected_logs = []
        
        for pattern in log_paths:
            try:
                matches = list(Path(".").glob(pattern))
                for log_file in matches:
                    if log_file.exists() and log_file.stat().st_size > 0:
                        try:
                            with open(log_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                                collected_logs.append(f"=== {log_file} ===\n{content}\n")
                        except Exception as e:
                            collected_logs.append(f"=== {log_file} (read error: {e}) ===\n")
            except Exception as e:
                print(f"⚠️  Warning: Could not process log pattern {pattern}: {e}")
        
        return "\n".join(collected_logs) if collected_logs else "No error logs found."
    
    def run_system_checks(self, project_path: str = ".") -> str:
        """Run basic system health checks."""
        print("🔍 Running system health checks...")
        
        checks = []
        
        # Check Python dependencies
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "list"], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                checks.append("✅ Python dependencies check passed")
            else:
                checks.append(f"❌ Python dependencies check failed: {result.stderr}")
        except Exception as e:
            checks.append(f"❌ Python dependencies check error: {e}")
        
        # Check for common issues
        common_issues = [
            ("Missing .env file", ".env", "Configuration file"),
            ("Missing requirements.txt", "requirements.txt", "Dependencies file"),
            ("Missing setup.py", "setup.py", "Package configuration"),
        ]
        
        for issue_name, file_path, description in common_issues:
            if Path(project_path) / file_path:
                checks.append(f"✅ {description} found")
            else:
                checks.append(f"⚠️  {description} missing")
        
        return "\n".join(checks)
    
    def analyze_debug_info(self, system_info: Dict[str, Any], error_logs: str, 
                          health_checks: str, custom_prompt: Optional[str] = None) -> str:
        """Send debug information to Gemini for analysis."""
        print("🤖 Analyzing debug information with Gemini...")
        
        # Build the debug analysis prompt
        base_prompt = """You are an expert software debugging assistant. Analyze the provided system information, error logs, and health checks to identify the root cause of issues and provide actionable debugging guidance.

Please provide:
1. **Issue Identification**: What specific problems are you seeing?
2. **Root Cause Analysis**: What's likely causing these issues?
3. **Configuration Issues**: Any missing or incorrect configuration?
4. **Dependency Problems**: Missing or incompatible dependencies?
5. **Environment Issues**: System or environment-related problems?
6. **Actionable Steps**: Specific commands or changes to fix the issues
7. **Prevention**: How to avoid similar issues in the future

Be specific and provide concrete, actionable advice."""
        
        if custom_prompt:
            prompt = f"{base_prompt}\n\nAdditional focus areas:\n{custom_prompt}\n\n"
        else:
            prompt = base_prompt + "\n\n"
        
        # Add debug information
        prompt += f"SYSTEM INFORMATION:\n{json.dumps(system_info, indent=2)}\n\n"
        prompt += f"HEALTH CHECKS:\n{health_checks}\n\n"
        prompt += f"ERROR LOGS:\n{error_logs}\n\n"
        
        try:
            # Generate response
            response = self.model.generate_content(prompt)
            
            print("✅ Debug analysis complete")
            return response.text
            
        except Exception as e:
            print(f"❌ Gemini API error: {str(e)}")
            raise
    
    def save_debug_results(self, results: str, output_path: str = "debug-analysis.md"):
        """Save the debug analysis results to a file."""
        print(f"💾 Saving debug results to {output_path}...")
        
        # Create the output directory if it doesn't exist
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Gemini Debug Analysis\n")
            f.write(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            f.write(results)
            
        print(f"✅ Debug results saved to {output_path}")
    
    def debug(self, project_path: str = ".", 
              log_paths: Optional[List[str]] = None,
              custom_prompt: Optional[str] = None,
              output_path: str = "debug-analysis.md") -> str:
        """Main debug process."""
        print(f"\n🔧 Starting Gemini Debug Analysis for: {project_path}\n")
        
        try:
            # Step 1: Collect system information
            system_info = self.collect_system_info(project_path)
            
            # Step 2: Collect error logs
            error_logs = self.collect_error_logs(log_paths)
            
            # Step 3: Run health checks
            health_checks = self.run_system_checks(project_path)
            
            # Step 4: Analyze with Gemini
            results = self.analyze_debug_info(system_info, error_logs, health_checks, custom_prompt)
            
            # Step 5: Save results
            self.save_debug_results(results, output_path)
                
            print("\n✨ Debug analysis complete!")
            return results
            
        except Exception as e:
            print(f"\n❌ Error during debug analysis: {str(e)}")
            raise


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Debug runtime errors and system issues using Gemini AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Debug current directory
  python gemini_debug_review.py
  
  # Debug specific project with custom focus
  python gemini_debug_review.py /path/to/project --prompt "Focus on dependency issues"
  
  # Debug with specific log files
  python gemini_debug_review.py --logs "error.log" "test.log"
  
  # Save results to specific location
  python gemini_debug_review.py --output "debug-report.md"
        """
    )
    
    parser.add_argument(
        'project_path',
        nargs='?',
        default='.',
        help='Path to the project to debug (default: current directory)'
    )
    
    parser.add_argument(
        '--prompt', '-p',
        help='Additional prompt for specific debug focus'
    )
    
    parser.add_argument(
        '--logs', '-l',
        action='append',
        help='Specific log files to analyze (can be used multiple times)'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='debug-analysis.md',
        help='Output file path for debug results'
    )
    
    parser.add_argument(
        '--api-key',
        help='Gemini API key (can also be set via GEMINI_API_KEY env var)'
    )
    
    parser.add_argument(
        '--config', '-C',
        help='Path to configuration file (YAML or JSON)'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize debug reviewer
        reviewer = GeminiDebugReviewer(api_key=args.api_key)
        
        # Run debug analysis
        reviewer.debug(
            project_path=args.project_path,
            log_paths=args.logs,
            custom_prompt=args.prompt,
            output_path=args.output
        )
        
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 