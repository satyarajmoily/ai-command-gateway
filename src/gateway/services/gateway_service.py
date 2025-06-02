"""
Main gateway service that orchestrates the complete workflow.
Handles request validation, command generation, and execution.
"""

import logging
from typing import Optional

from gateway.config.settings import get_settings
from gateway.core.models import (
    GatewayRequest, GatewayResponse, CommandGenerationRequest,
    ExecutionDetails, ErrorDetails
)
from gateway.core.command_generator import get_command_generator
from gateway.core.executors import get_executor

logger = logging.getLogger(__name__)


class GatewayService:
    """Main service that handles the complete gateway workflow."""
    
    def __init__(self):
        """Initialize the gateway service."""
        self.settings = get_settings()
        self.command_generator = get_command_generator()
        self.executor = get_executor()
        
        logger.info(
            f"Gateway service initialized",
            extra={
                "gateway_id": self.settings.gateway_instance_id,
                "execution_strategy": self.settings.execution_strategy
            }
        )
    
    async def process_request(self, request: GatewayRequest) -> GatewayResponse:
        """
        Process a complete gateway request.
        
        Args:
            request: The gateway request to process
            
        Returns:
            GatewayResponse with execution results or error details
        """
        logger.info(
            f"Processing gateway request",
            extra={
                "source_id": request.source_id,
                "target_name": request.target_resource.name,
                "intent": request.action_request.intent,
                "context": request.action_request.context,
                "priority": request.action_request.priority
            }
        )
        
        try:
            # Step 1: Resolve container name
            try:
                actual_container_name = self.settings.resolve_container_name(
                    request.target_resource.name
                )
                logger.info(
                    f"Container name resolved",
                    extra={
                        "source_id": request.source_id,
                        "target_name": request.target_resource.name,
                        "actual_name": actual_container_name
                    }
                )
            except ValueError as e:
                logger.error(f"Container name resolution failed: {e}")
                return self._create_error_response(
                    request,
                    "VALIDATION_ERROR",
                    "UNKNOWN_SERVICE",
                    str(e)
                )
            
            # Step 2: Generate Docker command using LLM with enhanced context
            command_request = CommandGenerationRequest(
                intent=request.action_request.intent,
                container_name=actual_container_name,
                context=request.action_request.context  # Use the provided context directly
            )
            
            command_response = self.command_generator.generate_command(command_request)
            
            if not command_response.success:
                # Track failed command generation
                try:
                    from gateway.api.main import COMMAND_GENERATION_COUNT
                    COMMAND_GENERATION_COUNT.labels(status='failed').inc()
                except (ImportError, NameError):
                    pass  # Metrics not available
                    
                logger.error(f"Command generation failed: {command_response.error_message}")
                return self._create_error_response(
                    request,
                    "LLM_GENERATION_FAILED",
                    "LLM_ERROR",
                    command_response.error_message
                )
            
            # Track successful command generation
            try:
                from gateway.api.main import COMMAND_GENERATION_COUNT
                COMMAND_GENERATION_COUNT.labels(status='success').inc()
            except (ImportError, NameError):
                pass  # Metrics not available
            
            generated_command = command_response.command
            logger.info(
                f"Docker command generated",
                extra={
                    "source_id": request.source_id,
                    "generated_command": generated_command
                }
            )
            
            # Step 3: Execute the command
            execution_result = self.executor.execute(
                generated_command,
                timeout=self.settings.command_timeout_seconds
            )
            
            logger.info(
                f"Command execution completed",
                extra={
                    "source_id": request.source_id,
                    "exit_code": execution_result.exit_code,
                    "status": execution_result.status
                }
            )
            
            # Step 4: Build simplified execution details
            execution_details = ExecutionDetails(
                command=generated_command,
                execution_result=execution_result
            )
            
            # Step 5: Determine overall status
            if execution_result.status == "SUCCESS":
                overall_status = "COMPLETED_SUCCESS"
            elif execution_result.status in ["FAILURE", "TIMEOUT", "ERROR"]:
                overall_status = "COMPLETED_FAILURE"
            else:
                overall_status = "EXECUTION_ERROR"
            
            # Step 6: Create optimized response
            return GatewayResponse(
                overall_status=overall_status,
                execution_details=execution_details
            )
            
        except Exception as e:
            logger.error(
                f"Gateway service error",
                extra={
                    "source_id": request.source_id,
                    "error": str(e)
                }
            )
            
            return self._create_error_response(
                request,
                "INTERNAL_ERROR",
                "GATEWAY_ERROR",
                str(e)
            )
    
    def _create_error_response(
        self,
        request: GatewayRequest,
        overall_status: str,
        error_code: str,
        error_message: str
    ) -> GatewayResponse:
        """Create error response with optimized schema."""
        return GatewayResponse(
            overall_status=overall_status,
            error_details=ErrorDetails(
                error_code=error_code,
                error_message=error_message
            )
        )


# Singleton instance
_gateway_service: Optional[GatewayService] = None


def get_gateway_service() -> GatewayService:
    """Get singleton gateway service instance."""
    global _gateway_service
    
    if _gateway_service is None:
        _gateway_service = GatewayService()
    
    return _gateway_service