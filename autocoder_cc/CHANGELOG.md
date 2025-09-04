# Changelog

All notable changes to Autocoder V5.2 will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [5.2.0] - 2025-07-13

### Added
- FastAPI-native architecture with SystemExecutionHarness integration
- Enhanced database integration with automatic driver detection
- 4-tier validation pipeline (Framework → Component Logic → Integration → Semantic)
- AST-based code analysis replacing string matching
- ComponentRegistry for centralized validation and instantiation
- Standalone capability classes (RetryHandler, CircuitBreaker, etc.)
- Dynamic component loading from manifests
- Schema framework with Pydantic models and runtime validation
- Production-ready deployment configurations (Docker, K8s, Helm)

### Changed
- Migrated from Flask to FastAPI exclusively
- Replaced hardcoded configuration with environment-driven settings
- Updated documentation with current architecture and examples
- Improved error handling and graceful shutdown mechanisms

### Removed
- Flask dependencies and references
- Hardcoded port and connection string values
- Legacy component base classes
- String-based placeholder detection

### Fixed
- Pydantic validation errors in generator settings
- ComponentTestResult and ParsedBinding attribute compatibility
- TaskGroup exceptions in generated systems
- Import errors in standalone component generation

## [Unreleased]

### Planned
- Phase 1: LocalOrchestrator with hot-reload and debug hooks
- Phase 1: VersionedSchema with automated migration support
- Enhanced observability and monitoring features
- Multi-language code generation support