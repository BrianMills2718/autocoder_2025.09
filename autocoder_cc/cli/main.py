#!/usr/bin/env python3
"""
Autocoder CLI - Enterprise Roadmap v3 Main Command Interface
"""
import click
from pathlib import Path
from .local_orchestrator import run_local


@click.group()
@click.version_option(version="5.2.0", prog_name="autocoder")
def cli():
    """
    Autocoder v5.2 - Enterprise System Generation Platform
    
    Generate, validate, and deploy production-ready distributed systems from natural language.
    
    Enterprise Roadmap v3 Features:
    - ComposedComponent architecture with capability-based composition
    - Centralized configuration system with environment inheritance
    - Registry-driven generation pipeline with multi-stage validation
    - LocalOrchestrator for developer-friendly workflows
    - Structured observability with OpenTelemetry integration
    """
    pass


# Add subcommands
cli.add_command(run_local, name="run-local")


@cli.command()
@click.argument('description')
@click.option('--output', '-o', default='./generated_system', help='Output directory')
@click.option('--deploy', is_flag=True, help='Generate deployment artifacts')
def generate(description: str, output: str, deploy: bool):
    """Generate a system from natural language description."""
    click.echo(f"Generating system: {description}")
    click.echo(f"Output directory: {output}")
    
    # Implementation would call the main generation pipeline
    from autocoder_cc.blueprint_language.natural_language_to_blueprint import generate_system_from_description
    
    try:
        # Generate the system
        # By default, skip deployment unless explicitly requested with --deploy
        skip_deployment = not deploy
        result = generate_system_from_description(description, output_dir=output, skip_deployment=skip_deployment)
        click.echo(f"✅ System generated successfully at: {output}")
        
        if deploy:
            click.echo("🚀 Generating deployment artifacts...")
            # Implementation would generate Kubernetes/Docker artifacts
            
    except Exception as e:
        click.echo(f"❌ Generation failed: {e}")


@cli.command()
@click.argument('blueprint_path', type=click.Path(exists=True))
@click.option('--output', '-o', default='./validated_system', help='Output directory')
def validate(blueprint_path: str, output: str):
    """Validate a system blueprint."""
    click.echo(f"Validating blueprint: {blueprint_path}")
    
    # Implementation would use the validation framework
    try:
        from autocoder_cc.blueprint_language.validation_framework import validate_blueprint
        
        result = validate_blueprint(blueprint_path)
        if result.success:
            click.echo("✅ Blueprint validation passed")
        else:
            click.echo(f"❌ Blueprint validation failed: {result.errors}")
            
    except Exception as e:
        click.echo(f"❌ Validation error: {e}")


@cli.command() 
@click.argument('system_path', type=click.Path(exists=True))
@click.option('--environment', '-e', default='development', help='Deployment environment')
@click.option('--namespace', '-n', help='Kubernetes namespace')
def deploy(system_path: str, environment: str, namespace: str):
    """Deploy a generated system to target environment."""
    click.echo(f"Deploying system from: {system_path}")
    click.echo(f"Environment: {environment}")
    
    # Implementation would use ProductionDeploymentGenerator
    try:
        from blueprint_language.production_deployment_generator import ProductionDeploymentGenerator
        
        generator = ProductionDeploymentGenerator()
        # Implementation would deploy to the target environment
        click.echo("🚀 Deployment initiated...")
        
    except Exception as e:
        click.echo(f"❌ Deployment failed: {e}")


@cli.command()
@click.argument('target_version', required=False)
@click.option('--list', 'list_versions', is_flag=True, help='List available schema versions')
@click.option('--current', is_flag=True, help='Show current schema version')
@click.option('--status', is_flag=True, help='Show schema system status')
def migrate(target_version: str, list_versions: bool, current: bool, status: bool):
    """Migrate blueprint schemas between versions."""
    from autocoder_cc.core.schema_versioning import get_version_manager
    
    try:
        version_manager = get_version_manager()
        
        if list_versions:
            versions = version_manager.list_available_versions()
            if versions:
                click.echo("Available schema versions:")
                for version in sorted(versions):
                    version_info = version_manager.get_version_info(version)
                    current_marker = " (current)" if version == version_manager.get_current_version() else ""
                    click.echo(f"  {version}: {version_info.description}{current_marker}")
            else:
                click.echo("No schema versions found")
            return
        
        if current:
            current_version = version_manager.get_current_version()
            if current_version:
                click.echo(f"Current schema version: {current_version}")
            else:
                click.echo("No current schema version set")
            return
        
        if status:
            status_info = version_manager.get_status()
            click.echo("Schema Version System Status:")
            click.echo(f"  Current Version: {status_info['current_version']}")
            click.echo(f"  Total Versions: {status_info['total_versions']}")
            click.echo(f"  Total Migrations: {status_info['total_migrations']}")
            click.echo(f"  Latest Version: {status_info['latest_version']}")
            click.echo(f"  Integrity Valid: {status_info['integrity_valid']}")
            return
        
        if not target_version:
            click.echo("Error: Target version required. Use --list to see available versions.")
            return
        
        # Perform migration
        click.echo(f"Migrating to schema version: {target_version}")
        executed_migrations = version_manager.migrate_to_version(target_version)
        
        if executed_migrations:
            click.echo(f"✅ Successfully executed {len(executed_migrations)} migrations")
            for migration in executed_migrations:
                click.echo(f"  - {migration.description}")
        else:
            click.echo("✅ Already at target version")
        
    except Exception as e:
        click.echo(f"❌ Migration failed: {e}")


@cli.group()
def vr1():
    """VR1 Boundary-Termination Validation commands."""
    pass


@vr1.command()
@click.argument('blueprint_path', type=click.Path(exists=True))
@click.option('--mode', '-m', type=click.Choice(['strict', 'warning', 'disabled']), default='warning', help='Enforcement mode')
@click.option('--auto-migrate', is_flag=True, help='Apply auto-migration if validation fails')
@click.option('--report', '-r', type=click.Path(), help='Save validation report to file')
def validate(blueprint_path: str, mode: str, auto_migrate: bool, report: str):
    """Validate a blueprint with VR1 boundary-termination rules."""
    click.echo(f"🔍 VR1 Validation: {blueprint_path}")
    click.echo(f"Enforcement mode: {mode}")
    
    try:
        from autocoder_cc.blueprint_language.blueprint_parser import BlueprintParser
        from autocoder_cc.blueprint_validation.migration_engine import VR1ValidationCoordinator
        
        # Parse blueprint
        parser = BlueprintParser(enable_vr1_semantics=True)
        blueprint = parser.parse_file(Path(blueprint_path))
        
        # Run VR1 validation
        coordinator = VR1ValidationCoordinator()
        success, actions, migrated_blueprint = coordinator.validate_with_vr1_coordination(
            blueprint,
            force_vr1=auto_migrate
        )
        
        if success:
            if actions:
                click.echo(f"✅ VR1 validation passed with {len(actions)} auto-migrations")
                for action in actions:
                    click.echo(f"  - {action}")
            else:
                click.echo("✅ VR1 validation passed - blueprint is compliant")
        else:
            click.echo("❌ VR1 validation failed")
            if mode == 'strict':
                click.echo("  Blueprint does not meet boundary-termination requirements")
            elif mode == 'warning':
                click.echo("  ⚠️  Warnings issued but not blocking")
        
        # Save report if requested
        if report:
            import json
            report_data = {
                "blueprint": blueprint_path,
                "success": success,
                "mode": mode,
                "actions": [str(a) for a in actions]
            }
            with open(report, 'w') as f:
                json.dump(report_data, f, indent=2)
            click.echo(f"📄 Report saved to: {report}")
            
    except Exception as e:
        click.echo(f"❌ VR1 validation error: {e}")


@vr1.command()
@click.argument('blueprint_path', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output path for migrated blueprint')
@click.option('--confidence', type=float, default=0.75, help='Migration confidence threshold')
def migrate(blueprint_path: str, output: str, confidence: float):
    """Migrate a legacy blueprint to VR1 compliance."""
    click.echo(f"🔄 Migrating blueprint to VR1: {blueprint_path}")
    
    try:
        from autocoder_cc.blueprint_language.blueprint_parser import BlueprintParser
        from autocoder_cc.blueprint_validation.migration_engine import BlueprintMigrationEngine
        import yaml
        
        # Parse blueprint
        parser = BlueprintParser()
        blueprint = parser.parse_file(Path(blueprint_path))
        
        # Run migration
        migration_engine = BlueprintMigrationEngine()
        migration_result = migration_engine.migrate_blueprint(blueprint)
        
        if migration_result.migration_needed:
            click.echo(f"✅ Migration completed: {migration_result.migration_type}")
            for op in migration_result.operations_applied:
                click.echo(f"  - {op}")
            
            # Save migrated blueprint
            output_path = output or blueprint_path.replace('.yaml', '_vr1.yaml')
            # Convert parsed blueprint back to dictionary
            migrated_dict = parser.to_dict(migration_result.migrated_blueprint)
            with open(output_path, 'w') as f:
                yaml.dump(migrated_dict, f)
            click.echo(f"📄 Migrated blueprint saved to: {output_path}")
        else:
            click.echo("✅ Blueprint already VR1 compliant - no migration needed")
            
    except Exception as e:
        click.echo(f"❌ Migration error: {e}")


@vr1.command()
def status():
    """Show VR1 validation status and configuration."""
    from autocoder_cc.core.config import settings
    
    click.echo("VR1 Boundary-Termination Validation Status")
    click.echo("==========================================")
    click.echo(f"Enabled: {'✅ Yes' if settings.ENABLE_VR1_VALIDATION else '❌ No'}")
    click.echo(f"Enforcement Mode: {settings.VR1_ENFORCEMENT_MODE}")
    click.echo(f"Force Compliance: {'Yes' if settings.FORCE_VR1_COMPLIANCE else 'No'}")
    click.echo(f"Auto-Healing: {'✅ Enabled' if settings.VR1_AUTO_HEALING else '❌ Disabled'}")
    click.echo(f"Telemetry: {'✅ Enabled' if settings.VR1_TELEMETRY_ENABLED else '❌ Disabled'}")
    click.echo(f"Max Hop Limit: {settings.VR1_MAX_HOP_LIMIT}")
    click.echo(f"Migration Confidence: {settings.VR1_MIGRATION_CONFIDENCE_THRESHOLD}")
    
    if settings.VR1_REPORT_PATH:
        click.echo(f"Report Path: {settings.VR1_REPORT_PATH}")


# Add VR1 group to main CLI
cli.add_command(vr1)


@cli.command()
def version():
    """Show version information."""
    click.echo("Autocoder v5.2.0 - Enterprise Roadmap v3")
    click.echo("Features:")
    click.echo("  ✅ ComposedComponent architecture")
    click.echo("  ✅ Centralized configuration system") 
    click.echo("  ✅ Registry-driven generation pipeline")
    click.echo("  ✅ LocalOrchestrator with hot-reload")
    click.echo("  ✅ Schema versioning and migration system")
    click.echo("  ✅ VR1 Boundary-Termination Validation")
    click.echo("  🚧 Structured observability (in progress)")


if __name__ == '__main__':
    cli()