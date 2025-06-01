"""
Configuration management for AI Command Gateway.
Uses Pydantic BaseSettings for environment variable loading with strict validation.
"""

from pathlib import Path
from typing import Dict, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
import logging


class Settings(BaseSettings):
    """AI Command Gateway configuration settings."""
    
    # Gateway Identification
    gateway_instance_id: str = Field(..., description="Unique identifier for this gateway instance")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # LLM Configuration
    llm_provider: str = Field(default="openai", description="LLM provider")
    llm_model_name: str = Field(..., description="LLM model to use for command generation")
    llm_api_key: str = Field(..., description="API key for LLM service")
    llm_api_base_url: str = Field(default="https://api.openai.com/v1/", description="LLM API base URL")
    llm_system_prompt: str = Field(
        default=(
            "You are an expert assistant that translates user intents for managing services "
            "into precise Docker CLI commands. The user will provide an intent and a target "
            "Docker container name. Respond ONLY with the Docker CLI command string. "
            "Do not add any explanation or conversational fluff."
        ),
        description="System prompt for LLM command generation"
    )
    
    # Execution Strategy
    execution_strategy: str = Field(..., description="Execution strategy: local_socket or ssh")
    
    # Container Name Mappings
    container_name_for_market_predictor: str = Field(..., description="Actual container name for market-predictor")
    container_name_for_coding_ai_agent: str = Field(..., description="Actual container name for coding-ai-agent")
    container_name_for_devops_ai_agent: str = Field(..., description="Actual container name for devops-ai-agent")
    
    # SSH Configuration (optional, required if execution_strategy=ssh)
    ssh_target_host: Optional[str] = Field(default=None, description="SSH target host")
    ssh_target_user: Optional[str] = Field(default=None, description="SSH target user")
    ssh_private_key_path: Optional[str] = Field(default=None, description="Path to SSH private key")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8080, description="API port")
    cors_origins: str = Field(default="*", description="CORS allowed origins")
    
    # Timeouts and Limits
    command_timeout_seconds: int = Field(default=30, description="Command execution timeout")
    max_command_output_length: int = Field(default=10000, description="Maximum command output length")
    
    model_config = {
        'env_file': Path(__file__).parent.parent.parent / '.env',
        'case_sensitive': False,
        'extra': 'ignore'
    }
    
    def __init__(self, **kwargs):
        # Find .env file relative to this config file
        env_file = Path(__file__).parent.parent.parent / '.env'
        if not env_file.exists():
            # Try relative to current working directory
            env_file = Path('.env')
        
        if env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(env_file)
        
        super().__init__(**kwargs)
        
    @field_validator('execution_strategy')
    @classmethod
    def validate_execution_strategy(cls, v):
        """Validate execution strategy is supported."""
        if v not in ['local_socket', 'ssh']:
            raise ValueError('execution_strategy must be either "local_socket" or "ssh"')
        return v
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level is supported."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'log_level must be one of {valid_levels}')
        return v.upper()
    
    def model_post_init(self, __context) -> None:
        """Validate SSH configuration after model initialization."""
        if self.execution_strategy == 'ssh':
            if not self.ssh_target_host:
                raise ValueError('ssh_target_host is required when execution_strategy is ssh')
            if not self.ssh_target_user:
                raise ValueError('ssh_target_user is required when execution_strategy is ssh')
            if not self.ssh_private_key_path:
                raise ValueError('ssh_private_key_path is required when execution_strategy is ssh')
    
    def get_container_name_mapping(self) -> Dict[str, str]:
        """Get mapping of logical names to actual container names."""
        return {
            'market-predictor': self.container_name_for_market_predictor,
            'coding-ai-agent': self.container_name_for_coding_ai_agent,
            'devops-ai-agent': self.container_name_for_devops_ai_agent,
        }
    
    def resolve_container_name(self, logical_name: str) -> str:
        """Resolve logical service name to actual container name."""
        mapping = self.get_container_name_mapping()
        if logical_name not in mapping:
            raise ValueError(f"Unknown logical service name: {logical_name}")
        return mapping[logical_name]
    
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get settings instance (singleton pattern)."""
    global _settings
    if _settings is None:
        try:
            _settings = Settings()
            _settings.setup_logging()
        except Exception as e:
            # Log the error and re-raise to fail fast
            print(f"FATAL: Configuration loading failed: {e}")
            raise
    return _settings


def reload_settings() -> Settings:
    """Reload settings (useful for testing)."""
    global _settings
    _settings = None
    return get_settings()