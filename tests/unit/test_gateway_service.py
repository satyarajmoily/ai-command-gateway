"""
Unit tests for main gateway service.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4
from datetime import datetime

from gateway.services.gateway_service import GatewayService, get_gateway_service
from gateway.core.models import (
    GatewayRequest, GatewayResponse, TargetResource, ActionRequest,
    CommandGenerationResponse, ExecutionResult, IncidentContext, KeyDataPoint
)


class TestGatewayService:
    """Test main gateway service functionality."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        settings = Mock()
        settings.gateway_instance_id = "test-gateway"
        settings.execution_strategy = "local_socket"
        settings.command_timeout_seconds = 30
        settings.resolve_container_name.return_value = "test-container"
        return settings
    
    @pytest.fixture
    def mock_command_generator(self):
        """Mock command generator."""
        generator = Mock()
        generator.generate_command.return_value = CommandGenerationResponse(
            command="docker restart test-container",
            success=True
        )
        return generator
    
    @pytest.fixture
    def mock_executor(self):
        """Mock executor."""
        executor = Mock()
        executor.execute.return_value = ExecutionResult(
            status="SUCCESS",
            exit_code=0,
            stdout="Container restarted successfully",
            stderr=""
        )
        return executor
    
    @pytest.fixture
    def sample_request(self):
        """Create a sample gateway request."""
        return GatewayRequest(
            request_id=uuid4(),
            source_agent_id="test-devops-agent",
            target_resource=TargetResource(logical_name="market-predictor"),
            action_request=ActionRequest(
                intent_or_command_description="restart the service due to high error rate"
            )
        )
    
    @patch('gateway.services.gateway_service.get_settings')
    @patch('gateway.services.gateway_service.get_command_generator')
    @patch('gateway.services.gateway_service.get_executor')
    @pytest.mark.asyncio
    async def test_successful_request_processing(
        self, mock_get_executor, mock_get_command_generator, mock_get_settings,
        mock_settings, mock_command_generator, mock_executor, sample_request
    ):
        """Test successful complete request processing."""
        mock_get_settings.return_value = mock_settings
        mock_get_command_generator.return_value = mock_command_generator
        mock_get_executor.return_value = mock_executor
        
        service = GatewayService()
        response = await service.process_request(sample_request)
        
        assert response.response_to_request_id == sample_request.request_id
        assert response.gateway_id == "test-gateway"
        assert response.overall_status == "COMPLETED_SUCCESS"
        assert response.execution_details is not None
        assert response.execution_details.docker_command_generated_by_llm == "docker restart test-container"
        assert response.execution_details.execution_result.status == "SUCCESS"
        assert "successfully executed" in response.summary_message_from_gateway.lower()
    
    @patch('gateway.services.gateway_service.get_settings')
    @patch('gateway.services.gateway_service.get_command_generator')
    @patch('gateway.services.gateway_service.get_executor')
    @pytest.mark.asyncio
    async def test_unknown_service_error(
        self, mock_get_executor, mock_get_command_generator, mock_get_settings,
        mock_command_generator, mock_executor, sample_request
    ):
        """Test handling of unknown service name."""
        mock_settings = Mock()
        mock_settings.resolve_container_name.side_effect = ValueError("Unknown service")
        mock_get_settings.return_value = mock_settings
        mock_get_command_generator.return_value = mock_command_generator
        mock_get_executor.return_value = mock_executor
        
        service = GatewayService()
        response = await service.process_request(sample_request)
        
        assert response.overall_status == "VALIDATION_ERROR"
        assert response.error_details is not None
        assert response.error_details.error_code == "UNKNOWN_SERVICE"
        assert "Unknown service" in response.summary_message_from_gateway
    
    @patch('gateway.services.gateway_service.get_settings')
    @patch('gateway.services.gateway_service.get_command_generator')
    @patch('gateway.services.gateway_service.get_executor')
    @pytest.mark.asyncio
    async def test_llm_generation_failure(
        self, mock_get_executor, mock_get_command_generator, mock_get_settings,
        mock_settings, mock_executor, sample_request
    ):
        """Test handling of LLM command generation failure."""
        mock_get_settings.return_value = mock_settings
        
        # Mock failed command generation
        failed_generator = Mock()
        failed_generator.generate_command.return_value = CommandGenerationResponse(
            command="",
            success=False,
            error_message="LLM API error"
        )
        mock_get_command_generator.return_value = failed_generator
        mock_get_executor.return_value = mock_executor
        
        service = GatewayService()
        response = await service.process_request(sample_request)
        
        assert response.overall_status == "LLM_GENERATION_FAILED"
        assert response.error_details is not None
        assert response.error_details.error_code == "LLM_ERROR"
        assert "Failed to generate Docker command" in response.summary_message_from_gateway
    
    @patch('gateway.services.gateway_service.get_settings')
    @patch('gateway.services.gateway_service.get_command_generator')
    @patch('gateway.services.gateway_service.get_executor')
    @pytest.mark.asyncio
    async def test_command_execution_failure(
        self, mock_get_executor, mock_get_command_generator, mock_get_settings,
        mock_settings, mock_command_generator, sample_request
    ):
        """Test handling of command execution failure."""
        mock_get_settings.return_value = mock_settings
        mock_get_command_generator.return_value = mock_command_generator
        
        # Mock failed execution
        failed_executor = Mock()
        failed_executor.execute.return_value = ExecutionResult(
            status="FAILURE",
            exit_code=1,
            stdout="",
            stderr="No such container: test-container"
        )
        mock_get_executor.return_value = failed_executor
        
        service = GatewayService()
        response = await service.process_request(sample_request)
        
        assert response.overall_status == "COMPLETED_FAILURE"
        assert response.execution_details is not None
        assert response.execution_details.execution_result.status == "FAILURE"
        assert "failed to execute" in response.summary_message_from_gateway.lower()
        assert "Exit code: 1" in response.summary_message_from_gateway
    
    @patch('gateway.services.gateway_service.get_settings')
    @patch('gateway.services.gateway_service.get_command_generator')
    @patch('gateway.services.gateway_service.get_executor')
    @pytest.mark.asyncio
    async def test_request_with_incident_context(
        self, mock_get_executor, mock_get_command_generator, mock_get_settings,
        mock_settings, mock_command_generator, mock_executor
    ):
        """Test processing request with incident context."""
        mock_get_settings.return_value = mock_settings
        mock_get_command_generator.return_value = mock_command_generator
        mock_get_executor.return_value = mock_executor
        
        # Create request with incident context
        request = GatewayRequest(
            request_id=uuid4(),
            source_agent_id="test-devops-agent",
            target_resource=TargetResource(logical_name="market-predictor"),
            action_request=ActionRequest(
                intent_or_command_description="restart the service",
                expected_outcome_description="Service should be healthy"
            ),
            incident_context=IncidentContext(
                summary="High error rate detected",
                key_data_points=[
                    KeyDataPoint(type="metric", name="error_rate", value="15%")
                ]
            )
        )
        
        service = GatewayService()
        response = await service.process_request(request)
        
        assert response.overall_status == "COMPLETED_SUCCESS"
        
        # Verify context was passed to command generator
        call_args = mock_command_generator.generate_command.call_args[0][0]
        assert call_args.context is not None
        assert "High error rate detected" in call_args.context
        assert "error_rate=15%" in call_args.context
        assert "Service should be healthy" in call_args.context
    
    @patch('gateway.services.gateway_service.get_settings')
    @patch('gateway.services.gateway_service.get_command_generator')
    @patch('gateway.services.gateway_service.get_executor')
    @pytest.mark.asyncio
    async def test_ssh_execution_strategy(
        self, mock_get_executor, mock_get_command_generator, mock_get_settings,
        mock_command_generator, mock_executor, sample_request
    ):
        """Test SSH execution strategy effective command generation."""
        # Mock SSH settings
        ssh_settings = Mock()
        ssh_settings.gateway_instance_id = "test-gateway"
        ssh_settings.execution_strategy = "ssh"
        ssh_settings.command_timeout_seconds = 30
        ssh_settings.ssh_target_host = "remote-host"
        ssh_settings.ssh_target_user = "opc"
        ssh_settings.ssh_private_key_path = "/path/to/key"
        ssh_settings.resolve_container_name.return_value = "test-container"
        
        mock_get_settings.return_value = ssh_settings
        mock_get_command_generator.return_value = mock_command_generator
        mock_get_executor.return_value = mock_executor
        
        service = GatewayService()
        response = await service.process_request(sample_request)
        
        assert response.overall_status == "COMPLETED_SUCCESS"
        effective_command = response.execution_details.effective_command_run_by_gateway
        assert "ssh -i /path/to/key opc@remote-host" in effective_command
        assert "docker restart test-container" in effective_command
    
    @patch('gateway.services.gateway_service.get_settings')
    @patch('gateway.services.gateway_service.get_command_generator')
    @patch('gateway.services.gateway_service.get_executor')
    @pytest.mark.asyncio
    async def test_internal_service_error(
        self, mock_get_executor, mock_get_command_generator, mock_get_settings,
        mock_settings, sample_request
    ):
        """Test handling of internal service errors."""
        mock_get_settings.return_value = mock_settings
        mock_get_command_generator.side_effect = Exception("Internal error")
        
        service = GatewayService()
        response = await service.process_request(sample_request)
        
        assert response.overall_status == "INTERNAL_ERROR"
        assert response.error_details is not None
        assert response.error_details.error_code == "GATEWAY_ERROR"
        assert "Internal gateway error" in response.summary_message_from_gateway


class TestGatewayServiceSingleton:
    """Test gateway service singleton pattern."""
    
    def test_get_gateway_service_singleton(self):
        """Test that get_gateway_service returns the same instance."""
        # Clear the global instance first
        import gateway.services.gateway_service
        gateway.services.gateway_service._gateway_service = None
        
        with patch('gateway.services.gateway_service.get_settings'):
            with patch('gateway.services.gateway_service.get_command_generator'):
                with patch('gateway.services.gateway_service.get_executor'):
                    service1 = get_gateway_service()
                    service2 = get_gateway_service()
                    
                    assert service1 is service2


class TestGatewayServiceHelperMethods:
    """Test gateway service helper methods."""
    
    @pytest.fixture
    def service_instance(self):
        """Create a service instance for testing."""
        with patch('gateway.services.gateway_service.get_settings'):
            with patch('gateway.services.gateway_service.get_command_generator'):
                with patch('gateway.services.gateway_service.get_executor'):
                    return GatewayService()
    
    def test_build_context_with_full_data(self, service_instance):
        """Test context building with all available data."""
        request = GatewayRequest(
            request_id=uuid4(),
            source_agent_id="test-agent",
            target_resource=TargetResource(
                logical_name="test-service",
                qualifiers={
                    "instance_group": "blue",
                    "region_hint": "us-west-1"
                }
            ),
            action_request=ActionRequest(
                intent_or_command_description="restart service",
                expected_outcome_description="Service should be healthy"
            ),
            incident_context=IncidentContext(
                summary="High memory usage",
                key_data_points=[
                    KeyDataPoint(type="metric", name="memory_usage", value="90%")
                ]
            )
        )
        
        context = service_instance._build_context(request)
        
        assert "High memory usage" in context
        assert "memory_usage=90%" in context
        assert "Service should be healthy" in context
        assert "Instance group: blue" in context
        assert "Region: us-west-1" in context
    
    def test_build_context_minimal_data(self, service_instance):
        """Test context building with minimal data."""
        request = GatewayRequest(
            request_id=uuid4(),
            source_agent_id="test-agent",
            target_resource=TargetResource(logical_name="test-service"),
            action_request=ActionRequest(intent_or_command_description="restart service")
        )
        
        context = service_instance._build_context(request)
        
        assert context is None  # No context data available