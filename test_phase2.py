#!/usr/bin/env python3
"""
Phase 2 validation script - tests LLM integration and execution strategies.
"""

import sys
import asyncio
import json
from pathlib import Path
from uuid import uuid4
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all Phase 2 components can be imported."""
    print("🔍 Testing imports...")
    
    try:
        from gateway.config.settings import get_settings
        from gateway.core.models import GatewayRequest, TargetResource, ActionRequest
        from gateway.core.command_generator import DockerCommandGenerator, get_command_generator
        from gateway.core.executors import LocalDockerExecutor, ExecutorFactory, get_executor
        from gateway.services.gateway_service import GatewayService, get_gateway_service
        
        print("✅ All Phase 2 imports successful")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_configuration_loading():
    """Test configuration loading with Phase 2 requirements."""
    print("\n🔍 Testing configuration loading...")
    
    try:
        from gateway.config.settings import get_settings
        
        settings = get_settings()
        
        # Test required Phase 2 settings
        required_attrs = [
            'llm_api_key', 'llm_model_name', 'llm_provider',
            'execution_strategy', 'gateway_instance_id'
        ]
        
        missing = []
        for attr in required_attrs:
            if not hasattr(settings, attr) or not getattr(settings, attr):
                missing.append(attr)
        
        if missing:
            print(f"❌ Missing required settings: {missing}")
            return False
        
        print(f"✅ Configuration loaded successfully")
        print(f"   - Gateway ID: {settings.gateway_instance_id}")
        print(f"   - LLM Model: {settings.llm_model_name}")
        print(f"   - Execution Strategy: {settings.execution_strategy}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False

def test_command_generator_initialization():
    """Test command generator initialization."""
    print("\n🔍 Testing command generator initialization...")
    
    try:
        from gateway.core.command_generator import DockerCommandGenerator
        
        # This will test OpenAI client initialization
        generator = DockerCommandGenerator()
        
        print("✅ Command generator initialized successfully")
        print(f"   - LLM Provider: {generator.settings.llm_provider}")
        print(f"   - Model: {generator.settings.llm_model_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Command generator initialization failed: {e}")
        print("   Note: This may fail if OpenAI API key is invalid")
        return False

def test_executor_factory():
    """Test executor factory functionality."""
    print("\n🔍 Testing executor factory...")
    
    try:
        from gateway.core.executors import ExecutorFactory, LocalDockerExecutor, SSHDockerExecutor
        
        executor = ExecutorFactory.create_executor()
        
        print(f"✅ Executor created: {type(executor).__name__}")
        
        # Test that it's the right type based on configuration
        from gateway.config.settings import get_settings
        settings = get_settings()
        
        if settings.execution_strategy == "local_socket":
            if not isinstance(executor, LocalDockerExecutor):
                print("❌ Wrong executor type for local_socket strategy")
                return False
        elif settings.execution_strategy == "ssh":
            if not isinstance(executor, SSHDockerExecutor):
                print("❌ Wrong executor type for ssh strategy")
                return False
        
        print(f"   - Strategy: {settings.execution_strategy}")
        return True
        
    except Exception as e:
        print(f"❌ Executor factory failed: {e}")
        return False

def test_gateway_service_initialization():
    """Test gateway service initialization."""
    print("\n🔍 Testing gateway service initialization...")
    
    try:
        from gateway.services.gateway_service import GatewayService
        
        service = GatewayService()
        
        print("✅ Gateway service initialized successfully")
        print(f"   - Gateway ID: {service.settings.gateway_instance_id}")
        print(f"   - Command Generator: {type(service.command_generator).__name__}")
        print(f"   - Executor: {type(service.executor).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Gateway service initialization failed: {e}")
        return False

async def test_request_model_creation():
    """Test creating a sample request model."""
    print("\n🔍 Testing request model creation...")
    
    try:
        from gateway.core.models import GatewayRequest, TargetResource, ActionRequest
        
        # Create a sample request
        request = GatewayRequest(
            source_agent_id="test-devops-agent",
            target_resource=TargetResource(logical_name="market-predictor"),
            action_request=ActionRequest(
                intent_or_command_description="restart the service due to high error rate"
            )
        )
        
        print("✅ Request model created successfully")
        print(f"   - Request ID: {request.request_id}")
        print(f"   - Target Service: {request.target_resource.logical_name}")
        print(f"   - Intent: {request.action_request.intent_or_command_description}")
        
        # Test JSON serialization
        request_json = request.model_dump()
        print(f"   - JSON serialization: {len(str(request_json))} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Request model creation failed: {e}")
        return False

def test_container_name_resolution():
    """Test container name resolution."""
    print("\n🔍 Testing container name resolution...")
    
    try:
        from gateway.config.settings import get_settings
        
        settings = get_settings()
        
        # Test each configured service
        test_services = ["market-predictor", "coding-ai-agent", "devops-ai-agent"]
        
        for service in test_services:
            try:
                resolved = settings.resolve_container_name(service)
                print(f"   ✅ {service} → {resolved}")
            except ValueError as e:
                print(f"   ❌ {service} → {e}")
                return False
        
        # Test unknown service
        try:
            settings.resolve_container_name("unknown-service")
            print("   ❌ Unknown service should have failed")
            return False
        except ValueError:
            print("   ✅ Unknown service properly rejected")
        
        print("✅ Container name resolution working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Container name resolution failed: {e}")
        return False

async def main():
    """Run all Phase 2 validations."""
    print("🚀 AI Command Gateway - Phase 2 LLM Integration Validation")
    print("=" * 70)
    
    validations = [
        test_imports,
        test_configuration_loading,
        test_command_generator_initialization,
        test_executor_factory,
        test_gateway_service_initialization,
        test_request_model_creation,
        test_container_name_resolution
    ]
    
    results = []
    for validation in validations:
        try:
            if asyncio.iscoroutinefunction(validation):
                result = await validation()
            else:
                result = validation()
            results.append(result)
        except Exception as e:
            print(f"❌ Validation error: {e}")
            results.append(False)
    
    print("\n" + "=" * 70)
    passed = sum(results)
    total = len(results)
    
    if all(results):
        print("🎉 PHASE 2 LLM INTEGRATION: ALL VALIDATIONS PASSED")
        print("✅ Command generator with OpenAI integration")
        print("✅ Execution strategies (Local Docker + SSH)")
        print("✅ Complete gateway service workflow")
        print("✅ Request/response model validation")
        print("✅ Container name resolution")
        print("\n🚀 Ready for integration testing with real OpenAI API!")
        print("\nNext steps:")
        print("1. Ensure OpenAI API key is valid")
        print("2. Test with actual Docker commands")
        print("3. Integration with devops-ai-agent")
        return 0
    else:
        print(f"❌ PHASE 2 LLM INTEGRATION: {passed}/{total} VALIDATIONS PASSED")
        print("🔧 Please fix issues before proceeding")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))