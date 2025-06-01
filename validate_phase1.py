#!/usr/bin/env python3
"""
Phase 1 validation script - tests basic structure and configuration without external dependencies.
"""

import sys
import os
from pathlib import Path

def validate_directory_structure():
    """Validate that all required directories and files exist."""
    print("🔍 Validating directory structure...")
    
    base_path = Path(__file__).parent
    required_paths = [
        "src/gateway/__init__.py",
        "src/gateway/api/__init__.py",
        "src/gateway/config/__init__.py",
        "src/gateway/core/__init__.py",
        "src/gateway/services/__init__.py",
        "tests/unit/__init__.py",
        "requirements.txt",
        ".gitignore",
        ".env",
        ".env.template",
        "memory-bank/projectbrief.md",
        "memory-bank/progress.md"
    ]
    
    missing = []
    for path in required_paths:
        if not (base_path / path).exists():
            missing.append(path)
    
    if missing:
        print(f"❌ Missing files: {missing}")
        return False
    
    print("✅ All required files and directories exist")
    return True

def validate_configuration_loading():
    """Test configuration loading without external dependencies."""
    print("\n🔍 Validating configuration system...")
    
    # Add src to path
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    
    try:
        # Test imports
        from gateway.config.settings import Settings
        from gateway.core.models import GatewayRequest, GatewayResponse
        
        print("✅ All imports successful")
        
        # Test configuration with current .env
        settings = Settings()
        print(f"✅ Configuration loaded: gateway_id={settings.gateway_instance_id}")
        print(f"✅ Execution strategy: {settings.execution_strategy}")
        
        # Test container name resolution
        container_mappings = settings.get_container_name_mapping()
        print(f"✅ Container mappings: {len(container_mappings)} services configured")
        
        # Test specific resolution
        resolved = settings.resolve_container_name("market-predictor")
        print(f"✅ Container resolution: market-predictor -> {resolved}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False

def validate_api_models():
    """Test API model creation and validation."""
    print("\n🔍 Validating API models...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from gateway.core.models import (
            GatewayRequest, GatewayResponse, TargetResource, 
            ActionRequest, HealthStatus
        )
        from uuid import uuid4
        from datetime import datetime
        
        # Test request model
        request = GatewayRequest(
            source_agent_id="test-agent",
            target_resource=TargetResource(logical_name="market-predictor"),
            action_request=ActionRequest(intent_or_command_description="restart the service")
        )
        print(f"✅ Request model: {request.request_id}")
        
        # Test response model  
        response = GatewayResponse(
            response_to_request_id=request.request_id,
            gateway_id="test-gateway",
            overall_status="FOUNDATION_READY",
            summary_message_from_gateway="Test message"
        )
        print(f"✅ Response model: {response.overall_status}")
        
        # Test health status
        health = HealthStatus(status="healthy")
        print(f"✅ Health model: {health.status}")
        
        return True
        
    except Exception as e:
        print(f"❌ API model validation failed: {e}")
        return False

def main():
    """Run all Phase 1 validations."""
    print("🚀 AI Command Gateway - Phase 1 Validation")
    print("=" * 50)
    
    validations = [
        validate_directory_structure,
        validate_configuration_loading,
        validate_api_models
    ]
    
    results = []
    for validation in validations:
        try:
            result = validation()
            results.append(result)
        except Exception as e:
            print(f"❌ Validation error: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    if all(results):
        print("🎉 Phase 1 Foundation: ALL VALIDATIONS PASSED")
        print("✅ Ready to proceed to Phase 2: LLM Integration")
        return 0
    else:
        print("❌ Phase 1 Foundation: SOME VALIDATIONS FAILED")
        print("🔧 Please fix issues before proceeding to Phase 2")
        return 1

if __name__ == "__main__":
    sys.exit(main())