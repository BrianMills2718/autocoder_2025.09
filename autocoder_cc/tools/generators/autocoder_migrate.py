#!/usr/bin/env python3
"""
Autocoder Blueprint Migration Tool
Provides automatic migration between blueprint schema versions.

Usage:
    autocoder migrate --from X --to Y blueprint.yaml
    autocoder migrate --from X --to Y --plan blueprint.yaml  # Show migration plan
    autocoder migrate --from X --to Y --apply blueprint.yaml  # Apply migration
    autocoder migrate --validate blueprint.yaml  # Validate schema version
"""

import argparse
import json
import sys
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

# Import schema versioning system
from autocoder_cc.core.schema_versioning import (
    SchemaVersionManager, 
    SchemaVersion, 
    SchemaType,
    detect_blueprint_type,
    migrate_blueprint_to_current,
    validate_blueprint_schema_version
)

logger = get_logger(__name__)


class MigrationTool:
    """Blueprint migration command-line tool"""
    
    def __init__(self):
        self.schema_manager = SchemaVersionManager()
    
    def parse_args(self) -> argparse.Namespace:
        """Parse command line arguments"""
        parser = argparse.ArgumentParser(
            description="Autocoder blueprint schema migration tool",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s --from 1.0 --to 1.1 --plan blueprint.yaml     # Show migration plan
  %(prog)s --from 1.0 --to 1.1 --apply blueprint.yaml    # Apply migration
  %(prog)s --validate blueprint.yaml                     # Validate schema version
  %(prog)s --current blueprint.yaml                      # Migrate to current version
            """
        )
        
        parser.add_argument("--from", dest="from_version", 
                          help="Source schema version (e.g., '1.0')")
        parser.add_argument("--to", dest="to_version", 
                          help="Target schema version (e.g., '1.1')")
        
        # Actions
        parser.add_argument("--plan", action="store_true", 
                          help="Show migration plan without applying changes")
        parser.add_argument("--apply", action="store_true", 
                          help="Apply migration and save to file")
        parser.add_argument("--validate", action="store_true", 
                          help="Validate blueprint schema version")
        parser.add_argument("--current", action="store_true", 
                          help="Migrate to current schema version")
        
        # File options
        parser.add_argument("blueprint_file", 
                          help="Blueprint file to migrate")
        parser.add_argument("--output", "-o", 
                          help="Output file path (default: overwrite input file)")
        
        # Options
        parser.add_argument("--dry-run", action="store_true", 
                          help="Show what would be done without making changes")
        parser.add_argument("--verbose", "-v", action="store_true", 
                          help="Enable verbose logging")
        
        return parser.parse_args()
    
    def load_blueprint(self, blueprint_path: Path) -> Dict[str, Any]:
        """Load blueprint from file"""
        if not blueprint_path.exists():
            raise FileNotFoundError(f"Blueprint file not found: {blueprint_path}")
        
        try:
            with blueprint_path.open("r", encoding="utf-8") as f:
                blueprint = yaml.safe_load(f)
            
            if not isinstance(blueprint, dict):
                raise ValueError("Blueprint file must contain a YAML dictionary")
            
            return blueprint
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in blueprint file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading blueprint file: {e}")
    
    def save_blueprint(self, blueprint: Dict[str, Any], output_path: Path):
        """Save blueprint to file"""
        try:
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with output_path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(blueprint, f, default_flow_style=False, sort_keys=False, indent=2)
            
            print(f"✅ Blueprint saved to: {output_path}")
            
        except Exception as e:
            raise ValueError(f"Error saving blueprint file: {e}")
    
    def generate_migration_plan(self, blueprint: Dict[str, Any], from_version: SchemaVersion, to_version: SchemaVersion) -> Dict[str, Any]:
        """Generate migration plan showing what changes will be made"""
        schema_type = detect_blueprint_type(blueprint)
        
        try:
            migration_path = self.schema_manager.migration_registry.get_migration_path(
                from_version, to_version, schema_type
            )
        except ValueError as e:
            return {
                "error": str(e),
                "from_version": str(from_version),
                "to_version": str(to_version),
                "schema_type": schema_type.value
            }
        
        plan = {
            "from_version": str(from_version),
            "to_version": str(to_version),
            "schema_type": schema_type.value,
            "migration_steps": len(migration_path),
            "steps": []
        }
        
        for i, migration in enumerate(migration_path, 1):
            step = {
                "step": i,
                "from": str(migration.from_version),
                "to": str(migration.to_version),
                "description": migration.description
            }
            plan["steps"].append(step)
        
        return plan
    
    def print_migration_plan(self, plan: Dict[str, Any]):
        """Print migration plan in a readable format"""
        if "error" in plan:
            print(f"❌ Migration Error: {plan['error']}")
            return
        
        print("📋 MIGRATION PLAN")
        print("=" * 50)
        print(f"Schema Type: {plan['schema_type']}")
        print(f"From Version: {plan['from_version']}")
        print(f"To Version: {plan['to_version']}")
        print(f"Migration Steps: {plan['migration_steps']}")
        print()
        
        if plan['migration_steps'] == 0:
            print("✅ No migration needed - versions are the same")
        else:
            print("Migration Steps:")
            for step in plan['steps']:
                print(f"  {step['step']}. {step['from']} → {step['to']}")
                print(f"     {step['description']}")
            print()
    
    def validate_blueprint(self, blueprint_path: Path) -> bool:
        """Validate blueprint schema version"""
        try:
            blueprint = self.load_blueprint(blueprint_path)
            schema_type = detect_blueprint_type(blueprint)
            current_version = self.schema_manager.detect_schema_version(blueprint, schema_type)
            
            # Validate version is supported
            self.schema_manager.validate_blueprint_version(blueprint, schema_type)
            
            print(f"✅ Blueprint validation successful")
            print(f"   File: {blueprint_path}")
            print(f"   Schema Type: {schema_type.value}")
            print(f"   Schema Version: {current_version}")
            print(f"   Supported: Yes")
            
            # Check if migration to current version is available
            current_supported = self.schema_manager.get_current_version(schema_type)
            if current_version < current_supported:
                print(f"   Note: Migration available to current version {current_supported}")
            
            return True
            
        except Exception as e:
            print(f"❌ Blueprint validation failed: {e}")
            return False
    
    def run(self) -> int:
        """Main entry point"""
        args = self.parse_args()
        
        # Configure logging
        if args.verbose:
            logging.basicConfig(level=logging.INFO)
        
        try:
            blueprint_path = Path(args.blueprint_file)
            
            # Validation mode
            if args.validate:
                success = self.validate_blueprint(blueprint_path)
                return 0 if success else 1
            
            # Load blueprint
            blueprint = self.load_blueprint(blueprint_path)
            schema_type = detect_blueprint_type(blueprint)
            
            # Current version migration mode
            if args.current:
                current_version = self.schema_manager.detect_schema_version(blueprint, schema_type)
                target_version = self.schema_manager.get_current_version(schema_type)
                
                print(f"🔄 Migrating to current schema version")
                print(f"   From: {current_version}")
                print(f"   To: {target_version}")
                print()
                
                if current_version == target_version:
                    print("✅ Blueprint is already at current version")
                    return 0
                
                # Generate migration plan
                plan = self.generate_migration_plan(blueprint, current_version, target_version)
                self.print_migration_plan(plan)
                
                if not args.plan and not args.dry_run:
                    # Apply migration
                    migrated_blueprint = self.schema_manager.migrate_blueprint(
                        blueprint, schema_type, target_version
                    )
                    
                    output_path = Path(args.output) if args.output else blueprint_path
                    self.save_blueprint(migrated_blueprint, output_path)
                
                return 0
            
            # Version-specific migration mode
            if not args.from_version or not args.to_version:
                print("❌ Error: --from and --to versions are required (or use --current)")
                return 1
            
            try:
                from_version = SchemaVersion(args.from_version)
                to_version = SchemaVersion(args.to_version)
            except ValueError as e:
                print(f"❌ Invalid version format: {e}")
                return 1
            
            # Verify current blueprint version matches --from
            actual_version = self.schema_manager.detect_schema_version(blueprint, schema_type)
            if actual_version != from_version:
                print(f"❌ Error: Blueprint version ({actual_version}) doesn't match --from ({from_version})")
                return 1
            
            # Generate migration plan
            plan = self.generate_migration_plan(blueprint, from_version, to_version)
            self.print_migration_plan(plan)
            
            if "error" in plan:
                return 1
            
            # Apply migration if requested
            if args.apply and not args.dry_run:
                migrated_blueprint = self.schema_manager.migrate_blueprint(
                    blueprint, schema_type, to_version
                )
                
                output_path = Path(args.output) if args.output else blueprint_path
                self.save_blueprint(migrated_blueprint, output_path)
            elif args.plan or args.dry_run:
                print("📝 Migration plan shown above (use --apply to execute)")
            else:
                print("📝 Use --plan to see migration plan or --apply to execute migration")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1


def main():
    """CLI entry point"""
    tool = MigrationTool()
    sys.exit(tool.run())


if __name__ == "__main__":
    main()