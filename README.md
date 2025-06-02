# AI Command Gateway

> **Intelligent Docker Operations Bridge** - Transform natural language into precise Docker commands with AI-powered execution

[![Production Ready](https://img.shields.io/badge/status-production%20ready-green.svg)](http://localhost:8003/health)
[![API Version](https://img.shields.io/badge/api-v1.0-blue.svg)](http://localhost:8003/docs)
[![Docker](https://img.shields.io/badge/docker-containerized-blue.svg)](http://localhost:8003)

## What is AI Command Gateway?

The **AI Command Gateway (ACG)** is an intelligent microservice that bridges the gap between natural language Docker operation requests and precise Docker CLI execution. It uses advanced AI reasoning to translate human-readable intents into optimized Docker commands and executes them safely across different environments.

### Key Features

🧠 **AI-Powered Translation** - Natural language → Docker CLI commands using GPT-3.5-turbo  
🐳 **Docker Integration** - Full container lifecycle management (start, stop, restart, monitor)  
🔒 **Multi-Environment** - Local Docker socket + SSH remote execution  
⚡ **High Performance** - Sub-2 second response times with intelligent caching  
📊 **Production Ready** - Comprehensive monitoring, logging, and error handling  
🌐 **RESTful API** - Clean JSON API with OpenAPI documentation  

### Use Cases

- **DevOps Automation**: Let AI agents manage containers with natural language instructions
- **Monitoring Integration**: Translate monitoring alerts into actionable Docker commands  
- **Development Workflows**: Simplify container management for development teams
- **Multi-Environment Deployment**: Consistent Docker operations across local and cloud environments

---

## 🚀 Quick Start

### Running Service
The AI Command Gateway is running and ready to use:

```bash
# Health Check
curl http://localhost:8003/health

# API Documentation  
open http://localhost:8003/docs
```

### Basic Example
```bash
curl -X POST "http://localhost:8003/execute-docker-command" \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "my-app",
    "target_resource": {"name": "market-predictor"},
    "action_request": {
      "intent": "restart the service",
      "context": "Service appears unresponsive",
      "priority": "HIGH"
    }
  }'
```

---

## 📋 API Documentation

### Endpoint Overview

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/execute-docker-command` | POST | Execute Docker operations via natural language |
| `/health` | GET | Service health check |
| `/docs` | GET | Interactive API documentation |
| `/metrics` | GET | Prometheus metrics |

### Core API: Execute Docker Command

**Endpoint**: `POST /execute-docker-command`

#### Request Format

```json
{
  "source_id": "string",
  "target_resource": {
    "name": "string"
  },
  "action_request": {
    "intent": "string",
    "context": "string (optional)",
    "priority": "NORMAL|LOW|HIGH|URGENT (optional, default: NORMAL)"
  }
}
```

#### Response Format

```json
{
  "request_id": "auto-generated-uuid",
  "timestamp_processed_utc": "2025-06-02T15:30:00.000Z",
  "overall_status": "COMPLETED_SUCCESS|COMPLETED_FAILURE|VALIDATION_ERROR|INTERNAL_ERROR",
  "execution_details": {
    "command": "docker restart market-predictor",
    "execution_result": {
      "status": "SUCCESS|FAILURE|TIMEOUT|ERROR",
      "exit_code": 0,
      "stdout": "market-predictor\n",
      "stderr": ""
    }
  },
  "error_details": {
    "error_code": "string (optional)",
    "error_message": "string (optional)"
  }
}
```

---

## 💡 Usage Examples

### Container Management

#### Restart a Service
```bash
curl -X POST "http://localhost:8003/execute-docker-command" \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "monitoring-system",
    "target_resource": {"name": "coding-ai-agent"},
    "action_request": {
      "intent": "restart the service",
      "context": "High memory usage detected",
      "priority": "HIGH"
    }
  }'
```

#### Stop a Service
```bash
curl -X POST "http://localhost:8003/execute-docker-command" \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "deployment-script",
    "target_resource": {"name": "market-predictor"},
    "action_request": {
      "intent": "stop the container",
      "priority": "NORMAL"
    }
  }'
```

#### Start a Service
```bash
curl -X POST "http://localhost:8003/execute-docker-command" \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "deployment-script",
    "target_resource": {"name": "market-predictor"},
    "action_request": {
      "intent": "start the container",
      "context": "Deployment completed, starting service",
      "priority": "NORMAL"
    }
  }'
```

### Monitoring & Status

#### Check Container Status
```bash
curl -X POST "http://localhost:8003/execute-docker-command" \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "health-checker",
    "target_resource": {"name": "devops-ai-agent"},
    "action_request": {
      "intent": "check container status",
      "context": "Regular health check",
      "priority": "LOW"
    }
  }'
```

#### Get Resource Usage
```bash
curl -X POST "http://localhost:8003/execute-docker-command" \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "monitoring",
    "target_resource": {"name": "coding-ai-agent"},
    "action_request": {
      "intent": "show memory and CPU usage",
      "context": "Performance monitoring check",
      "priority": "NORMAL"
    }
  }'
```

#### View Container Logs
```bash
curl -X POST "http://localhost:8003/execute-docker-command" \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "debugging",
    "target_resource": {"name": "market-predictor"},
    "action_request": {
      "intent": "show recent logs",
      "context": "Investigating error reports",
      "priority": "HIGH"
    }
  }'
```

### Advanced Operations

#### Container Health Check
```bash
curl -X POST "http://localhost:8003/execute-docker-command" \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "health-monitor",
    "target_resource": {"name": "coding-ai-agent"},
    "action_request": {
      "intent": "check if service is healthy",
      "context": "Automated health monitoring",
      "priority": "NORMAL"
    }
  }'
```

#### Inspect Container Configuration
```bash
curl -X POST "http://localhost:8003/execute-docker-command" \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "admin-tools",
    "target_resource": {"name": "devops-ai-agent"},
    "action_request": {
      "intent": "show container configuration",
      "context": "Configuration audit",
      "priority": "LOW"
    }
  }'
```

---

## 🎯 Supported Operations

The AI Command Gateway can intelligently translate various intents into appropriate Docker commands:

| Intent Category | Example Intents | Generated Commands |
|----------------|-----------------|-------------------|
| **Lifecycle** | "restart the service", "stop container", "start service" | `docker restart`, `docker stop`, `docker start` |
| **Status** | "check status", "is it running", "show container info" | `docker ps`, `docker inspect` |
| **Monitoring** | "show resource usage", "get memory stats", "CPU usage" | `docker stats`, `docker top` |
| **Logs** | "show recent logs", "tail logs", "check errors" | `docker logs` |
| **Health** | "check health", "is service healthy", "health status" | `docker ps --filter health=healthy` |

### Supported Services

Currently configured services:
- `market-predictor`
- `devops-ai-agent` 
- `coding-ai-agent`

*Additional services can be configured via environment variables*

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key for AI processing | - | ✅ |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-3.5-turbo` | ❌ |
| `EXECUTION_STRATEGY` | Execution method | `local_socket` | ❌ |
| `API_HOST` | API server host | `0.0.0.0` | ❌ |
| `API_PORT` | API server port | `8003` | ❌ |
| `LOG_LEVEL` | Logging level | `INFO` | ❌ |
| `COMMAND_TIMEOUT_SECONDS` | Command execution timeout | `30` | ❌ |

### Container Name Mapping

Map logical service names to actual container names:

```env
CONTAINER_NAME_FOR_MARKET_PREDICTOR="market-predictor"
CONTAINER_NAME_FOR_DEVOPS_AI_AGENT="devops-ai-agent"
CONTAINER_NAME_FOR_CODING_AI_AGENT="coding-ai-agent"
```

### SSH Remote Execution (Optional)

For remote Docker host execution:

```env
EXECUTION_STRATEGY="ssh"
SSH_TARGET_HOST="your-docker-host"
SSH_TARGET_USER="docker-user"
SSH_PRIVATE_KEY_PATH="/path/to/ssh/key"
```

---

## 🔍 Error Handling

### Common Error Responses

#### Service Not Found
```json
{
  "overall_status": "VALIDATION_ERROR",
  "error_details": {
    "error_code": "UNKNOWN_SERVICE",
    "error_message": "Unknown logical service name: invalid-service"
  }
}
```

#### Command Generation Failed
```json
{
  "overall_status": "LLM_GENERATION_FAILED",
  "error_details": {
    "error_code": "LLM_ERROR",
    "error_message": "Generated command failed validation"
  }
}
```

#### Execution Failed
```json
{
  "overall_status": "COMPLETED_FAILURE",
  "execution_details": {
    "command": "docker restart non-existent-container",
    "execution_result": {
      "status": "FAILURE",
      "exit_code": 1,
      "stderr": "Error: No such container: non-existent-container"
    }
  }
}
```

---

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8003/health
```

### Prometheus Metrics
```bash
curl http://localhost:8003/metrics
```

**Available Metrics:**
- `gateway_requests_total` - Total requests by source and status
- `gateway_request_duration_seconds` - Request duration histograms
- `gateway_command_generation_total` - Command generation success/failure
- `gateway_command_execution_total` - Docker command execution stats
- `gateway_active_requests` - Currently active requests

---

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client App    │───▶│ AI Command      │───▶│ Docker Engine   │
│   (DevOps Agent)│    │ Gateway         │    │ (Containers)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │ OpenAI GPT-3.5  │
                       │ (Command Gen)   │
                       └─────────────────┘
```

### Components

- **API Layer**: FastAPI REST endpoint with request validation
- **AI Engine**: OpenAI GPT-3.5-turbo for natural language processing
- **Execution Layer**: Local Docker socket or SSH remote execution
- **Configuration**: Environment-based configuration management
- **Monitoring**: Prometheus metrics and health checks

---

## 🔗 Integration Examples

### DevOps AI Agent Integration

```python
import httpx

class AICommandGatewayClient:
    def __init__(self, base_url="http://localhost:8003"):
        self.base_url = base_url
    
    async def execute_docker_command(self, service_name: str, intent: str, context: str = None):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/execute-docker-command",
                json={
                    "source_id": "devops-ai-agent",
                    "target_resource": {"name": service_name},
                    "action_request": {
                        "intent": intent,
                        "context": context,
                        "priority": "NORMAL"
                    }
                }
            )
            return response.json()

# Usage
gateway = AICommandGatewayClient()
result = await gateway.execute_docker_command(
    "market-predictor", 
    "restart the service",
    "High CPU usage detected"
)
```

### Monitoring System Integration

```bash
# Monitoring script example
check_service_health() {
    local service=$1
    response=$(curl -s -X POST "http://localhost:8003/execute-docker-command" \
      -H "Content-Type: application/json" \
      -d "{
        \"source_id\": \"monitoring-system\",
        \"target_resource\": {\"name\": \"$service\"},
        \"action_request\": {
          \"intent\": \"check if service is healthy\",
          \"context\": \"Automated health check\",
          \"priority\": \"NORMAL\"
        }
      }")
    
    echo "$response" | jq '.execution_details.execution_result.stdout'
}

check_service_health "market-predictor"
```

---

## 🚀 Getting Started

1. **Verify Service**: Ensure the AI Command Gateway is running
   ```bash
   curl http://localhost:8003/health
   ```

2. **Test Basic Operation**: Try a simple command
   ```bash
   curl -X POST "http://localhost:8003/execute-docker-command" \
     -H "Content-Type: application/json" \
     -d '{
       "source_id": "test",
       "target_resource": {"name": "market-predictor"},
       "action_request": {"intent": "check status"}
     }'
   ```

3. **Explore API**: Visit the interactive documentation
   ```bash
   open http://localhost:8003/docs
   ```

4. **Monitor Metrics**: Check Prometheus metrics
   ```bash
   curl http://localhost:8003/metrics
   ```

---

## 📚 Additional Resources

- **API Documentation**: [http://localhost:8003/docs](http://localhost:8003/docs)
- **Health Status**: [http://localhost:8003/health](http://localhost:8003/health)
- **Metrics**: [http://localhost:8003/metrics](http://localhost:8003/metrics)
- **Service Logs**: `docker logs ai-command-gateway`

---

**AI Command Gateway** - Making Docker operations intelligent and accessible through natural language. Transform your infrastructure management with AI-powered automation.