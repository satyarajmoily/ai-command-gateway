"""
Command execution strategies for different environments.
Supports local Docker socket and SSH remote execution.
"""

import subprocess
import logging
from abc import ABC, abstractmethod
from typing import Optional
import paramiko
from pathlib import Path

from gateway.config.settings import get_settings
from gateway.core.models import ExecutionResult

logger = logging.getLogger(__name__)


class ExecutionStrategy(ABC):
    """Abstract base class for command execution strategies."""
    
    @abstractmethod
    def execute(self, command: str, timeout: int = 30) -> ExecutionResult:
        """
        Execute a Docker command.
        
        Args:
            command: Docker command to execute
            timeout: Execution timeout in seconds
            
        Returns:
            ExecutionResult with command output and status
        """
        pass


class LocalDockerExecutor(ExecutionStrategy):
    """Executes Docker commands via local Docker socket."""
    
    def __init__(self):
        """Initialize local Docker executor."""
        self.settings = get_settings()
        logger.info("Local Docker executor initialized")
    
    def execute(self, command: str, timeout: int = 30) -> ExecutionResult:
        """
        Execute Docker command locally via Docker socket.
        
        Args:
            command: Docker command to execute
            timeout: Execution timeout in seconds
            
        Returns:
            ExecutionResult with command output
        """
        logger.info(f"Executing local Docker command: {command}")
        
        try:
            # Execute the command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Truncate output if too long
            stdout = self._truncate_output(result.stdout)
            stderr = self._truncate_output(result.stderr)
            
            execution_result = ExecutionResult(
                status="SUCCESS" if result.returncode == 0 else "FAILURE",
                exit_code=result.returncode,
                stdout=stdout,
                stderr=stderr
            )
            
            logger.info(
                f"Local command execution completed",
                extra={
                    "command": command,
                    "exit_code": result.returncode,
                    "status": execution_result.status
                }
            )
            
            return execution_result
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout} seconds: {command}")
            return ExecutionResult(
                status="TIMEOUT",
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds"
            )
        except Exception as e:
            logger.error(f"Local command execution failed: {e}")
            return ExecutionResult(
                status="ERROR",
                exit_code=-1,
                stdout="",
                stderr=f"Execution error: {str(e)}"
            )
    
    def _truncate_output(self, output: str) -> str:
        """Truncate output if it exceeds maximum length."""
        max_length = self.settings.max_command_output_length
        if len(output) > max_length:
            truncated = output[:max_length]
            truncated += f"\n\n[OUTPUT TRUNCATED - {len(output)} total characters, showing first {max_length}]"
            return truncated
        return output


class SSHDockerExecutor(ExecutionStrategy):
    """Executes Docker commands via SSH on remote host."""
    
    def __init__(self):
        """Initialize SSH Docker executor."""
        self.settings = get_settings()
        
        # Validate SSH configuration
        if not all([
            self.settings.ssh_target_host,
            self.settings.ssh_target_user,
            self.settings.ssh_private_key_path
        ]):
            raise ValueError("SSH configuration incomplete")
        
        logger.info(
            f"SSH Docker executor initialized",
            extra={
                "host": self.settings.ssh_target_host,
                "user": self.settings.ssh_target_user
            }
        )
    
    def execute(self, command: str, timeout: int = 30) -> ExecutionResult:
        """
        Execute Docker command via SSH on remote host.
        
        Args:
            command: Docker command to execute
            timeout: Execution timeout in seconds
            
        Returns:
            ExecutionResult with command output
        """
        logger.info(
            f"Executing SSH Docker command",
            extra={
                "command": command,
                "host": self.settings.ssh_target_host
            }
        )
        
        client = None
        try:
            # Create SSH client
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect to remote host
            client.connect(
                hostname=self.settings.ssh_target_host,
                username=self.settings.ssh_target_user,
                key_filename=self.settings.ssh_private_key_path,
                timeout=10
            )
            
            # Execute command
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            
            # Get results
            exit_code = stdout.channel.recv_exit_status()
            stdout_text = stdout.read().decode('utf-8')
            stderr_text = stderr.read().decode('utf-8')
            
            # Truncate output if too long
            stdout_text = self._truncate_output(stdout_text)
            stderr_text = self._truncate_output(stderr_text)
            
            execution_result = ExecutionResult(
                status="SUCCESS" if exit_code == 0 else "FAILURE",
                exit_code=exit_code,
                stdout=stdout_text,
                stderr=stderr_text
            )
            
            logger.info(
                f"SSH command execution completed",
                extra={
                    "command": command,
                    "host": self.settings.ssh_target_host,
                    "exit_code": exit_code,
                    "status": execution_result.status
                }
            )
            
            return execution_result
            
        except paramiko.SSHException as e:
            logger.error(f"SSH connection failed: {e}")
            return ExecutionResult(
                status="SSH_ERROR",
                exit_code=-1,
                stdout="",
                stderr=f"SSH connection failed: {str(e)}"
            )
        except Exception as e:
            logger.error(f"SSH command execution failed: {e}")
            return ExecutionResult(
                status="ERROR",
                exit_code=-1,
                stdout="",
                stderr=f"SSH execution error: {str(e)}"
            )
        finally:
            if client:
                client.close()
    
    def _truncate_output(self, output: str) -> str:
        """Truncate output if it exceeds maximum length."""
        max_length = self.settings.max_command_output_length
        if len(output) > max_length:
            truncated = output[:max_length]
            truncated += f"\n\n[OUTPUT TRUNCATED - {len(output)} total characters, showing first {max_length}]"
            return truncated
        return output


class ExecutorFactory:
    """Factory for creating execution strategy instances."""
    
    @staticmethod
    def create_executor() -> ExecutionStrategy:
        """
        Create appropriate executor based on configuration.
        
        Returns:
            ExecutionStrategy instance
            
        Raises:
            ValueError: If execution strategy is not supported
        """
        settings = get_settings()
        
        if settings.execution_strategy == "local_socket":
            return LocalDockerExecutor()
        elif settings.execution_strategy == "ssh":
            return SSHDockerExecutor()
        else:
            raise ValueError(f"Unsupported execution strategy: {settings.execution_strategy}")


# Global instance for dependency injection
_executor: Optional[ExecutionStrategy] = None


def get_executor() -> ExecutionStrategy:
    """Get executor instance (singleton pattern)."""
    global _executor
    if _executor is None:
        _executor = ExecutorFactory.create_executor()
    return _executor