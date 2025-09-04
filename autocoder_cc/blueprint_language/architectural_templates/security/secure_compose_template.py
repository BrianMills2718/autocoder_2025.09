"""
Secure Docker Compose Template
Prevents hardcoded secrets and enforces security best practices
"""

SECURE_COMPOSE_TEMPLATE = '''
# Security-Aware Docker Compose Template
# NEVER include hardcoded passwords, secrets, or API keys

version: '3.8'

services:
  {service_name}:
    build: .
    ports:
      - "{external_port}:{internal_port}"
    environment:
      # Database configuration using environment variables
      - DB_HOST=${{DB_HOST}}
      - DB_PORT=${{DB_PORT}}
      - DB_NAME=${{DB_NAME}}
      - DB_USER=${{DB_USER}}
      - DB_PASSWORD=${{DB_PASSWORD}}  # MUST be set in .env file
      - DATABASE_URL=${{DATABASE_URL}}
      
      # Redis configuration using environment variables  
      - REDIS_HOST=${{REDIS_HOST}}
      - REDIS_PORT=${{REDIS_PORT}}
      - REDIS_PASSWORD=${{REDIS_PASSWORD}}  # MUST be set in .env file
      - REDIS_URL=${{REDIS_URL}}
      
      # RabbitMQ configuration using environment variables
      - RABBITMQ_HOST=${{RABBITMQ_HOST}}
      - RABBITMQ_PORT=${{RABBITMQ_PORT}}
      - RABBITMQ_USER=${{RABBITMQ_USER}}
      - RABBITMQ_PASSWORD=${{RABBITMQ_PASSWORD}}  # MUST be set in .env file
      - RABBITMQ_URL=${{RABBITMQ_URL}}
      
      # API configuration
      - API_SECRET_KEY=${{API_SECRET_KEY}}  # MUST be set in .env file
      - JWT_SECRET=${{JWT_SECRET}}  # MUST be set in .env file
      - ENVIRONMENT=${{ENVIRONMENT}}
      
    env_file:
      - .env  # All secrets MUST be in .env file
    volumes:
      - ./config:/app/config:ro
      - ./logs:/app/logs
    depends_on:
      - postgres
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:{internal_port}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    networks:
      - {service_name}-network

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=${{DB_NAME}}
      - POSTGRES_USER=${{DB_USER}}
      - POSTGRES_PASSWORD=${{DB_PASSWORD}}  # From .env file
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${{DB_USER}}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - {service_name}-network

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass "${{REDIS_PASSWORD}}"  # From .env file
    environment:
      - REDIS_PASSWORD=${{REDIS_PASSWORD}}  # From .env file
    volumes:
      - redis_data:/data
    healthcheck:
      # Use environment variable, never hardcode password
      test: ["CMD", "redis-cli", "-a", "${{REDIS_PASSWORD}}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - {service_name}-network

  rabbitmq:
    image: rabbitmq:3-management
    environment:
      - RABBITMQ_DEFAULT_USER=${{RABBITMQ_USER}}  # From .env file
      - RABBITMQ_DEFAULT_PASS=${{RABBITMQ_PASSWORD}}  # From .env file
    ports:
      - "5672:5672"
      - "15672:15672"
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "-q", "ping"]
      interval: 30s
      timeout: 30s
      retries: 3
    restart: unless-stopped
    networks:
      - {service_name}-network

volumes:
  postgres_data:
  redis_data:
  rabbitmq_data:

networks:
  {service_name}-network:
    driver: bridge
'''

REQUIRED_ENV_TEMPLATE = '''
# .env file template - NEVER commit this file to git
# Copy to .env and fill in actual values

# Database Configuration
DB_HOST=postgres
DB_PORT=5432
DB_NAME={service_name}_db
DB_USER=postgres
DB_PASSWORD=CHANGE_ME_SECURE_PASSWORD_HERE
DATABASE_URL=postgresql://${{DB_USER}}:${{DB_PASSWORD}}@${{DB_HOST}}:${{DB_PORT}}/${{DB_NAME}}

# Redis Configuration  
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=CHANGE_ME_SECURE_REDIS_PASSWORD_HERE
REDIS_URL=redis://:${{REDIS_PASSWORD}}@${{REDIS_HOST}}:${{REDIS_PORT}}/0

# RabbitMQ Configuration
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=rabbitmq_user
RABBITMQ_PASSWORD=CHANGE_ME_SECURE_RABBITMQ_PASSWORD_HERE
RABBITMQ_URL=amqp://${{RABBITMQ_USER}}:${{RABBITMQ_PASSWORD}}@${{RABBITMQ_HOST}}:${{RABBITMQ_PORT}}/

# API Configuration
API_SECRET_KEY=CHANGE_ME_SECURE_API_KEY_HERE
JWT_SECRET=CHANGE_ME_SECURE_JWT_SECRET_HERE
ENVIRONMENT=production

# Application Configuration
EXTERNAL_PORT={external_port}
INTERNAL_PORT={internal_port}
'''

def get_secure_compose_template(service_name: str, external_port: int, internal_port: int) -> str:
    """Generate secure docker-compose.yml with no hardcoded secrets"""
    return SECURE_COMPOSE_TEMPLATE.format(
        service_name=service_name,
        external_port=external_port,
        internal_port=internal_port
    )

def get_env_template(service_name: str, external_port: int, internal_port: int) -> str:
    """Generate .env template with secure placeholders"""
    return REQUIRED_ENV_TEMPLATE.format(
        service_name=service_name,
        external_port=external_port,
        internal_port=internal_port
    )

def validate_no_hardcoded_secrets(content: str) -> list:
    """Validate that content contains no hardcoded secrets"""
    violations = []
    
    # Check for hardcoded passwords
    if "password=" in content.lower() and "${" not in content:
        violations.append("Hardcoded password detected - use environment variables")
    
    # Check for hardcoded API keys
    hardcoded_patterns = [
        "api_key=",
        "secret_key=", 
        "jwt_secret=",
        "redis_password=",
        "db_password="
    ]
    
    for pattern in hardcoded_patterns:
        if pattern in content.lower() and "${" not in content:
            violations.append(f"Hardcoded secret detected: {pattern} - use environment variables")
    
    return violations