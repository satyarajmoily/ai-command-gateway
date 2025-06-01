"""
Unit tests for API endpoints.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime

from gateway.api.main import app
from gateway.core.models import GatewayRequest, TargetResource, ActionRequest


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    settings = MagicMock()
    settings.gateway_instance_id = "test-gateway"
    settings.execution_strategy = "local_socket"
    settings.cors_origins = "*"
    settings.get_container_name_mapping.return_value = {
        "market-predictor": "test-market-predictor",
        "coding-ai-agent": "test-coding-agent",
        "devops-ai-agent": "test-devops-agent"
    }
    settings.resolve_container_name.side_effect = lambda name: {
        "market-predictor": "test-market-predictor",
        "coding-ai-agent": "test-coding-agent",
        "devops-ai-agent": "test-devops-agent"
    }.get(name, None) or (_ for _ in ()).throw(ValueError(f"Unknown service: {name}"))
    return settings


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Test health check endpoint."""
    
    async def test_health_check_success(self, mock_settings):
        """Test successful health check."""
        with patch('gateway.api.main.get_settings', return_value=mock_settings):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "configuration" in data["checks"]
        assert "execution_strategy" in data["checks"]
    
    async def test_health_check_with_ssh_strategy(self, mock_settings):
        """Test health check with SSH strategy."""
        mock_settings.execution_strategy = "ssh"
        mock_settings.ssh_target_host = "test-host"
        mock_settings.ssh_target_user = "test-user"
        mock_settings.ssh_private_key_path = "/path/to/key"
        
        with patch('gateway.api.main.get_settings', return_value=mock_settings):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["checks"]["ssh_host"] == "test-host"
        assert data["checks"]["ssh_user"] == "test-user"
        assert data["checks"]["ssh_key_configured"] is True


@pytest.mark.asyncio
class TestExecuteDockerCommand:
    """Test main API endpoint."""
    
    def create_test_request(self, logical_name="market-predictor", intent="restart the service"):
        """Create a test request."""
        return {
            "request_id": str(uuid4()),
            "source_agent_id": "test-devops-agent",
            "timestamp_utc": datetime.utcnow().isoformat(),
            "target_resource": {
                "logical_name": logical_name
            },
            "action_request": {
                "intent_or_command_description": intent
            }
        }
    
    async def test_execute_command_valid_request(self, mock_settings):
        """Test valid request processing."""
        request_data = self.create_test_request()
        
        with patch('gateway.api.main.get_settings', return_value=mock_settings):
            with patch('gateway.services.gateway_service.get_command_generator') as mock_cmd_gen:
                with patch('gateway.services.gateway_service.get_executor') as mock_executor:
                    # Mock successful command generation
                    mock_cmd_gen.return_value.generate_command.return_value.success = True
                    mock_cmd_gen.return_value.generate_command.return_value.command = "docker restart test-market-predictor"
                    
                    # Mock successful execution
                    mock_executor.return_value.execute.return_value.status = "SUCCESS"
                    mock_executor.return_value.execute.return_value.exit_code = 0
                    mock_executor.return_value.execute.return_value.stdout = "test-market-predictor\n"
                    mock_executor.return_value.execute.return_value.stderr = ""
                    
                    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                        response = await client.post("/execute-docker-command", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "COMPLETED_SUCCESS"
        assert data["gateway_id"] == "test-gateway"
        assert data["response_to_request_id"] == request_data["request_id"]
        assert "Successfully executed" in data["summary_message_from_gateway"]
    
    async def test_execute_command_unknown_service(self, mock_settings):
        """Test request with unknown service name."""
        request_data = self.create_test_request(logical_name="unknown-service")
        
        with patch('gateway.api.main.get_settings', return_value=mock_settings):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/execute-docker-command", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "VALIDATION_ERROR"
        assert data["error_details"]["error_code"] == "UNKNOWN_SERVICE"
        assert "unknown-service" in data["summary_message_from_gateway"]
    
    async def test_execute_command_invalid_request_format(self, mock_settings):
        """Test request with invalid format."""
        invalid_request = {
            "invalid_field": "test"
            # Missing required fields
        }
        
        with patch('gateway.api.main.get_settings', return_value=mock_settings):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/execute-docker-command", json=invalid_request)
        
        assert response.status_code == 422  # Validation error
    
    async def test_execute_command_all_services(self, mock_settings):
        """Test requests for all supported services."""
        services = ["market-predictor", "coding-ai-agent", "devops-ai-agent"]
        
        for service in services:
            request_data = self.create_test_request(logical_name=service)
            
            with patch('gateway.api.main.get_settings', return_value=mock_settings):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post("/execute-docker-command", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["overall_status"] == "FOUNDATION_READY"
            assert f"test-{service}" in data["summary_message_from_gateway"]
    
    async def test_execute_command_with_incident_context(self, mock_settings):
        """Test request with incident context."""
        request_data = self.create_test_request()
        request_data["incident_context"] = {
            "summary": "High error rate detected",
            "key_data_points": [
                {"type": "metric", "name": "error_rate", "value": "15%"}
            ]
        }
        
        with patch('gateway.api.main.get_settings', return_value=mock_settings):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/execute-docker-command", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "FOUNDATION_READY"
    
    async def test_execute_command_configuration_error(self, mock_settings):
        """Test request when configuration fails."""
        mock_settings.resolve_container_name.side_effect = Exception("Configuration error")
        
        request_data = self.create_test_request()
        
        with patch('gateway.api.main.get_settings', return_value=mock_settings):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/execute-docker-command", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "INTERNAL_ERROR"
        assert data["error_details"]["error_code"] == "GATEWAY_ERROR"