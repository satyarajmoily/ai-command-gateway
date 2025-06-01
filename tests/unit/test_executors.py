"""
Unit tests for command execution strategies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import subprocess
import paramiko

from gateway.core.executors import (
    LocalDockerExecutor, SSHDockerExecutor, ExecutorFactory, 
    get_executor, ExecutionStrategy
)
from gateway.core.models import ExecutionResult


class TestLocalDockerExecutor:
    """Test local Docker execution strategy."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        settings = Mock()
        settings.max_command_output_length = 1000
        settings.command_timeout_seconds = 30
        return settings
    
    @patch('gateway.core.executors.get_settings')
    def test_successful_command_execution(self, mock_get_settings, mock_settings):
        """Test successful command execution."""
        mock_get_settings.return_value = mock_settings
        
        # Mock subprocess result
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Container restarted successfully"
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result):
            executor = LocalDockerExecutor()
            result = executor.execute("docker restart test-container")
        
        assert result.status == "SUCCESS"
        assert result.exit_code == 0
        assert result.stdout == "Container restarted successfully"
        assert result.stderr == ""
    
    @patch('gateway.core.executors.get_settings')
    def test_failed_command_execution(self, mock_get_settings, mock_settings):
        """Test failed command execution."""
        mock_get_settings.return_value = mock_settings
        
        # Mock subprocess result for failure
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: No such container: test-container"
        
        with patch('subprocess.run', return_value=mock_result):
            executor = LocalDockerExecutor()
            result = executor.execute("docker restart test-container")
        
        assert result.status == "FAILURE"
        assert result.exit_code == 1
        assert result.stdout == ""
        assert "No such container" in result.stderr
    
    @patch('gateway.core.executors.get_settings')
    def test_command_timeout(self, mock_get_settings, mock_settings):
        """Test command timeout handling."""
        mock_get_settings.return_value = mock_settings
        
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("docker", 30)):
            executor = LocalDockerExecutor()
            result = executor.execute("docker restart test-container", timeout=30)
        
        assert result.status == "TIMEOUT"
        assert result.exit_code == -1
        assert "timed out" in result.stderr
    
    @patch('gateway.core.executors.get_settings')
    def test_execution_exception(self, mock_get_settings, mock_settings):
        """Test handling of execution exceptions."""
        mock_get_settings.return_value = mock_settings
        
        with patch('subprocess.run', side_effect=Exception("Execution failed")):
            executor = LocalDockerExecutor()
            result = executor.execute("docker restart test-container")
        
        assert result.status == "ERROR"
        assert result.exit_code == -1
        assert "Execution failed" in result.stderr
    
    @patch('gateway.core.executors.get_settings')
    def test_output_truncation(self, mock_get_settings, mock_settings):
        """Test output truncation for long outputs."""
        mock_settings.max_command_output_length = 50
        mock_get_settings.return_value = mock_settings
        
        # Create long output
        long_output = "A" * 100
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = long_output
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result):
            executor = LocalDockerExecutor()
            result = executor.execute("docker logs test-container")
        
        assert len(result.stdout) > 50  # Should include truncation message
        assert "OUTPUT TRUNCATED" in result.stdout
        assert "100 total characters" in result.stdout


class TestSSHDockerExecutor:
    """Test SSH Docker execution strategy."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for SSH testing."""
        settings = Mock()
        settings.ssh_target_host = "test-host"
        settings.ssh_target_user = "test-user"
        settings.ssh_private_key_path = "/path/to/key"
        settings.max_command_output_length = 1000
        return settings
    
    @patch('gateway.core.executors.get_settings')
    def test_ssh_executor_initialization(self, mock_get_settings, mock_settings):
        """Test SSH executor initialization with valid config."""
        mock_get_settings.return_value = mock_settings
        
        executor = SSHDockerExecutor()
        assert executor.settings == mock_settings
    
    @patch('gateway.core.executors.get_settings')
    def test_ssh_executor_invalid_config(self, mock_get_settings):
        """Test SSH executor fails with invalid config."""
        invalid_settings = Mock()
        invalid_settings.ssh_target_host = None
        invalid_settings.ssh_target_user = "test-user"
        invalid_settings.ssh_private_key_path = "/path/to/key"
        mock_get_settings.return_value = invalid_settings
        
        with pytest.raises(ValueError, match="SSH configuration incomplete"):
            SSHDockerExecutor()
    
    @patch('gateway.core.executors.get_settings')
    @patch('paramiko.SSHClient')
    def test_successful_ssh_execution(self, mock_ssh_client_class, mock_get_settings, mock_settings):
        """Test successful SSH command execution."""
        mock_get_settings.return_value = mock_settings
        
        # Mock SSH client and execution
        mock_client = Mock()
        mock_ssh_client_class.return_value = mock_client
        
        mock_stdout = Mock()
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_stdout.read.return_value = b"Container restarted"
        
        mock_stderr = Mock()
        mock_stderr.read.return_value = b""
        
        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)
        
        executor = SSHDockerExecutor()
        result = executor.execute("docker restart test-container")
        
        assert result.status == "SUCCESS"
        assert result.exit_code == 0
        assert result.stdout == "Container restarted"
        assert result.stderr == ""
        
        # Verify SSH connection was made
        mock_client.connect.assert_called_once_with(
            hostname="test-host",
            username="test-user", 
            key_filename="/path/to/key",
            timeout=10
        )
        mock_client.close.assert_called_once()
    
    @patch('gateway.core.executors.get_settings')
    @patch('paramiko.SSHClient')
    def test_failed_ssh_execution(self, mock_ssh_client_class, mock_get_settings, mock_settings):
        """Test failed SSH command execution."""
        mock_get_settings.return_value = mock_settings
        
        mock_client = Mock()
        mock_ssh_client_class.return_value = mock_client
        
        mock_stdout = Mock()
        mock_stdout.channel.recv_exit_status.return_value = 1
        mock_stdout.read.return_value = b""
        
        mock_stderr = Mock()
        mock_stderr.read.return_value = b"No such container"
        
        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)
        
        executor = SSHDockerExecutor()
        result = executor.execute("docker restart test-container")
        
        assert result.status == "FAILURE"
        assert result.exit_code == 1
        assert "No such container" in result.stderr
    
    @patch('gateway.core.executors.get_settings')
    @patch('paramiko.SSHClient')
    def test_ssh_connection_failure(self, mock_ssh_client_class, mock_get_settings, mock_settings):
        """Test SSH connection failure handling."""
        mock_get_settings.return_value = mock_settings
        
        mock_client = Mock()
        mock_ssh_client_class.return_value = mock_client
        mock_client.connect.side_effect = paramiko.SSHException("Connection failed")
        
        executor = SSHDockerExecutor()
        result = executor.execute("docker restart test-container")
        
        assert result.status == "SSH_ERROR"
        assert result.exit_code == -1
        assert "Connection failed" in result.stderr


class TestExecutorFactory:
    """Test executor factory functionality."""
    
    @patch('gateway.core.executors.get_settings')
    def test_create_local_executor(self, mock_get_settings):
        """Test creating local executor."""
        mock_settings = Mock()
        mock_settings.execution_strategy = "local_socket"
        mock_settings.max_command_output_length = 1000
        mock_get_settings.return_value = mock_settings
        
        executor = ExecutorFactory.create_executor()
        assert isinstance(executor, LocalDockerExecutor)
    
    @patch('gateway.core.executors.get_settings')
    def test_create_ssh_executor(self, mock_get_settings):
        """Test creating SSH executor."""
        mock_settings = Mock()
        mock_settings.execution_strategy = "ssh"
        mock_settings.ssh_target_host = "test-host"
        mock_settings.ssh_target_user = "test-user"
        mock_settings.ssh_private_key_path = "/path/to/key"
        mock_settings.max_command_output_length = 1000
        mock_get_settings.return_value = mock_settings
        
        executor = ExecutorFactory.create_executor()
        assert isinstance(executor, SSHDockerExecutor)
    
    @patch('gateway.core.executors.get_settings')
    def test_create_executor_invalid_strategy(self, mock_get_settings):
        """Test factory with invalid execution strategy."""
        mock_settings = Mock()
        mock_settings.execution_strategy = "invalid_strategy"
        mock_get_settings.return_value = mock_settings
        
        with pytest.raises(ValueError, match="Unsupported execution strategy"):
            ExecutorFactory.create_executor()


class TestExecutorSingleton:
    """Test executor singleton pattern."""
    
    def test_get_executor_singleton(self):
        """Test that get_executor returns the same instance."""
        # Clear the global instance first
        import gateway.core.executors
        gateway.core.executors._executor = None
        
        mock_settings = Mock()
        mock_settings.execution_strategy = "local_socket"
        mock_settings.max_command_output_length = 1000
        
        with patch('gateway.core.executors.get_settings', return_value=mock_settings):
            executor1 = get_executor()
            executor2 = get_executor()
            
            assert executor1 is executor2