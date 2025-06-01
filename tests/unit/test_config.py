"""
Unit tests for configuration management.
"""

import pytest
import tempfile
import os
from pathlib import Path
from pydantic import ValidationError

from gateway.config.settings import Settings, get_settings, reload_settings


class TestSettings:
    """Test configuration settings loading and validation."""
    
    def test_valid_local_socket_config(self, tmp_path):
        """Test valid local socket configuration."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
GATEWAY_INSTANCE_ID=test-gateway
LLM_MODEL_NAME=gpt-3.5-turbo
LLM_API_KEY=test-key
EXECUTION_STRATEGY=local_socket
CONTAINER_NAME_FOR_MARKET_PREDICTOR=test-market-predictor
CONTAINER_NAME_FOR_CODING_AI_AGENT=test-coding-agent
CONTAINER_NAME_FOR_DEVOPS_AI_AGENT=test-devops-agent
        """)
        
        # Mock the config file location
        original_config = Settings.model_config['env_file']
        Settings.model_config['env_file'] = env_file
        
        try:
            settings = Settings()
            assert settings.gateway_instance_id == "test-gateway"
            assert settings.execution_strategy == "local_socket"
            assert settings.llm_model_name == "gpt-3.5-turbo"
            assert settings.container_name_for_market_predictor == "test-market-predictor"
        finally:
            Settings.model_config['env_file'] = original_config
    
    def test_valid_ssh_config(self, tmp_path):
        """Test valid SSH configuration."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
GATEWAY_INSTANCE_ID=test-gateway
LLM_MODEL_NAME=gpt-3.5-turbo
LLM_API_KEY=test-key
EXECUTION_STRATEGY=ssh
SSH_TARGET_HOST=test-host
SSH_TARGET_USER=test-user
SSH_PRIVATE_KEY_PATH=/path/to/key
CONTAINER_NAME_FOR_MARKET_PREDICTOR=test-market-predictor
CONTAINER_NAME_FOR_CODING_AI_AGENT=test-coding-agent
CONTAINER_NAME_FOR_DEVOPS_AI_AGENT=test-devops-agent
        """)
        
        original_config = Settings.model_config['env_file']
        Settings.model_config['env_file'] = env_file
        
        try:
            settings = Settings()
            assert settings.execution_strategy == "ssh"
            assert settings.ssh_target_host == "test-host"
            assert settings.ssh_target_user == "test-user"
            assert settings.ssh_private_key_path == "/path/to/key"
        finally:
            Settings.model_config['env_file'] = original_config
    
    def test_invalid_execution_strategy(self, tmp_path):
        """Test invalid execution strategy raises error."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
GATEWAY_INSTANCE_ID=test-gateway
LLM_MODEL_NAME=gpt-3.5-turbo
LLM_API_KEY=test-key
EXECUTION_STRATEGY=invalid_strategy
CONTAINER_NAME_FOR_MARKET_PREDICTOR=test-market-predictor
CONTAINER_NAME_FOR_CODING_AI_AGENT=test-coding-agent
CONTAINER_NAME_FOR_DEVOPS_AI_AGENT=test-devops-agent
        """)
        
        original_config = Settings.model_config['env_file']
        Settings.model_config['env_file'] = env_file
        
        try:
            with pytest.raises(ValidationError):
                Settings()
        finally:
            Settings.model_config['env_file'] = original_config
    
    def test_ssh_missing_config(self, tmp_path):
        """Test SSH strategy with missing configuration raises error."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
GATEWAY_INSTANCE_ID=test-gateway
LLM_MODEL_NAME=gpt-3.5-turbo
LLM_API_KEY=test-key
EXECUTION_STRATEGY=ssh
CONTAINER_NAME_FOR_MARKET_PREDICTOR=test-market-predictor
CONTAINER_NAME_FOR_CODING_AI_AGENT=test-coding-agent
CONTAINER_NAME_FOR_DEVOPS_AI_AGENT=test-devops-agent
        """)
        
        original_config = Settings.model_config['env_file']
        Settings.model_config['env_file'] = env_file
        
        try:
            with pytest.raises(ValidationError):
                Settings()
        finally:
            Settings.model_config['env_file'] = original_config
    
    def test_container_name_mapping(self, tmp_path):
        """Test container name mapping functionality."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
GATEWAY_INSTANCE_ID=test-gateway
LLM_MODEL_NAME=gpt-3.5-turbo
LLM_API_KEY=test-key
EXECUTION_STRATEGY=local_socket
CONTAINER_NAME_FOR_MARKET_PREDICTOR=actual-market-predictor
CONTAINER_NAME_FOR_CODING_AI_AGENT=actual-coding-agent
CONTAINER_NAME_FOR_DEVOPS_AI_AGENT=actual-devops-agent
        """)
        
        original_config = Settings.model_config['env_file']
        Settings.model_config['env_file'] = env_file
        
        try:
            settings = Settings()
            
            # Test mapping retrieval
            mapping = settings.get_container_name_mapping()
            assert mapping["market-predictor"] == "actual-market-predictor"
            assert mapping["coding-ai-agent"] == "actual-coding-agent"
            assert mapping["devops-ai-agent"] == "actual-devops-agent"
            
            # Test name resolution
            assert settings.resolve_container_name("market-predictor") == "actual-market-predictor"
            assert settings.resolve_container_name("coding-ai-agent") == "actual-coding-agent"
            
            # Test unknown service
            with pytest.raises(ValueError):
                settings.resolve_container_name("unknown-service")
        finally:
            Settings.model_config['env_file'] = original_config
    
    def test_missing_required_fields(self, tmp_path):
        """Test that missing required fields raise validation errors."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
GATEWAY_INSTANCE_ID=test-gateway
# Missing LLM_MODEL_NAME and LLM_API_KEY
EXECUTION_STRATEGY=local_socket
        """)
        
        original_config = Settings.model_config['env_file']
        Settings.model_config['env_file'] = env_file
        
        try:
            with pytest.raises(ValidationError):
                Settings()
        finally:
            Settings.model_config['env_file'] = original_config


class TestConfigurationLoading:
    """Test global configuration loading functions."""
    
    def test_get_settings_singleton(self):
        """Test that get_settings returns the same instance."""
        # Clear any existing settings
        reload_settings()
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2
    
    def test_reload_settings(self):
        """Test that reload_settings creates a new instance."""
        settings1 = get_settings()
        settings2 = reload_settings()
        
        # Should be different instances but same configuration
        assert settings1 is not settings2
        assert settings1.gateway_instance_id == settings2.gateway_instance_id