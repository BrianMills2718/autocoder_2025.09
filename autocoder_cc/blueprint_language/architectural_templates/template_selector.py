"""
Template Selector
Selects appropriate architectural templates based on blueprint requirements
"""

import logging
from typing import Dict, Any, List, Tuple
from .messaging.rabbitmq_component_template import get_rabbitmq_template, get_rabbitmq_requirements, get_rabbitmq_env_vars
from .security.secure_compose_template import get_secure_compose_template, get_env_template, validate_no_hardcoded_secrets
from tests.contracts.blueprint_structure_contract import BlueprintContract

logger = logging.getLogger(__name__)

class TemplateSelector:
    """Selects and applies appropriate architectural templates based on blueprint"""
    
    def __init__(self):
        self.templates = {
            "rabbitmq": {
                "template": get_rabbitmq_template,
                "requirements": get_rabbitmq_requirements,
                "env_vars": get_rabbitmq_env_vars
            },
            "secure_compose": {
                "template": get_secure_compose_template,
                "env_template": get_env_template,
                "validator": validate_no_hardcoded_secrets
            }
        }
        logger.info("✅ TemplateSelector initialized with architectural templates")
    
    def select_templates_for_blueprint(self, blueprint: Dict[str, Any]) -> Dict[str, Any]:
        """Select all applicable templates for a blueprint"""
        selected = {
            "component_templates": [],
            "requirements": set(),
            "env_vars": {},
            "compose_template": None,
            "env_template": None,
            "security_validations": []
        }
        
        # Check for messaging requirements
        if self._requires_rabbitmq(blueprint):
            selected["component_templates"].append("rabbitmq")
            selected["requirements"].update(self.templates["rabbitmq"]["requirements"]())
            
            # Add RabbitMQ environment variables for each component
            components = blueprint.get("components", [])
            for component in components:
                if isinstance(component, dict):
                    component_name = component.get("name", "unknown")
                    env_vars = self.templates["rabbitmq"]["env_vars"](component_name)
                    selected["env_vars"].update(env_vars)
        
        # Always use secure compose template
        system_name = blueprint.get("system", {}).get("name", "unknown_system")
        selected["compose_template"] = "secure_compose"
        selected["env_template"] = self.templates["secure_compose"]["env_template"]
        selected["security_validations"].append(self.templates["secure_compose"]["validator"])
        
        logger.info(f"Selected templates for {system_name}: {selected['component_templates']}")
        return selected
    
    def _requires_rabbitmq(self, blueprint: Dict[str, Any]) -> bool:
        """Check if blueprint requires RabbitMQ messaging"""
        # Check infrastructure declarations
        infrastructure = blueprint.get("infrastructure", {})
        if "rabbitmq" in infrastructure:
            logger.info("RabbitMQ required: found in infrastructure")
            return True
        
        # Check for RabbitMQ service in docker-compose (if present)
        if "services" in blueprint:
            services = blueprint["services"]
            if "rabbitmq" in services:
                logger.info("RabbitMQ required: found in services")
                return True
        
        # Check component messaging configurations
        components = BlueprintContract.get_components(blueprint)
        for component in components:
            if isinstance(component, dict):
                messaging = component.get("messaging", {})
                if messaging.get("type") == "rabbitmq":
                    logger.info(f"RabbitMQ required: found in component {component.get('name')}")
                    return True
        
        return False
    
    def get_component_template(self, template_name: str) -> str:
        """Get component template content by name"""
        if template_name not in self.templates:
            raise ValueError(f"Unknown template: {template_name}")
        return self.templates[template_name]["template"]()
    
    def get_compose_template(self, service_name: str, external_port: int, internal_port: int) -> Tuple[str, str]:
        """Get secure docker-compose template and env template"""
        compose_content = get_secure_compose_template(service_name, external_port, internal_port)
        env_content = get_env_template(service_name, external_port, internal_port)
        return compose_content, env_content
    
    def validate_security(self, content: str) -> List[str]:
        """Validate content for security violations"""
        violations = []
        for validator in self.templates["secure_compose"]["validator"]:
            violations.extend(validator(content))
        return violations

def create_template_guidance_prompt(blueprint: Dict[str, Any]) -> str:
    """Create LLM prompt with architectural template guidance"""
    selector = TemplateSelector()
    selected = selector.select_templates_for_blueprint(blueprint)
    
    prompt_parts = [
        "ARCHITECTURAL TEMPLATE GUIDANCE:",
        "You must follow these architectural patterns in your code generation:",
        ""
    ]
    
    # Add component template guidance
    for template_name in selected["component_templates"]:
        if template_name == "rabbitmq":
            prompt_parts.extend([
                "RABBITMQ INTEGRATION REQUIRED:",
                "- Import pika and implement RabbitMQMixin",
                "- Add setup_rabbitmq(), publish_message(), and consume_messages() methods",
                "- Use exchange/queue pattern with proper error handling",
                "- Add pika>=1.3.0 to requirements.txt",
                ""
            ])
    
    # Add security guidance
    prompt_parts.extend([
        "SECURITY REQUIREMENTS:",
        "- NEVER include hardcoded passwords, API keys, or secrets",
        "- Use environment variables: ${VARIABLE_NAME}",
        "- Reference .env file for all secrets",
        "- Use secure connection patterns",
        ""
    ])
    
    # Add requirements guidance
    if selected["requirements"]:
        prompt_parts.extend([
            "REQUIRED DEPENDENCIES:",
            f"Add to requirements.txt: {', '.join(selected['requirements'])}",
            ""
        ])
    
    return "\n".join(prompt_parts)