"""
Request and response models for AI Command Gateway API.
Defines the JSON schema for communication with devops-ai-agent.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


# Request Models - OPTIMIZED SCHEMA

class TargetResource(BaseModel):
    """Target resource information - simplified."""
    name: str = Field(..., description="Name of the service (e.g., 'coding-ai-agent')")


class ActionRequest(BaseModel):
    """Action request details - enhanced with context."""
    intent: str = Field(
        ..., 
        description="Natural language description of desired Docker operation"
    )
    context: Optional[str] = Field(
        None,
        description="Additional context to enhance command generation (e.g., 'Observing increase in memory')"
    )
    priority: str = Field(default="NORMAL", description="Request priority: LOW, NORMAL, HIGH, URGENT")


class GatewayRequest(BaseModel):
    """Main request model for gateway API - optimized."""
    source_id: str = Field(..., description="Identifier of the calling agent")
    target_resource: TargetResource = Field(..., description="Target resource information")
    action_request: ActionRequest = Field(..., description="Action to be performed")


# Response Models - SIMPLIFIED SCHEMA

class ExecutionResult(BaseModel):
    """Result of command execution."""
    status: str = Field(..., description="Execution status: SUCCESS or FAILURE")
    exit_code: int = Field(..., description="Command exit code")
    stdout: str = Field(..., description="Standard output from command")
    stderr: str = Field(..., description="Standard error from command")


class ExecutionDetails(BaseModel):
    """Detailed execution information - simplified."""
    command: str = Field(..., description="Docker command that was executed")
    execution_result: ExecutionResult = Field(..., description="Execution result")


class ErrorDetails(BaseModel):
    """Error details for failed operations."""
    error_code: Optional[str] = Field(None, description="Error code")
    error_message: Optional[str] = Field(None, description="Error message")


class GatewayResponse(BaseModel):
    """Main response model for gateway API - optimized."""
    request_id: UUID = Field(default_factory=uuid4, description="Auto-generated request identifier")
    timestamp_processed_utc: datetime = Field(default_factory=datetime.utcnow, description="Processing timestamp")
    overall_status: str = Field(..., description="Overall operation status")
    execution_details: Optional[ExecutionDetails] = Field(None, description="Execution details")
    error_details: Optional[ErrorDetails] = Field(None, description="Error details if applicable")


# Health Check Models

class HealthStatus(BaseModel):
    """Health check status."""
    status: str = Field(..., description="Health status: healthy, unhealthy, or degraded")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="1.0.0", description="Gateway version")
    checks: Dict[str, Any] = Field(default_factory=dict, description="Individual health checks")


# Internal Models

class CommandGenerationRequest(BaseModel):
    """Internal model for LLM command generation."""
    intent: str = Field(..., description="Natural language intent")
    container_name: str = Field(..., description="Resolved container name")
    context: Optional[str] = Field(None, description="Additional context")


class CommandGenerationResponse(BaseModel):
    """Internal model for LLM command generation response."""
    command: str = Field(..., description="Generated Docker command")
    success: bool = Field(..., description="Whether generation was successful")
    error_message: Optional[str] = Field(None, description="Error message if failed")