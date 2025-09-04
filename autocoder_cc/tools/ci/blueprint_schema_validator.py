"""
Blueprint Schema Validator for CI/CD Pipeline
Validates all blueprint files against JSON Schema definitions
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from autocoder_cc.validation.schema_validator import SchemaValidator, ValidationLevel


class CIBlueprintSchemaValidator:
    """CI/CD pipeline blueprint schema validator"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent.parent
        self.schema_validator = SchemaValidator()
        
    def validate_project_blueprints(self) -> Dict[str, Any]:
        """Validate all blueprint files in the project"""
        results = {
            "status": "success",
            "files_validated": 0,
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        # Find all blueprint files (exclude generated systems and helm/k8s directories)
        blueprint_files = []
        
        # Look for architecture and deployment blueprints, but exclude generated systems
        for pattern in ["**/architecture.yaml", "**/architecture.yml", "**/architecture.json"]:
            for file_path in self.project_root.glob(pattern):
                # Skip generated systems and helm/k8s directories
                if ("generated_systems" not in str(file_path) and 
                    "helm" not in str(file_path) and 
                    "k8s" not in str(file_path)):
                    blueprint_files.append(file_path)
        
        for pattern in ["**/deployment.yaml", "**/deployment.yml", "**/deployment.json"]:
            for file_path in self.project_root.glob(pattern):
                # Skip generated systems and helm/k8s directories
                if ("generated_systems" not in str(file_path) and 
                    "helm" not in str(file_path) and 
                    "k8s" not in str(file_path)):
                    blueprint_files.append(file_path)
        
        # Validate each file
        for file_path in blueprint_files:
            # Determine blueprint type from filename
            if "architecture" in file_path.name:
                blueprint_type = "architecture"
            elif "deployment" in file_path.name:
                blueprint_type = "deployment"
            else:
                continue
            
            try:
                errors = self.schema_validator.validate_blueprint_file(file_path, blueprint_type)
                
                file_results = {
                    "file": str(file_path.relative_to(self.project_root)),
                    "type": blueprint_type,
                    "valid": len(errors) == 0,
                    "errors": [],
                    "warnings": []
                }
                
                # Categorize errors
                for error in errors:
                    error_dict = {
                        "level": error.level.value,
                        "message": error.message,
                        "path": error.path,
                        "schema_path": error.schema_path,
                        "value": error.value
                    }
                    
                    if error.level in [ValidationLevel.ERROR, ValidationLevel.CRITICAL]:
                        file_results["errors"].append(error_dict)
                        results["errors"].append(error_dict)
                    elif error.level == ValidationLevel.WARNING:
                        file_results["warnings"].append(error_dict)
                        results["warnings"].append(error_dict)
                
                results["details"][str(file_path.relative_to(self.project_root))] = file_results
                results["files_validated"] += 1
                
            except Exception as e:
                error_dict = {
                    "level": "error",
                    "message": f"Failed to validate {file_path}: {str(e)}",
                    "path": str(file_path.relative_to(self.project_root)),
                    "schema_path": None,
                    "value": None
                }
                results["errors"].append(error_dict)
                results["details"][str(file_path.relative_to(self.project_root))] = {
                    "file": str(file_path.relative_to(self.project_root)),
                    "type": blueprint_type,
                    "valid": False,
                    "errors": [error_dict],
                    "warnings": []
                }
        
        # Set overall status
        if results["errors"]:
            results["status"] = "failure"
        elif results["warnings"]:
            results["status"] = "warning"
        
        return results
    
    def validate_build_pipeline(self) -> bool:
        """Validate blueprints for build pipeline"""
        print("🔍 Validating blueprint files against JSON Schema...")
        
        results = self.validate_project_blueprints()
        
        # Print summary
        print(f"📊 Schema validation summary:")
        print(f"   Files validated: {results['files_validated']}")
        print(f"   Errors: {len(results['errors'])}")
        print(f"   Warnings: {len(results['warnings'])}")
        
        # Print details
        if results['errors']:
            print("\n❌ Schema validation errors:")
            for error in results['errors']:
                print(f"   - {error['message']}")
                if error['path']:
                    print(f"     Path: {error['path']}")
                if error['schema_path']:
                    print(f"     Schema: {error['schema_path']}")
        
        if results['warnings']:
            print("\n⚠️ Schema validation warnings:")
            for warning in results['warnings']:
                print(f"   - {warning['message']}")
                if warning['path']:
                    print(f"     Path: {warning['path']}")
        
        # Print per-file results
        if results['details']:
            print("\n📁 Per-file results:")
            for file_path, file_results in results['details'].items():
                status_icon = "✅" if file_results['valid'] else "❌"
                print(f"   {status_icon} {file_path} ({file_results['type']})")
                
                if file_results['errors']:
                    for error in file_results['errors']:
                        print(f"      ❌ {error['message']}")
                
                if file_results['warnings']:
                    for warning in file_results['warnings']:
                        print(f"      ⚠️ {warning['message']}")
        
        return results['status'] == 'success'
    
    def generate_schema_report(self, output_file: Optional[Path] = None) -> None:
        """Generate detailed schema validation report"""
        results = self.validate_project_blueprints()
        
        # Create detailed report
        report = {
            "timestamp": "2025-01-01T00:00:00Z",  # Will be updated by actual CI
            "project": "autocoder4_cc",
            "validation_results": results,
            "schema_info": {
                "architecture": self.schema_validator.get_schema_info("architecture"),
                "deployment": self.schema_validator.get_schema_info("deployment")
            }
        }
        
        # Write report
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"📄 Schema validation report written to: {output_file}")
        else:
            print(json.dumps(report, indent=2))


def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: python blueprint_schema_validator.py <command> [args]")
        print("Commands:")
        print("  validate      - Validate all blueprints (CI mode)")
        print("  report [file] - Generate detailed validation report")
        return 1
    
    command = sys.argv[1]
    validator = CIBlueprintSchemaValidator()
    
    if command == "validate":
        success = validator.validate_build_pipeline()
        return 0 if success else 1
    
    elif command == "report":
        output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else None
        validator.generate_schema_report(output_file)
        return 0
    
    else:
        print(f"Unknown command: {command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())