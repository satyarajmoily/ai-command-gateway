"""
Unit tests for Docker command generator.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from gateway.core.command_generator import DockerCommandGenerator, get_command_generator
from gateway.core.models import CommandGenerationRequest, CommandGenerationResponse


class TestDockerCommandGenerator:
    """Test Docker command generation functionality."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        settings = Mock()
        settings.llm_api_key = "test-key"
        settings.llm_api_base_url = "https://api.openai.com/v1/"
        settings.llm_model_name = "gpt-3.5-turbo"
        settings.llm_provider = "openai"
        settings.llm_system_prompt = "Test system prompt"
        return settings
    
    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI API response."""
        choice = Choice(
            index=0,
            message=ChatCompletionMessage(
                role="assistant",
                content="docker restart test-container"
            ),
            finish_reason="stop"
        )
        
        response = ChatCompletion(
            id="test-id",
            object="chat.completion",
            created=1234567890,
            model="gpt-3.5-turbo",
            choices=[choice]
        )
        return response
    
    @patch('gateway.core.command_generator.get_settings')
    @patch('gateway.core.command_generator.OpenAI')
    def test_generate_restart_command(self, mock_openai_class, mock_get_settings, mock_settings, mock_openai_response):
        """Test generating a restart command."""
        mock_get_settings.return_value = mock_settings
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response
        
        generator = DockerCommandGenerator()
        
        request = CommandGenerationRequest(
            intent="restart the service",
            container_name="test-container"
        )
        
        response = generator.generate_command(request)
        
        assert response.success is True
        assert response.command == "docker restart test-container"
        assert response.error_message is None
    
    @patch('gateway.core.command_generator.get_settings')
    @patch('gateway.core.command_generator.OpenAI')
    def test_generate_logs_command(self, mock_openai_class, mock_get_settings, mock_settings):
        """Test generating a logs command."""
        mock_get_settings.return_value = mock_settings
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock response for logs command
        choice = Choice(
            index=0,
            message=ChatCompletionMessage(
                role="assistant",
                content="docker logs --tail 50 test-container"
            ),
            finish_reason="stop"
        )
        
        response = ChatCompletion(
            id="test-id",
            object="chat.completion", 
            created=1234567890,
            model="gpt-3.5-turbo",
            choices=[choice]
        )
        
        mock_client.chat.completions.create.return_value = response
        
        generator = DockerCommandGenerator()
        
        request = CommandGenerationRequest(
            intent="get the last 50 lines of logs",
            container_name="test-container"
        )
        
        result = generator.generate_command(request)
        
        assert result.success is True
        assert result.command == "docker logs --tail 50 test-container"
    
    @patch('gateway.core.command_generator.get_settings')
    @patch('gateway.core.command_generator.OpenAI')
    def test_generate_command_with_context(self, mock_openai_class, mock_get_settings, mock_settings, mock_openai_response):
        """Test generating command with additional context."""
        mock_get_settings.return_value = mock_settings
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response
        
        generator = DockerCommandGenerator()
        
        request = CommandGenerationRequest(
            intent="restart the service",
            container_name="test-container",
            context="High error rate detected"
        )
        
        result = generator.generate_command(request)
        
        assert result.success is True
        # Verify context was included in the prompt
        call_args = mock_client.chat.completions.create.call_args[1]
        messages = call_args['messages']
        user_message = messages[1]['content']
        assert "High error rate detected" in user_message
    
    def test_validate_command_valid_cases(self):
        """Test command validation with valid commands."""
        generator = DockerCommandGenerator.__new__(DockerCommandGenerator)
        
        valid_commands = [
            "docker restart my-container",
            "docker logs --tail 50 my-container",
            "docker exec my-container ps aux",
            "docker stats --no-stream my-container",
            "docker inspect my-container"
        ]
        
        for command in valid_commands:
            assert generator._validate_command(command) is True, f"Valid command failed: {command}"
    
    def test_validate_command_invalid_cases(self):
        """Test command validation with invalid commands."""
        generator = DockerCommandGenerator.__new__(DockerCommandGenerator)
        
        invalid_commands = [
            "",
            "not-docker command",
            "docker",  # No subcommand
            "docker rm my-container",  # Dangerous command
            "docker exec my-container sudo rm -rf /",  # Dangerous pattern
            "docker invalid-subcommand my-container"  # Invalid subcommand
        ]
        
        for command in invalid_commands:
            assert generator._validate_command(command) is False, f"Invalid command passed: {command}"
    
    @patch('gateway.core.command_generator.get_settings')
    @patch('gateway.core.command_generator.OpenAI')
    def test_openai_api_error_handling(self, mock_openai_class, mock_get_settings, mock_settings):
        """Test handling of OpenAI API errors."""
        mock_get_settings.return_value = mock_settings
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        generator = DockerCommandGenerator()
        
        request = CommandGenerationRequest(
            intent="restart the service",
            container_name="test-container"
        )
        
        result = generator.generate_command(request)
        
        assert result.success is False
        assert "API Error" in result.error_message
        assert result.command == ""
    
    @patch('gateway.core.command_generator.get_settings')
    @patch('gateway.core.command_generator.OpenAI')
    def test_invalid_generated_command(self, mock_openai_class, mock_get_settings, mock_settings):
        """Test handling of invalid commands generated by LLM."""
        mock_get_settings.return_value = mock_settings
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock response with invalid command
        choice = Choice(
            index=0,
            message=ChatCompletionMessage(
                role="assistant",
                content="rm -rf /"  # Invalid/dangerous command
            ),
            finish_reason="stop"
        )
        
        response = ChatCompletion(
            id="test-id",
            object="chat.completion",
            created=1234567890,
            model="gpt-3.5-turbo",
            choices=[choice]
        )
        
        mock_client.chat.completions.create.return_value = response
        
        generator = DockerCommandGenerator()
        
        request = CommandGenerationRequest(
            intent="restart the service",
            container_name="test-container"
        )
        
        result = generator.generate_command(request)
        
        assert result.success is False
        assert "validation" in result.error_message.lower()


class TestCommandGeneratorSingleton:
    """Test command generator singleton pattern."""
    
    def test_get_command_generator_singleton(self):
        """Test that get_command_generator returns the same instance."""
        # Clear the global instance first
        import gateway.core.command_generator
        gateway.core.command_generator._command_generator = None
        
        with patch('gateway.core.command_generator.get_settings'):
            with patch('gateway.core.command_generator.OpenAI'):
                generator1 = get_command_generator()
                generator2 = get_command_generator()
                
                assert generator1 is generator2