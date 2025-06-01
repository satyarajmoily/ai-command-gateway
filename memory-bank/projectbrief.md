# AI Command Gateway - Project Brief

## Core Purpose
Create an intelligent execution bridge between the devops-ai-agent and Docker environments that translates natural language Docker operation intents into specific CLI commands and executes them across different target environments.

## Key Requirements

### Primary Functionality
- **Single API Endpoint**: `POST /execute-docker-command`
- **Natural Language Processing**: Convert high-level intents to Docker commands
- **Multi-Environment Support**: Local Docker socket and SSH remote execution
- **Environment Agnostic**: Same codebase, different configurations
- **Raw Output Handling**: Preserve logs, metrics, and command results

### Integration Goals
- Enable devops-ai-agent to remain environment-agnostic
- Provide consistent API for Docker operations
- Support Oracle Cloud and local development environments
- Maintain clean separation of concerns

### Configuration Philosophy
- All environment behavior driven by external .env files
- Fail-fast on missing critical configuration
- No hardcoded defaults that mask configuration issues
- Container name mapping through configuration

## Non-Goals (Initial Version)
- Complex multi-step workflow orchestration
- Advanced security features (RBAC, approval workflows)
- Non-Docker command types (Kubernetes API, OCI API)
- User notifications (handled by devops-ai-agent)

## Success Criteria
1. Seamless integration with existing devops-ai-agent
2. Support for local and Oracle Cloud environments
3. Reliable natural language to Docker command translation
4. Clean architecture following existing patterns
5. Comprehensive error handling and logging

## Technology Alignment
- FastAPI (consistent with other services)
- Pydantic configuration management
- OpenAI for command generation LLM
- Volume-mounted source code architecture
- Docker containerization with proper networking