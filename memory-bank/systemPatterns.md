# AI Command Gateway - System Patterns

## Architecture Overview

The AI Command Gateway follows the established monorepo patterns while introducing a specialized execution bridge architecture.

### Core Components

```
Gateway Service
├── API Layer (FastAPI)
│   ├── Request/Response Models
│   ├── Endpoint Implementation
│   └── Error Handling
├── Configuration Layer (Pydantic)
│   ├── Environment Detection
│   ├── Execution Strategy Selection
│   └── Container Name Mapping
├── LLM Integration
│   ├── Command Generation
│   ├── Prompt Engineering
│   └── Response Parsing
└── Execution Layer
    ├── Local Docker Executor
    ├── SSH Remote Executor
    └── Execution Strategy Factory
```

### Design Patterns

#### Strategy Pattern for Execution
```python
class ExecutionStrategy:
    def execute(self, command: str) -> ExecutionResult
    
class LocalDockerExecutor(ExecutionStrategy):
    # Uses Docker socket directly
    
class SSHDockerExecutor(ExecutionStrategy):
    # Uses SSH for remote execution
```

#### Factory Pattern for Executor Selection
```python
class ExecutorFactory:
    @staticmethod
    def create_executor(strategy: str) -> ExecutionStrategy
```

#### Configuration-Driven Behavior
- All environment-specific logic externalized to .env files
- No hardcoded environment assumptions
- Fail-fast validation for missing configurations

### Integration Patterns

#### Request/Response Flow
1. **DevOps Agent** → HTTP POST → **Gateway API**
2. **Gateway** → Configuration lookup → **Container Resolution**
3. **Gateway** → LLM prompt → **Command Generation**
4. **Gateway** → Strategy execution → **Docker Command**
5. **Gateway** → Response formatting → **DevOps Agent**

#### Error Handling Hierarchy
```
Application Errors
├── Configuration Errors (500 - fail to start)
├── LLM Generation Errors (500 - internal failure)
├── Command Execution Errors (200 - command failed)
└── Validation Errors (400 - bad request)
```

### Data Flow Patterns

#### Request Processing Pipeline
```
HTTP Request → Validation → Configuration → Resolution → Generation → Execution → Response
```

#### Configuration Loading Pattern
```python
@lru_cache()
def get_settings():
    return Settings()  # Pydantic BaseSettings with .env loading
```

#### Container Name Resolution
```python
logical_name: "market-predictor"
    ↓ (configuration lookup)
actual_name: "infrastructure-market-predictor"  # or "market-predictor-prod-instance1"
```

## Architectural Decisions

### Single Responsibility Separation
- **Gateway**: Only handles intent → command → execution
- **DevOps Agent**: Maintains all intelligence and decision-making
- **Infrastructure**: Continues orchestration-only role

### LLM Specialization
- Internal LLM focused exclusively on Docker command generation
- No general-purpose AI capabilities in gateway
- Prompt engineering optimized for command syntax

### Environment Abstraction
- Single codebase supports multiple deployment targets
- Environment differences handled through configuration only
- No conditional logic based on environment detection

### Stateless Design
- No persistent state between requests
- Each request handled independently
- Configuration loaded at startup (or cached)

## Security Patterns

### Configuration Security
- SSH keys mounted as volumes, not embedded
- API keys from environment variables only
- No secrets in codebase or logs

### Command Execution Safety
- LLM-generated commands logged before execution
- Execution timeout and resource limits
- Error output captured and returned safely

### Network Security
- Container networking through established patterns
- SSH key management for remote execution
- No direct exposure of Docker socket to external networks

## Monitoring Patterns

### Logging Strategy
```python
# Structured logging with correlation IDs
logger.info("Processing request", 
    request_id=request.request_id,
    source_agent=request.source_agent_id,
    logical_name=request.target_resource.logical_name
)
```

### Metrics Collection
- Request/response timing
- LLM generation success/failure rates
- Command execution outcomes
- Error classification and frequency

### Health Checks
- Configuration validation
- LLM connectivity
- Execution strategy availability
- Container connectivity (for local strategy)

## Scalability Patterns

### Horizontal Scaling
- Stateless design enables multiple instances
- Load balancing through infrastructure layer
- Independent scaling from other services

### Resource Management
- LLM client connection pooling
- SSH connection management for remote execution
- Memory-efficient request processing

## Testing Patterns

### Unit Testing Strategy
```python
# Mock LLM responses for consistent testing
# Mock execution layers for isolation
# Configuration testing with various scenarios
```

### Integration Testing
```python
# Real LLM integration with test prompts
# Local Docker execution with test containers
# End-to-end request/response validation
```

### Contract Testing
- API contract validation with devops-ai-agent
- Response format compliance testing
- Error scenario coverage

This architecture maintains consistency with existing patterns while introducing the specialized execution bridge functionality needed for environment-agnostic Docker operations.