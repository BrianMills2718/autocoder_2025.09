#!/usr/bin/env python3
"""
Comprehensive MkDocs Configuration Validator
Validates MkDocs configuration syntax, structure, file references, and compatibility
"""

import os
import sys
import yaml
import json
import subprocess
import tempfile
import shutil
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from urllib.parse import urlparse
import re
import logging


@dataclass
class ValidationIssue:
    """Represents a validation issue"""
    severity: str  # 'error', 'warning', 'info'
    category: str  # 'syntax', 'structure', 'references', 'plugins', 'build'
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Results of validation process"""
    is_valid: bool
    issues: List[ValidationIssue]
    config_data: Optional[Dict[str, Any]] = None
    
    @property
    def error_count(self) -> int:
        return len([i for i in self.issues if i.severity == 'error'])
    
    @property
    def warning_count(self) -> int:
        return len([i for i in self.issues if i.severity == 'warning'])
    
    @property
    def info_count(self) -> int:
        return len([i for i in self.issues if i.severity == 'info'])


class MkDocsConfigValidator:
    """Comprehensive MkDocs configuration validator"""
    
    REQUIRED_FIELDS = {
        'site_name': str,
        'docs_dir': str,
    }
    
    RECOMMENDED_FIELDS = {
        'site_description': str,
        'site_author': str,
        'site_url': str,
        'repo_url': str,
        'repo_name': str,
        'theme': dict,
        'nav': list,
        'plugins': list,
        'markdown_extensions': list
    }
    
    VALID_THEMES = {
        'mkdocs',
        'readthedocs', 
        'material',
        'bootstrap',
        'bootswatch',
        'ivory',
        'windmill',
        'gitiles'
    }
    
    COMMON_PLUGINS = {
        'search',
        'minify',
        'git-revision-date',
        'git-revision-date-localized',
        'awesome-pages',
        'exclude',
        'macros',
        'redirects',
        'tags',
        'social',
        'blog',
        'rss'
    }
    
    MARKDOWN_EXTENSIONS = {
        'abbr',
        'admonition', 
        'attr_list',
        'codehilite',
        'def_list',
        'footnotes',
        'md_in_html',
        'meta',
        'sane_lists',
        'smarty',
        'tables',
        'toc',
        'wikilinks',
        'pymdownx.arithmatex',
        'pymdownx.betterem',
        'pymdownx.caret',
        'pymdownx.details',
        'pymdownx.emoji',
        'pymdownx.highlight',
        'pymdownx.inlinehilite',
        'pymdownx.keys',
        'pymdownx.magiclink',
        'pymdownx.mark',
        'pymdownx.smartsymbols',
        'pymdownx.superfences',
        'pymdownx.tabbed',
        'pymdownx.tasklist',
        'pymdownx.tilde'
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self.issues: List[ValidationIssue] = []
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for validation process"""
        logger = logging.getLogger('mkdocs_validator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def validate_config(self, config_path: str, strict: bool = False) -> ValidationResult:
        """
        Comprehensive MkDocs configuration validation
        
        Args:
            config_path: Path to mkdocs.yml configuration file
            strict: Enable strict validation mode
            
        Returns:
            ValidationResult with all validation issues
        """
        self.issues = []
        self.logger.info(f"Starting MkDocs configuration validation: {config_path}")
        
        try:
            # Step 1: Validate file existence and accessibility
            self._validate_file_access(config_path)
            
            # Step 2: Validate YAML syntax
            config_data = self._validate_yaml_syntax(config_path)
            if not config_data:
                return ValidationResult(is_valid=False, issues=self.issues)
            
            # Step 3: Validate configuration structure
            self._validate_config_structure(config_data, strict)
            
            # Step 4: Validate file references
            config_dir = Path(config_path).parent
            self._validate_file_references(config_data, config_dir)
            
            # Step 5: Validate plugin compatibility
            self._validate_plugin_configuration(config_data)
            
            # Step 6: Validate theme configuration
            self._validate_theme_configuration(config_data)
            
            # Step 7: Validate navigation structure
            self._validate_navigation_structure(config_data, config_dir)
            
            # Step 8: Validate markdown extensions
            self._validate_markdown_extensions(config_data)
            
            # Step 9: Test build if requested
            if strict:
                self._test_build_process(config_path)
            
            # Determine overall validation result
            has_errors = any(issue.severity == 'error' for issue in self.issues)
            is_valid = not has_errors
            
            self.logger.info(f"Validation completed. Valid: {is_valid}, "
                           f"Errors: {self.error_count}, Warnings: {self.warning_count}")
            
            return ValidationResult(
                is_valid=is_valid,
                issues=self.issues,
                config_data=config_data
            )
            
        except Exception as e:
            self.issues.append(ValidationIssue(
                severity='error',
                category='general',
                message=f"Unexpected error during validation: {e}",
                file_path=config_path
            ))
            
            return ValidationResult(is_valid=False, issues=self.issues)
    
    def _validate_file_access(self, config_path: str):
        """Validate file exists and is accessible"""
        config_file = Path(config_path)
        
        if not config_file.exists():
            self.issues.append(ValidationIssue(
                severity='error',
                category='syntax',
                message=f"Configuration file not found: {config_path}",
                file_path=config_path,
                suggestion="Ensure the mkdocs.yml file exists in the specified location"
            ))
            return
        
        if not config_file.is_file():
            self.issues.append(ValidationIssue(
                severity='error',
                category='syntax',
                message=f"Path is not a file: {config_path}",
                file_path=config_path
            ))
            return
        
        if not os.access(config_file, os.R_OK):
            self.issues.append(ValidationIssue(
                severity='error',
                category='syntax',
                message=f"No read permission for file: {config_path}",
                file_path=config_path
            ))
    
    def _validate_yaml_syntax(self, config_path: str) -> Optional[Dict[str, Any]]:
        """Validate YAML syntax and structure"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            if config_data is None:
                self.issues.append(ValidationIssue(
                    severity='error',
                    category='syntax',
                    message="Configuration file is empty or contains only comments",
                    file_path=config_path,
                    suggestion="Add required configuration fields like site_name and docs_dir"
                ))
                return None
            
            if not isinstance(config_data, dict):
                self.issues.append(ValidationIssue(
                    severity='error',
                    category='syntax',
                    message="Configuration must be a YAML dictionary",
                    file_path=config_path,
                    suggestion="Ensure the YAML file contains key-value pairs at the root level"
                ))
                return None
            
            self.logger.info("YAML syntax validation passed")
            return config_data
            
        except yaml.YAMLError as e:
            error_line = getattr(e, 'problem_mark', None)
            line_number = error_line.line + 1 if error_line else None
            
            self.issues.append(ValidationIssue(
                severity='error',
                category='syntax',
                message=f"YAML syntax error: {e}",
                file_path=config_path,
                line_number=line_number,
                suggestion="Check YAML syntax using a YAML validator"
            ))
            return None
            
        except UnicodeDecodeError as e:
            self.issues.append(ValidationIssue(
                severity='error',
                category='syntax',
                message=f"File encoding error: {e}",
                file_path=config_path,
                suggestion="Ensure file is saved with UTF-8 encoding"
            ))
            return None
    
    def _validate_config_structure(self, config_data: Dict[str, Any], strict: bool):
        """Validate configuration structure and required fields"""
        # Check required fields
        for field, expected_type in self.REQUIRED_FIELDS.items():
            if field not in config_data:
                self.issues.append(ValidationIssue(
                    severity='error',
                    category='structure',
                    message=f"Required field missing: {field}",
                    suggestion=f"Add '{field}' to your configuration"
                ))
            elif not isinstance(config_data[field], expected_type):
                self.issues.append(ValidationIssue(
                    severity='error',
                    category='structure',
                    message=f"Field '{field}' must be of type {expected_type.__name__}",
                    suggestion=f"Change {field} to a {expected_type.__name__} value"
                ))
        
        # Check recommended fields (warnings in strict mode)
        if strict:
            for field, expected_type in self.RECOMMENDED_FIELDS.items():
                if field not in config_data:
                    self.issues.append(ValidationIssue(
                        severity='warning',
                        category='structure',
                        message=f"Recommended field missing: {field}",
                        suggestion=f"Consider adding '{field}' to improve documentation quality"
                    ))
                elif not isinstance(config_data[field], expected_type):
                    self.issues.append(ValidationIssue(
                        severity='warning',
                        category='structure',
                        message=f"Field '{field}' should be of type {expected_type.__name__}",
                        suggestion=f"Change {field} to a {expected_type.__name__} value"
                    ))
        
        # Validate site_url format if present
        if 'site_url' in config_data:
            site_url = config_data['site_url']
            if not self._is_valid_url(site_url):
                self.issues.append(ValidationIssue(
                    severity='warning',
                    category='structure',
                    message=f"site_url appears to be invalid: {site_url}",
                    suggestion="Ensure site_url is a complete, valid URL"
                ))
        
        # Validate repo_url format if present
        if 'repo_url' in config_data:
            repo_url = config_data['repo_url']
            if not self._is_valid_url(repo_url):
                self.issues.append(ValidationIssue(
                    severity='warning',
                    category='structure',
                    message=f"repo_url appears to be invalid: {repo_url}",
                    suggestion="Ensure repo_url is a valid repository URL"
                ))
    
    def _validate_file_references(self, config_data: Dict[str, Any], config_dir: Path):
        """Validate all file and directory references in configuration"""
        # Validate docs_dir
        if 'docs_dir' in config_data:
            docs_dir = config_dir / config_data['docs_dir']
            if not docs_dir.exists():
                self.issues.append(ValidationIssue(
                    severity='error',
                    category='references',
                    message=f"Documentation directory not found: {config_data['docs_dir']}",
                    suggestion=f"Create directory {docs_dir} or update docs_dir in configuration"
                ))
            elif not docs_dir.is_dir():
                self.issues.append(ValidationIssue(
                    severity='error',
                    category='references',
                    message=f"docs_dir path is not a directory: {config_data['docs_dir']}",
                    suggestion="Ensure docs_dir points to a directory, not a file"
                ))
            else:
                # Check if docs directory has any markdown files
                md_files = list(docs_dir.rglob('*.md'))
                if not md_files:
                    self.issues.append(ValidationIssue(
                        severity='warning',
                        category='references',
                        message=f"No markdown files found in docs directory: {config_data['docs_dir']}",
                        suggestion="Add some .md files to your documentation directory"
                    ))
        
        # Validate site_dir (if specified)
        if 'site_dir' in config_data:
            site_dir = config_dir / config_data['site_dir']
            docs_dir = config_dir / config_data.get('docs_dir', 'docs')
            
            # Check if site_dir is inside docs_dir (problematic)
            try:
                site_dir.resolve().relative_to(docs_dir.resolve())
                self.issues.append(ValidationIssue(
                    severity='error',
                    category='references',
                    message="site_dir cannot be inside docs_dir",
                    suggestion="Move site_dir outside the documentation source directory"
                ))
            except ValueError:
                pass  # site_dir is not inside docs_dir, which is good
        
        # Validate navigation file references
        self._validate_nav_file_references(config_data, config_dir)
        
        # Validate theme-specific file references
        self._validate_theme_file_references(config_data, config_dir)
    
    def _validate_nav_file_references(self, config_data: Dict[str, Any], config_dir: Path):
        """Validate file references in navigation structure"""
        if 'nav' not in config_data:
            return
        
        docs_dir = config_dir / config_data.get('docs_dir', 'docs')
        
        def check_nav_item(item, path_prefix=""):
            if isinstance(item, dict):
                for title, content in item.items():
                    if isinstance(content, str):
                        # File reference
                        file_path = docs_dir / content
                        if not file_path.exists():
                            self.issues.append(ValidationIssue(
                                severity='error',
                                category='references',
                                message=f"Navigation references missing file: {content}",
                                suggestion=f"Create file {file_path} or remove from navigation"
                            ))
                    elif isinstance(content, list):
                        # Nested navigation
                        for sub_item in content:
                            check_nav_item(sub_item, f"{path_prefix}/{title}")
            elif isinstance(item, str):
                # Direct file reference
                file_path = docs_dir / item
                if not file_path.exists():
                    self.issues.append(ValidationIssue(
                        severity='error',
                        category='references',
                        message=f"Navigation references missing file: {item}",
                        suggestion=f"Create file {file_path} or remove from navigation"
                    ))
        
        for nav_item in config_data['nav']:
            check_nav_item(nav_item)
    
    def _validate_theme_file_references(self, config_data: Dict[str, Any], config_dir: Path):
        """Validate theme-specific file references"""
        if 'theme' not in config_data:
            return
        
        theme_config = config_data['theme']
        if not isinstance(theme_config, dict):
            return
        
        # Check custom_dir if specified
        if 'custom_dir' in theme_config:
            custom_dir = config_dir / theme_config['custom_dir']
            if not custom_dir.exists():
                self.issues.append(ValidationIssue(
                    severity='error',
                    category='references',
                    message=f"Theme custom_dir not found: {theme_config['custom_dir']}",
                    suggestion=f"Create directory {custom_dir} or remove custom_dir from theme config"
                ))
            elif not custom_dir.is_dir():
                self.issues.append(ValidationIssue(
                    severity='error',
                    category='references',
                    message=f"Theme custom_dir is not a directory: {theme_config['custom_dir']}",
                    suggestion="Ensure custom_dir points to a directory"
                ))
        
        # Check favicon if specified
        if 'favicon' in theme_config:
            favicon_path = config_dir / config_data.get('docs_dir', 'docs') / theme_config['favicon']
            if not favicon_path.exists():
                self.issues.append(ValidationIssue(
                    severity='warning',
                    category='references',
                    message=f"Favicon file not found: {theme_config['favicon']}",
                    suggestion=f"Add favicon file {favicon_path} or remove favicon from theme config"
                ))
        
        # Check logo if specified
        if 'logo' in theme_config:
            logo_path = config_dir / config_data.get('docs_dir', 'docs') / theme_config['logo']
            if not logo_path.exists():
                self.issues.append(ValidationIssue(
                    severity='warning',
                    category='references',
                    message=f"Logo file not found: {theme_config['logo']}",
                    suggestion=f"Add logo file {logo_path} or remove logo from theme config"
                ))
    
    def _validate_plugin_configuration(self, config_data: Dict[str, Any]):
        """Validate plugin configuration and compatibility"""
        if 'plugins' not in config_data:
            return
        
        plugins = config_data['plugins']
        if not isinstance(plugins, list):
            self.issues.append(ValidationIssue(
                severity='error',
                category='plugins',
                message="plugins must be a list",
                suggestion="Change plugins to a list format: plugins: [search, ...]"
            ))
            return
        
        plugin_names = set()
        
        for plugin in plugins:
            if isinstance(plugin, str):
                plugin_name = plugin
                plugin_config = {}
            elif isinstance(plugin, dict):
                if len(plugin) != 1:
                    self.issues.append(ValidationIssue(
                        severity='error',
                        category='plugins',
                        message=f"Plugin configuration must have exactly one key: {plugin}",
                        suggestion="Each plugin should be either a string or a dict with one key"
                    ))
                    continue
                plugin_name = list(plugin.keys())[0]
                plugin_config = plugin[plugin_name] or {}
            else:
                self.issues.append(ValidationIssue(
                    severity='error',
                    category='plugins',
                    message=f"Invalid plugin configuration: {plugin}",
                    suggestion="Plugins must be strings or single-key dictionaries"
                ))
                continue
            
            # Check for duplicate plugins
            if plugin_name in plugin_names:
                self.issues.append(ValidationIssue(
                    severity='warning',
                    category='plugins',
                    message=f"Duplicate plugin: {plugin_name}",
                    suggestion="Remove duplicate plugin entries"
                ))
            plugin_names.add(plugin_name)
            
            # Validate plugin name
            if plugin_name not in self.COMMON_PLUGINS:
                self.issues.append(ValidationIssue(
                    severity='info',
                    category='plugins',
                    message=f"Unknown or custom plugin: {plugin_name}",
                    suggestion="Ensure the plugin is installed and properly configured"
                ))
            
            # Validate plugin-specific configurations
            self._validate_specific_plugin_config(plugin_name, plugin_config)
    
    def _validate_specific_plugin_config(self, plugin_name: str, plugin_config: Dict[str, Any]):
        """Validate configuration for specific plugins"""
        if plugin_name == 'search':
            if 'lang' in plugin_config:
                # Validate language codes
                valid_langs = ['en', 'es', 'fr', 'de', 'ja', 'zh', 'ru', 'pt', 'it']
                langs = plugin_config['lang']
                if isinstance(langs, list):
                    for lang in langs:
                        if lang not in valid_langs:
                            self.issues.append(ValidationIssue(
                                severity='info',
                                category='plugins',
                                message=f"Unknown search language: {lang}",
                                suggestion="Check if the language is supported by the search plugin"
                            ))
        
        elif plugin_name == 'minify':
            if 'minify_html' in plugin_config and not isinstance(plugin_config['minify_html'], bool):
                self.issues.append(ValidationIssue(
                    severity='warning',
                    category='plugins',
                    message="minify_html should be a boolean value",
                    suggestion="Set minify_html to true or false"
                ))
    
    def _validate_theme_configuration(self, config_data: Dict[str, Any]):
        """Validate theme configuration"""
        if 'theme' not in config_data:
            self.issues.append(ValidationIssue(
                severity='warning',
                category='structure',
                message="No theme specified, using default",
                suggestion="Specify a theme explicitly for better control"
            ))
            return
        
        theme_config = config_data['theme']
        
        if isinstance(theme_config, str):
            theme_name = theme_config
            theme_options = {}
        elif isinstance(theme_config, dict):
            theme_name = theme_config.get('name')
            theme_options = {k: v for k, v in theme_config.items() if k != 'name'}
        else:
            self.issues.append(ValidationIssue(
                severity='error',
                category='structure',
                message="theme must be a string or dictionary",
                suggestion="Use format: theme: material or theme: {name: material, ...}"
            ))
            return
        
        if not theme_name:
            self.issues.append(ValidationIssue(
                severity='error',
                category='structure',
                message="Theme name not specified",
                suggestion="Add 'name' field to theme configuration"
            ))
            return
        
        if theme_name not in self.VALID_THEMES:
            self.issues.append(ValidationIssue(
                severity='info',
                category='structure',
                message=f"Unknown or custom theme: {theme_name}",
                suggestion="Ensure the theme is installed and available"
            ))
        
        # Validate Material theme specific options
        if theme_name == 'material':
            self._validate_material_theme_config(theme_options)
    
    def _validate_material_theme_config(self, theme_options: Dict[str, Any]):
        """Validate Material theme specific configuration"""
        if 'palette' in theme_options:
            palette = theme_options['palette']
            if isinstance(palette, dict):
                # Single palette
                self._validate_material_palette(palette)
            elif isinstance(palette, list):
                # Multiple palettes
                for i, p in enumerate(palette):
                    if not isinstance(p, dict):
                        self.issues.append(ValidationIssue(
                            severity='error',
                            category='structure',
                            message=f"Palette {i} must be a dictionary",
                            suggestion="Each palette entry should be a dictionary with scheme, primary, etc."
                        ))
                    else:
                        self._validate_material_palette(p, f"palette[{i}]")
        
        if 'features' in theme_options:
            features = theme_options['features']
            if not isinstance(features, list):
                self.issues.append(ValidationIssue(
                    severity='error',
                    category='structure',
                    message="theme features must be a list",
                    suggestion="Change features to a list: features: [navigation.tabs, ...]"
                ))
    
    def _validate_material_palette(self, palette: Dict[str, Any], context: str = "palette"):
        """Validate Material theme palette configuration"""
        valid_schemes = ['default', 'slate']
        valid_colors = [
            'red', 'pink', 'purple', 'deep-purple', 'indigo', 'blue', 
            'light-blue', 'cyan', 'teal', 'green', 'light-green', 
            'lime', 'yellow', 'amber', 'orange', 'deep-orange', 
            'brown', 'grey', 'blue-grey', 'black', 'white'
        ]
        
        if 'scheme' in palette and palette['scheme'] not in valid_schemes:
            self.issues.append(ValidationIssue(
                severity='warning',
                category='structure',
                message=f"{context}: Unknown color scheme '{palette['scheme']}'",
                suggestion=f"Use one of: {', '.join(valid_schemes)}"
            ))
        
        if 'primary' in palette and palette['primary'] not in valid_colors:
            self.issues.append(ValidationIssue(
                severity='warning',
                category='structure',
                message=f"{context}: Unknown primary color '{palette['primary']}'",
                suggestion=f"Use one of the Material Design colors"
            ))
        
        if 'accent' in palette and palette['accent'] not in valid_colors:
            self.issues.append(ValidationIssue(
                severity='warning',
                category='structure',
                message=f"{context}: Unknown accent color '{palette['accent']}'",
                suggestion=f"Use one of the Material Design colors"
            ))
    
    def _validate_navigation_structure(self, config_data: Dict[str, Any], config_dir: Path):
        """Validate navigation structure and logic"""
        if 'nav' not in config_data:
            # Check if there's an index file in docs
            docs_dir = config_dir / config_data.get('docs_dir', 'docs')
            index_files = ['index.md', 'README.md']
            
            has_index = any((docs_dir / index_file).exists() for index_file in index_files)
            if not has_index:
                self.issues.append(ValidationIssue(
                    severity='warning',
                    category='structure',
                    message="No navigation specified and no index.md or README.md found",
                    suggestion="Add navigation or create an index.md file"
                ))
            return
        
        nav = config_data['nav']
        if not isinstance(nav, list):
            self.issues.append(ValidationIssue(
                severity='error',
                category='structure',
                message="Navigation must be a list",
                suggestion="Change nav to a list format"
            ))
            return
        
        if not nav:
            self.issues.append(ValidationIssue(
                severity='warning',
                category='structure',
                message="Navigation is empty",
                suggestion="Add navigation entries or remove nav to use automatic navigation"
            ))
            return
        
        # Check navigation depth and structure
        self._check_nav_depth(nav)
        
        # Check for duplicate navigation entries
        self._check_nav_duplicates(nav)
    
    def _check_nav_depth(self, nav: List, current_depth: int = 1, max_depth: int = 4):
        """Check navigation depth and warn if too deep"""
        for item in nav:
            if isinstance(item, dict):
                for title, content in item.items():
                    if isinstance(content, list):
                        if current_depth >= max_depth:
                            self.issues.append(ValidationIssue(
                                severity='warning',
                                category='structure',
                                message=f"Navigation is very deep (level {current_depth + 1}) at '{title}'",
                                suggestion="Consider flattening navigation structure for better usability"
                            ))
                        else:
                            self._check_nav_depth(content, current_depth + 1, max_depth)
    
    def _check_nav_duplicates(self, nav: List, seen_titles: Optional[set] = None, path: str = ""):
        """Check for duplicate navigation titles"""
        if seen_titles is None:
            seen_titles = set()
        
        for item in nav:
            if isinstance(item, dict):
                for title, content in item.items():
                    current_path = f"{path}/{title}" if path else title
                    
                    if title in seen_titles:
                        self.issues.append(ValidationIssue(
                            severity='warning',
                            category='structure',
                            message=f"Duplicate navigation title: '{title}'",
                            suggestion="Use unique titles for navigation entries"
                        ))
                    seen_titles.add(title)
                    
                    if isinstance(content, list):
                        self._check_nav_duplicates(content, seen_titles, current_path)
    
    def _validate_markdown_extensions(self, config_data: Dict[str, Any]):
        """Validate markdown extensions configuration"""
        if 'markdown_extensions' not in config_data:
            return
        
        extensions = config_data['markdown_extensions']
        if not isinstance(extensions, list):
            self.issues.append(ValidationIssue(
                severity='error',
                category='structure',
                message="markdown_extensions must be a list",
                suggestion="Change to list format: markdown_extensions: [toc, tables, ...]"
            ))
            return
        
        for ext in extensions:
            if isinstance(ext, str):
                ext_name = ext
                ext_config = {}
            elif isinstance(ext, dict):
                if len(ext) != 1:
                    self.issues.append(ValidationIssue(
                        severity='error',
                        category='structure',
                        message=f"Extension configuration must have exactly one key: {ext}",
                        suggestion="Each extension should be a string or single-key dictionary"
                    ))
                    continue
                ext_name = list(ext.keys())[0]
                ext_config = ext[ext_name] or {}
            else:
                self.issues.append(ValidationIssue(
                    severity='error',
                    category='structure',
                    message=f"Invalid extension configuration: {ext}",
                    suggestion="Extensions must be strings or single-key dictionaries"
                ))
                continue
            
            if ext_name not in self.MARKDOWN_EXTENSIONS:
                self.issues.append(ValidationIssue(
                    severity='info',
                    category='structure',
                    message=f"Unknown or custom markdown extension: {ext_name}",
                    suggestion="Ensure the extension is installed and available"
                ))
    
    def _test_build_process(self, config_path: str):
        """Test actual MkDocs build process"""
        try:
            # Create temporary directory for build test
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_config = Path(temp_dir) / "mkdocs.yml"
                shutil.copy2(config_path, temp_config)
                
                # Copy docs directory if it exists
                config_dir = Path(config_path).parent
                with open(config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                docs_dir_name = config_data.get('docs_dir', 'docs')
                source_docs = config_dir / docs_dir_name
                
                if source_docs.exists():
                    target_docs = Path(temp_dir) / docs_dir_name
                    shutil.copytree(source_docs, target_docs)
                
                # Run mkdocs build
                result = subprocess.run([
                    'mkdocs', 'build', 
                    '--config-file', str(temp_config),
                    '--site-dir', str(Path(temp_dir) / 'site'),
                    '--strict'
                ], capture_output=True, text=True, cwd=temp_dir, timeout=120)
                
                if result.returncode != 0:
                    self.issues.append(ValidationIssue(
                        severity='error',
                        category='build',
                        message=f"MkDocs build failed: {result.stderr}",
                        suggestion="Fix the build errors reported by MkDocs"
                    ))
                else:
                    self.issues.append(ValidationIssue(
                        severity='info',
                        category='build',
                        message="MkDocs build test passed successfully"
                    ))
                    
        except subprocess.TimeoutExpired:
            self.issues.append(ValidationIssue(
                severity='error',
                category='build',
                message="MkDocs build test timed out",
                suggestion="Check for configuration issues that might cause slow builds"
            ))
        except FileNotFoundError:
            self.issues.append(ValidationIssue(
                severity='warning',
                category='build',
                message="MkDocs not found, skipping build test",
                suggestion="Install MkDocs to enable build testing: pip install mkdocs"
            ))
        except Exception as e:
            self.issues.append(ValidationIssue(
                severity='warning',
                category='build',
                message=f"Build test failed: {e}",
                suggestion="Check MkDocs installation and configuration"
            ))
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @property
    def error_count(self) -> int:
        return len([i for i in self.issues if i.severity == 'error'])
    
    @property
    def warning_count(self) -> int:
        return len([i for i in self.issues if i.severity == 'warning'])
    
    @property
    def info_count(self) -> int:
        return len([i for i in self.issues if i.severity == 'info'])


def main():
    """CLI interface for MkDocs configuration validation"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate MkDocs configuration')
    parser.add_argument('config_file', help='Path to mkdocs.yml file')
    parser.add_argument('--strict', action='store_true', 
                       help='Enable strict validation mode')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                       help='Output format')
    parser.add_argument('--build-test', action='store_true',
                       help='Test actual MkDocs build process')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Create validator and run validation
    validator = MkDocsConfigValidator()
    
    # Override strict mode if build-test is requested
    strict_mode = args.strict or args.build_test
    
    result = validator.validate_config(args.config_file, strict_mode)
    
    # Output results
    if args.format == 'json':
        output = {
            'is_valid': result.is_valid,
            'error_count': result.error_count,
            'warning_count': result.warning_count,
            'info_count': result.info_count,
            'issues': [asdict(issue) for issue in result.issues],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        print(json.dumps(output, indent=2))
    else:
        # Text output
        print(f"MkDocs Configuration Validation Results")
        print(f"======================================")
        print(f"File: {args.config_file}")
        print(f"Valid: {result.is_valid}")
        print(f"Errors: {result.error_count}")
        print(f"Warnings: {result.warning_count}")
        print(f"Info: {result.info_count}")
        print()
        
        if result.issues:
            for issue in result.issues:
                severity_symbol = {'error': '❌', 'warning': '⚠️', 'info': 'ℹ️'}
                print(f"{severity_symbol.get(issue.severity, '•')} {issue.severity.upper()}: {issue.message}")
                if issue.file_path and issue.line_number:
                    print(f"   Location: {issue.file_path}:{issue.line_number}")
                elif issue.file_path:
                    print(f"   File: {issue.file_path}")
                if issue.suggestion:
                    print(f"   Suggestion: {issue.suggestion}")
                print()
        else:
            print("✅ No issues found!")
    
    # Exit with appropriate code
    sys.exit(0 if result.is_valid else 1)


if __name__ == "__main__":
    main()