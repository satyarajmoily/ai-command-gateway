"""
LLM-based Docker command generator.
Translates natural language intents into precise Docker CLI commands.
"""

import logging
from typing import Optional
from openai import OpenAI

from gateway.config.settings import get_settings
from gateway.core.models import CommandGenerationRequest, CommandGenerationResponse

logger = logging.getLogger(__name__)


class DockerCommandGenerator:
    """Generates Docker commands using LLM from natural language intents."""
    
    def __init__(self):
        """Initialize the command generator with OpenAI client."""
        self.settings = get_settings()
        self.client = OpenAI(
            api_key=self.settings.llm_api_key,
            base_url=self.settings.llm_api_base_url
        )
        
        logger.info(
            f"Docker Command Generator initialized",
            extra={
                "model": self.settings.llm_model_name,
                "provider": self.settings.llm_provider
            }
        )
    
    def generate_command(self, request: CommandGenerationRequest) -> CommandGenerationResponse:
        """
        Generate Docker command from natural language intent.
        
        Args:
            request: Command generation request with intent and container name
            
        Returns:
            CommandGenerationResponse with generated command or error
        """
        try:
            logger.info(
                f"Generating Docker command",
                extra={
                    "intent": request.intent,
                    "container": request.container_name,
                    "context": request.context
                }
            )
            
            # Build the prompt
            prompt = self._build_prompt(request)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.settings.llm_model_name,
                messages=prompt,
                max_tokens=150,
                temperature=0.1,  # Low temperature for consistent command generation
                timeout=10.0
            )
            
            # Extract the command
            command = response.choices[0].message.content.strip()
            
            # Validate the command
            if not self._validate_command(command):
                logger.warning(f"Generated command failed validation: {command}")
                return CommandGenerationResponse(
                    command="",
                    success=False,
                    error_message=f"Generated command failed validation: {command}"
                )
            
            logger.info(
                f"Successfully generated Docker command",
                extra={
                    "intent": request.intent,
                    "generated_command": command
                }
            )
            
            return CommandGenerationResponse(
                command=command,
                success=True
            )
            
        except Exception as e:
            logger.error(
                f"Failed to generate Docker command",
                extra={
                    "intent": request.intent,
                    "error": str(e)
                }
            )
            
            return CommandGenerationResponse(
                command="",
                success=False,
                error_message=f"LLM generation failed: {str(e)}"
            )
    
    def _build_prompt(self, request: CommandGenerationRequest) -> list:
        """Build the prompt for the LLM."""
        system_prompt = self.settings.llm_system_prompt
        
        # Add specific examples to improve command generation
        examples = self._get_command_examples()
        
        user_message = f"""Intent: {request.intent}
Container: {request.container_name}"""
        
        if request.context:
            user_message += f"\nContext: {request.context}"
        
        messages = [
            {"role": "system", "content": f"{system_prompt}\n\nExamples:\n{examples}"},
            {"role": "user", "content": user_message}
        ]
        
        return messages
    
    def _get_command_examples(self) -> str:
        """Get example Docker commands for different intents."""
        return """
Intent: "restart the service"
Container: "my-app"
Response: docker restart my-app

Intent: "get the last 50 lines of logs"
Container: "my-app"
Response: docker logs --tail 50 my-app

Intent: "check if the container is running"
Container: "my-app"  
Response: docker ps --filter name=my-app

Intent: "execute df -h command inside the container"
Container: "my-app"
Response: docker exec my-app df -h

Intent: "stop the service"
Container: "my-app"
Response: docker stop my-app

Intent: "start the service"
Container: "my-app"
Response: docker start my-app

Intent: "get real-time logs"
Container: "my-app"
Response: docker logs -f my-app

Intent: "check container resource usage"
Container: "my-app"
Response: docker stats --no-stream my-app

Intent: "inspect the container configuration"
Container: "my-app"
Response: docker inspect my-app

Intent: "get container processes"
Container: "my-app"
Response: docker exec my-app ps aux
"""
    
    def _validate_command(self, command: str) -> bool:
        """
        Validate that the generated command is a valid Docker command.
        
        Args:
            command: The generated command string
            
        Returns:
            True if valid, False otherwise
        """
        if not command:
            return False
        
        # Must start with 'docker'
        if not command.strip().startswith('docker '):
            return False
        
        # Extract the docker subcommand
        parts = command.strip().split()
        if len(parts) < 2:
            return False
        
        # Valid Docker subcommands for our use case (EXPANDED)
        valid_subcommands = {
            'restart', 'start', 'stop', 'logs', 'exec', 'ps', 
            'inspect', 'stats', 'top', 'port', 'diff', 'commit',
            'images', 'version', 'info', 'system'
        }
        
        subcommand = parts[1]
        if subcommand not in valid_subcommands:
            logger.warning(f"Invalid Docker subcommand: {subcommand}")
            return False
        
        # Additional validation for specific commands
        if subcommand == 'exec':
            # docker exec requires at least: docker exec <container> <command>
            if len(parts) < 4:
                return False
        
        # IMPROVED: Command should not contain truly dangerous operations
        # Fixed to not trigger on JSON formatting
        dangerous_patterns = ['rm -rf', 'rmi -f', '--privileged', 'sudo su', 'mkfs', 'fdisk']
        command_lower = command.lower()
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                logger.warning(f"Potentially dangerous command pattern detected: {pattern}")
                return False
        
        # IMPROVED: Don't flag single 'rm' or JSON formatting as dangerous
        # Only flag 'rm -rf' patterns, not 'rm' in JSON format strings
        if ' rm ' in command_lower and '-rf' in command_lower:
            logger.warning(f"Dangerous rm -rf pattern detected")
            return False
        
        return True


# Global instance for dependency injection
_command_generator: Optional[DockerCommandGenerator] = None


def get_command_generator() -> DockerCommandGenerator:
    """Get command generator instance (singleton pattern)."""
    global _command_generator
    if _command_generator is None:
        _command_generator = DockerCommandGenerator()
    return _command_generator