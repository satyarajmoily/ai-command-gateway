# AI Command Gateway - Technical Context

## Technology Stack

### Core Framework
- **FastAPI**: REST API framework (consistent with other services)
- **Pydantic**: Configuration management and data validation
- **Uvicorn**: ASGI server for production deployment
- **Python 3.13.3**: Aligned with monorepo Python version

### LLM Integration
- **OpenAI Python Client**: For Docker command generation
- **Model**: GPT-3.5-turbo or GPT-4 (configurable)
- **Prompt Engineering**: Specialized for Docker CLI command output

### Execution Technologies
- **subprocess**: Local Docker command execution
- **Paramiko**: SSH client for remote execution
- **Docker CLI**: Primary interface for container operations

### Testing Framework
- **pytest**: Unit and integration testing
- **httpx**: HTTP client testing for FastAPI
- **pytest-asyncio**: Async test support

## Dependencies

### Production Requirements
```
fastapi>=0.104.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
uvicorn>=0.24.0
openai>=1.3.0
paramiko>=3.3.0
```

### Development Requirements
```
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx>=0.25.0
black>=23.0.0
isort>=5.12.0
mypy>=1.7.0
```

## Configuration Architecture

### Environment Variable Pattern
Following established monorepo pattern with `.env` files:

```python
from pydantic import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Gateway identification
    gateway_instance_id: str
    log_level: str = "INFO"
    
    # LLM configuration  
    llm_provider: str = "openai"
    llm_model_name: str = "gpt-3.5-turbo"
    llm_api_key: str
    
    # Execution strategy
    execution_strategy: str  # "local_socket" or "ssh"
    
    # Container mappings
    container_name_for_market_predictor: str
    container_name_for_devops_ai_agent: str
    container_name_for_coding_ai_agent: str
    
    class Config:
        env_file = Path(__file__).parent.parent.parent / '.env'
```

### Configuration Validation
- Strict validation with no defaults for critical settings
- Strategy-specific validation (SSH settings required for SSH strategy)
- Fail-fast behavior on startup if configuration invalid

## Docker Integration

### Container Architecture
Following established volume-mounting pattern:

```dockerfile
# Multi-stage build - dependencies only
FROM python:3.13.3-slim as dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM dependencies as runtime
WORKDIR /app
EXPOSE 8080
CMD ["uvicorn", "gateway.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Volume Mounting Strategy
```yaml
# In docker-compose.yml
ai-command-gateway:
  build: ./ai-command-gateway/docker
  volumes:
    - ./ai-command-gateway/src:/app:ro  # Source code as read-only volume
    - ./ai-command-gateway/.env:/app/.env:ro  # Configuration
    - /var/run/docker.sock:/var/run/docker.sock:ro  # Docker socket (local strategy)
```

## Execution Strategies

### Local Docker Socket
```python
import subprocess
import json

def execute_local_command(command: str) -> ExecutionResult:
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            timeout=30
        )
        return ExecutionResult(
            status="success" if result.returncode == 0 else "failure",
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr
        )
    except subprocess.TimeoutExpired:
        return ExecutionResult(status="timeout", ...)
```

### SSH Remote Execution
```python
import paramiko

def execute_ssh_command(host: str, user: str, key_path: str, command: str) -> ExecutionResult:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, username=user, key_filename=key_path)
        stdin, stdout, stderr = client.exec_command(command, timeout=30)
        
        return ExecutionResult(
            status="success" if stdout.channel.recv_exit_status() == 0 else "failure",
            exit_code=stdout.channel.recv_exit_status(),
            stdout=stdout.read().decode(),
            stderr=stderr.read().decode()
        )
    finally:
        client.close()
```

## LLM Integration Pattern

### Prompt Engineering
```python
SYSTEM_PROMPT = """You are an expert Docker command generator. 
Convert user intents into precise Docker CLI commands.
Respond ONLY with the command string, no explanations.

Examples:
Intent: "restart the container"
Container: "my-app"
Response: docker restart my-app

Intent: "get last 50 log lines"  
Container: "my-app"
Response: docker logs --tail 50 my-app
"""

def generate_command(intent: str, container_name: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Intent: {intent}\nContainer: {container_name}"}
    ]
    
    response = openai_client.chat.completions.create(
        model=settings.llm_model_name,
        messages=messages,
        max_tokens=100,
        temperature=0.1
    )
    
    return response.choices[0].message.content.strip()
```

## Error Handling Strategy

### Error Classification
```python
class GatewayError(Exception):
    pass

class ConfigurationError(GatewayError):
    # Missing or invalid configuration
    pass

class LLMGenerationError(GatewayError):
    # LLM failed to generate command
    pass

class CommandExecutionError(GatewayError):
    # Command execution failed
    pass
```

### Response Formatting
```python
def format_error_response(error: Exception, request_id: str) -> dict:
    if isinstance(error, ConfigurationError):
        return {
            "overall_status": "CONFIGURATION_ERROR",
            "error_details": {
                "error_code": "GATEWAY_CONFIG_ERROR",
                "error_message": str(error)
            }
        }
    # ... other error types
```

## Network and Security

### API Security
```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8001"],  # DevOps agent only
    allow_methods=["POST"],
    allow_headers=["*"],
)
```

### SSH Key Management
- Keys mounted as Docker secrets or volumes
- Never embedded in code or logs
- Proper permission management (600 for private keys)

### Command Logging
```python
import logging

logger = logging.getLogger(__name__)

def log_command_execution(command: str, result: ExecutionResult, request_id: str):
    logger.info(
        "Command executed",
        extra={
            "request_id": request_id,
            "command": command,
            "exit_code": result.exit_code,
            "execution_time": result.execution_time
        }
    )
```

## Development Environment

### Local Development Setup
1. Python 3.13.3 virtual environment
2. Docker Desktop for local testing
3. Environment variable configuration in `.env`
4. Hot reload during development

### Testing Strategy
```python
# Unit tests with mocked dependencies
@pytest.fixture
def mock_openai_client():
    with patch('gateway.core.command_generator.openai_client') as mock:
        mock.chat.completions.create.return_value.choices[0].message.content = "docker restart test-app"
        yield mock

# Integration tests with real components
@pytest.mark.integration
async def test_local_execution():
    # Test with real Docker socket
    pass
```

This technical foundation ensures the AI Command Gateway integrates seamlessly with the existing infrastructure while providing robust Docker command translation and execution capabilities.