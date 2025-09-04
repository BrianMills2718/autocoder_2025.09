"""
Build Context Hasher
Comprehensive build context capture for complete reproducibility
"""

import sys
import os
import platform
import json
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Simple logger for testing
def get_logger(name: str):
    """Simple logger for testing"""
    import logging
    return logging.getLogger(name)


@dataclass
class BuildContext:
    """Complete build context for reproducible builds"""
    build_id: str
    timestamp: str
    python_version: str
    platform_info: Dict[str, str]
    environment_variables: Dict[str, str]
    dependency_versions: Dict[str, str]
    llm_configuration: Dict[str, Any]
    tokenizer_info: Dict[str, Any]
    os_architecture: Dict[str, str]
    git_info: Dict[str, str]
    file_hashes: Dict[str, str]
    build_hash: str = ""


class BuildContextHasher:
    """Captures comprehensive build context for reproducible builds"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.project_root = Path(__file__).parent.parent.parent
        
    def capture_build_context(self, build_id: str) -> BuildContext:
        """Capture complete build context"""
        self.logger.info(f"Capturing build context for build_id: {build_id}")
        
        context = BuildContext(
            build_id=build_id,
            timestamp=datetime.now().isoformat(),
            python_version=self._get_python_version(),
            platform_info=self._get_platform_info(),
            environment_variables=self._get_relevant_env_vars(),
            dependency_versions=self._get_dependency_versions(),
            llm_configuration=self._get_llm_configuration(),
            tokenizer_info=self._get_tokenizer_info(),
            os_architecture=self._get_os_architecture(),
            git_info=self._get_git_info(),
            file_hashes=self._get_critical_file_hashes()
        )
        
        # Generate build hash from all context
        context.build_hash = self._generate_build_hash(context)
        
        self.logger.info(f"Build context captured with hash: {context.build_hash}")
        return context
    
    def _get_python_version(self) -> str:
        """Get detailed Python version information"""
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    def _get_platform_info(self) -> Dict[str, str]:
        """Get platform information"""
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_implementation": platform.python_implementation(),
            "python_compiler": platform.python_compiler()
        }
    
    def _get_relevant_env_vars(self) -> Dict[str, str]:
        """Get relevant environment variables for build reproducibility"""
        relevant_vars = [
            "ENVIRONMENT",
            "LOG_LEVEL",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "OPENAI_MODEL",
            "ANTHROPIC_MODEL",
            "OPENAI_TEMPERATURE",
            "ANTHROPIC_TEMPERATURE",
            "OPENAI_MAX_TOKENS",
            "ANTHROPIC_MAX_TOKENS",
            "PYTHON_VERSION",
            "PATH",
            "PYTHONPATH",
            "LANG",
            "LC_ALL",
            "TZ"
        ]
        
        env_vars = {}
        for var in relevant_vars:
            value = os.getenv(var)
            if value is not None:
                # Mask sensitive values
                if "API_KEY" in var or "SECRET" in var or "PASSWORD" in var:
                    env_vars[var] = f"<masked:{len(value)}>"
                else:
                    env_vars[var] = value
        
        return env_vars
    
    def _get_dependency_versions(self) -> Dict[str, str]:
        """Get versions of critical dependencies"""
        dependencies = {}
        
        # Python packages
        try:
            import pkg_resources
            for package in ["openai", "anthropic", "tiktoken", "transformers", "torch", "numpy", "pydantic"]:
                try:
                    version = pkg_resources.get_distribution(package).version
                    dependencies[f"python:{package}"] = version
                except pkg_resources.DistributionNotFound:
                    pass
        except ImportError:
            # Fallback if pkg_resources not available
            import importlib.metadata
            for package in ["openai", "anthropic", "tiktoken", "transformers", "torch", "numpy", "pydantic"]:
                try:
                    version = importlib.metadata.version(package)
                    dependencies[f"python:{package}"] = version
                except importlib.metadata.PackageNotFoundError:
                    pass
        
        # System dependencies
        system_deps = ["git", "docker", "kubectl", "helm"]
        for dep in system_deps:
            try:
                result = subprocess.run([dep, "--version"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # Extract version from output
                    version_line = result.stdout.strip().split('\n')[0]
                    dependencies[f"system:{dep}"] = version_line
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        return dependencies
    
    def _get_llm_configuration(self) -> Dict[str, Any]:
        """Get LLM configuration and sampling parameters"""
        llm_config = {
            "openai": {
                "model": os.getenv("OPENAI_MODEL", "gpt-4"),
                "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.0")),
                "max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", "4096")),
                "top_p": float(os.getenv("OPENAI_TOP_P", "1.0")),
                "frequency_penalty": float(os.getenv("OPENAI_FREQUENCY_PENALTY", "0.0")),
                "presence_penalty": float(os.getenv("OPENAI_PRESENCE_PENALTY", "0.0")),
                "stop": os.getenv("OPENAI_STOP", "null")
            },
            "anthropic": {
                "model": os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
                "temperature": float(os.getenv("ANTHROPIC_TEMPERATURE", "0.0")),
                "max_tokens": int(os.getenv("ANTHROPIC_MAX_TOKENS", "4096")),
                "top_p": float(os.getenv("ANTHROPIC_TOP_P", "1.0")),
                "top_k": int(os.getenv("ANTHROPIC_TOP_K", "0")),
                "stop_sequences": os.getenv("ANTHROPIC_STOP", "null")
            },
            "sampling_seed": os.getenv("LLM_SAMPLING_SEED", "42"),
            "deterministic_mode": os.getenv("LLM_DETERMINISTIC", "true").lower() == "true"
        }
        
        return llm_config
    
    def _get_tokenizer_info(self) -> Dict[str, Any]:
        """Get tokenizer information"""
        tokenizer_info = {}
        
        # OpenAI tokenizer (tiktoken)
        try:
            import tiktoken
            tokenizer_info["tiktoken_version"] = tiktoken.__version__
            
            # Get encoding info for common models
            for model in ["gpt-4", "gpt-3.5-turbo", "text-davinci-003"]:
                try:
                    encoding = tiktoken.encoding_for_model(model)
                    tokenizer_info[f"tiktoken_{model}_encoding"] = encoding.name
                except Exception:
                    pass
        except ImportError:
            pass
        
        # Hugging Face tokenizers
        try:
            import transformers
            tokenizer_info["transformers_version"] = transformers.__version__
            
            # Get tokenizer info for common models
            for model in ["bert-base-uncased", "gpt2", "t5-base"]:
                try:
                    from transformers import AutoTokenizer
                    tokenizer = AutoTokenizer.from_pretrained(model)
                    tokenizer_info[f"hf_{model}_vocab_size"] = tokenizer.vocab_size
                except Exception:
                    pass
        except ImportError:
            pass
        
        return tokenizer_info
    
    def _get_os_architecture(self) -> Dict[str, str]:
        """Get detailed OS architecture information"""
        arch_info = {
            "architecture": platform.architecture()[0],
            "machine": platform.machine(),
            "processor": platform.processor(),
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version()
        }
        
        # Additional Linux-specific information
        if platform.system() == "Linux":
            try:
                # Get kernel version
                result = subprocess.run(["uname", "-r"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    arch_info["kernel_version"] = result.stdout.strip()
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Get distribution info
            try:
                with open("/etc/os-release", "r") as f:
                    for line in f:
                        if line.startswith("NAME="):
                            arch_info["distro_name"] = line.split("=")[1].strip('"')
                        elif line.startswith("VERSION="):
                            arch_info["distro_version"] = line.split("=")[1].strip('"')
            except FileNotFoundError:
                pass
        
        # macOS-specific information
        elif platform.system() == "Darwin":
            try:
                result = subprocess.run(["sw_vers", "-productVersion"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    arch_info["macos_version"] = result.stdout.strip()
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        # Windows-specific information
        elif platform.system() == "Windows":
            arch_info["windows_version"] = platform.win32_ver()[0]
        
        return arch_info
    
    def _get_git_info(self) -> Dict[str, str]:
        """Get git repository information"""
        git_info = {}
        
        try:
            # Get current commit hash
            result = subprocess.run(["git", "rev-parse", "HEAD"], 
                                  capture_output=True, text=True, timeout=5, cwd=self.project_root)
            if result.returncode == 0:
                git_info["commit_hash"] = result.stdout.strip()
            
            # Get current branch
            result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], 
                                  capture_output=True, text=True, timeout=5, cwd=self.project_root)
            if result.returncode == 0:
                git_info["branch"] = result.stdout.strip()
            
            # Get remote origin URL
            result = subprocess.run(["git", "config", "--get", "remote.origin.url"], 
                                  capture_output=True, text=True, timeout=5, cwd=self.project_root)
            if result.returncode == 0:
                git_info["remote_url"] = result.stdout.strip()
            
            # Get last commit timestamp
            result = subprocess.run(["git", "log", "-1", "--format=%ct"], 
                                  capture_output=True, text=True, timeout=5, cwd=self.project_root)
            if result.returncode == 0:
                git_info["last_commit_timestamp"] = result.stdout.strip()
            
            # Check for uncommitted changes
            result = subprocess.run(["git", "status", "--porcelain"], 
                                  capture_output=True, text=True, timeout=5, cwd=self.project_root)
            if result.returncode == 0:
                has_changes = len(result.stdout.strip()) > 0
                git_info["has_uncommitted_changes"] = str(has_changes)
        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return git_info
    
    def _get_critical_file_hashes(self) -> Dict[str, str]:
        """Get hashes of critical files for build reproducibility"""
        critical_files = [
            "CLAUDE.md",
            "pyproject.toml",
            "requirements.txt",
            "schemas/architecture.schema.json",
            "schemas/deployment.schema.json",
            "autocoder_cc/core/config.py",
            "autocoder_cc/components/component_registry.py",
            "autocoder_cc/blueprint_language/system_generator.py",
            "autocoder_cc/validation/schema_validator.py"
        ]
        
        file_hashes = {}
        
        for file_path in critical_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'rb') as f:
                        content = f.read()
                        file_hash = hashlib.sha256(content).hexdigest()
                        file_hashes[file_path] = file_hash
                except Exception as e:
                    file_hashes[file_path] = f"<error:{str(e)}>"
        
        return file_hashes
    
    def _generate_build_hash(self, context: BuildContext) -> str:
        """Generate deterministic build hash from all context"""
        # Create a deterministic representation of the context
        hash_data = {
            "python_version": context.python_version,
            "platform_info": context.platform_info,
            "environment_variables": context.environment_variables,
            "dependency_versions": context.dependency_versions,
            "llm_configuration": context.llm_configuration,
            "tokenizer_info": context.tokenizer_info,
            "os_architecture": context.os_architecture,
            "git_info": context.git_info,
            "file_hashes": context.file_hashes
        }
        
        # Convert to deterministic JSON string
        json_str = json.dumps(hash_data, sort_keys=True, separators=(',', ':'))
        
        # Generate SHA256 hash
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
    
    def save_build_context(self, context: BuildContext, output_path: Path):
        """Save build context to file"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        context_dict = {
            "build_id": context.build_id,
            "timestamp": context.timestamp,
            "python_version": context.python_version,
            "platform_info": context.platform_info,
            "environment_variables": context.environment_variables,
            "dependency_versions": context.dependency_versions,
            "llm_configuration": context.llm_configuration,
            "tokenizer_info": context.tokenizer_info,
            "os_architecture": context.os_architecture,
            "git_info": context.git_info,
            "file_hashes": context.file_hashes,
            "build_hash": context.build_hash
        }
        
        with open(output_path, 'w') as f:
            json.dump(context_dict, f, indent=2, sort_keys=True)
        
        self.logger.info(f"Build context saved to: {output_path}")
    
    def verify_build_reproducibility(self, context1: BuildContext, context2: BuildContext) -> bool:
        """Verify that two build contexts are reproducible"""
        # Compare critical elements for reproducibility
        return (
            context1.python_version == context2.python_version and
            context1.platform_info == context2.platform_info and
            context1.dependency_versions == context2.dependency_versions and
            context1.llm_configuration == context2.llm_configuration and
            context1.tokenizer_info == context2.tokenizer_info and
            context1.os_architecture == context2.os_architecture and
            context1.file_hashes == context2.file_hashes and
            context1.build_hash == context2.build_hash
        )


def verify_complete_build_context():
    """Verify that complete build context can be captured"""
    print("Verifying complete build context capture...")
    
    hasher = BuildContextHasher()
    context = hasher.capture_build_context("test_build_001")
    
    print(f"✅ Build ID: {context.build_id}")
    print(f"✅ Build Hash: {context.build_hash}")
    print(f"✅ Python Version: {context.python_version}")
    print(f"✅ Platform: {context.platform_info['system']} {context.platform_info['release']}")
    print(f"✅ Dependencies: {len(context.dependency_versions)} captured")
    print(f"✅ LLM Config: {len(context.llm_configuration)} parameters")
    print(f"✅ Tokenizer Info: {len(context.tokenizer_info)} entries")
    print(f"✅ OS Architecture: {len(context.os_architecture)} properties")
    print(f"✅ Git Info: {len(context.git_info)} properties")
    print(f"✅ File Hashes: {len(context.file_hashes)} critical files")
    
    # Test reproducibility
    context2 = hasher.capture_build_context("test_build_002")
    is_reproducible = hasher.verify_build_reproducibility(context, context2)
    print(f"✅ Reproducibility Test: {'PASS' if is_reproducible else 'FAIL'}")
    
    # Save context
    output_path = Path("build_context_test.json")
    hasher.save_build_context(context, output_path)
    print(f"✅ Build context saved to: {output_path}")
    
    return context


if __name__ == "__main__":
    verify_complete_build_context()