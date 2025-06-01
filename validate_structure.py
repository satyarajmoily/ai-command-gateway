#!/usr/bin/env python3
"""
Basic structure validation script - no external dependencies required.
"""

import os
import sys
from pathlib import Path

def validate_directory_structure():
    """Validate that all required directories and files exist."""
    print("🔍 Validating directory structure...")
    
    base_path = Path(__file__).parent
    required_paths = [
        # Source structure
        "src/gateway/__init__.py",
        "src/gateway/api/__init__.py", 
        "src/gateway/api/main.py",
        "src/gateway/config/__init__.py",
        "src/gateway/config/settings.py",
        "src/gateway/core/__init__.py",
        "src/gateway/core/models.py",
        "src/gateway/services/__init__.py",
        
        # Test structure
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/unit/test_config.py",
        "tests/unit/test_api.py",
        
        # Configuration files
        "requirements.txt",
        ".gitignore",
        ".env",
        ".env.template",
        
        # Documentation
        "README.md",
        "memory-bank/projectbrief.md",
        "memory-bank/productContext.md",
        "memory-bank/activeContext.md",
        "memory-bank/systemPatterns.md",
        "memory-bank/techContext.md",
        "memory-bank/progress.md",
        
        # Setup scripts
        "setup_dev.py",
        "validate_phase1.py"
    ]
    
    missing = []
    for path in required_paths:
        if not (base_path / path).exists():
            missing.append(path)
    
    if missing:
        print(f"❌ Missing files:")
        for file in missing:
            print(f"   - {file}")
        return False
    
    print("✅ All required files and directories exist")
    return True

def validate_file_contents():
    """Validate key file contents."""
    print("\n🔍 Validating file contents...")
    
    base_path = Path(__file__).parent
    
    # Check requirements.txt has essential dependencies
    requirements = (base_path / "requirements.txt").read_text()
    essential_deps = ["fastapi", "pydantic", "uvicorn", "openai", "paramiko"]
    
    missing_deps = []
    for dep in essential_deps:
        if dep not in requirements.lower():
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"❌ Missing dependencies in requirements.txt: {missing_deps}")
        return False
    
    print("✅ All essential dependencies present in requirements.txt")
    
    # Check .env has required configuration
    env_content = (base_path / ".env").read_text()
    required_env_vars = [
        "GATEWAY_INSTANCE_ID",
        "EXECUTION_STRATEGY", 
        "LLM_MODEL_NAME",
        "CONTAINER_NAME_FOR_MARKET_PREDICTOR"
    ]
    
    missing_env = []
    for var in required_env_vars:
        if var not in env_content:
            missing_env.append(var)
    
    if missing_env:
        print(f"❌ Missing environment variables in .env: {missing_env}")
        return False
    
    print("✅ All required environment variables present in .env")
    
    return True

def validate_python_syntax():
    """Validate Python syntax of key files."""
    print("\n🔍 Validating Python syntax...")
    
    base_path = Path(__file__).parent
    python_files = [
        "src/gateway/config/settings.py",
        "src/gateway/core/models.py",
        "src/gateway/api/main.py",
        "tests/unit/test_config.py",
        "tests/unit/test_api.py"
    ]
    
    errors = []
    for file_path in python_files:
        try:
            with open(base_path / file_path, 'r') as f:
                compile(f.read(), file_path, 'exec')
            print(f"✅ {file_path} - syntax OK")
        except SyntaxError as e:
            errors.append(f"{file_path}: {e}")
            print(f"❌ {file_path} - syntax error: {e}")
        except Exception as e:
            errors.append(f"{file_path}: {e}")
            print(f"❌ {file_path} - error: {e}")
    
    if errors:
        print(f"\n❌ Python syntax errors found:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    print("✅ All Python files have valid syntax")
    return True

def validate_api_structure():
    """Validate API structure and endpoints."""
    print("\n🔍 Validating API structure...")
    
    base_path = Path(__file__).parent
    main_py = (base_path / "src/gateway/api/main.py").read_text()
    
    # Check for required endpoints
    required_endpoints = [
        "/health",
        "/execute-docker-command"
    ]
    
    missing_endpoints = []
    for endpoint in required_endpoints:
        if endpoint not in main_py:
            missing_endpoints.append(endpoint)
    
    if missing_endpoints:
        print(f"❌ Missing API endpoints: {missing_endpoints}")
        return False
    
    print("✅ All required API endpoints present")
    
    # Check for FastAPI app creation
    if "app = FastAPI" not in main_py:
        print("❌ FastAPI app not properly initialized")
        return False
    
    print("✅ FastAPI application properly initialized")
    return True

def main():
    """Run all structure validations."""
    print("🚀 AI Command Gateway - Structure Validation")
    print("=" * 60)
    
    validations = [
        validate_directory_structure,
        validate_file_contents,
        validate_python_syntax,
        validate_api_structure
    ]
    
    results = []
    for validation in validations:
        try:
            result = validation()
            results.append(result)
        except Exception as e:
            print(f"❌ Validation error: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    if all(results):
        print("🎉 PHASE 1 FOUNDATION: ALL STRUCTURE VALIDATIONS PASSED")
        print("✅ Complete directory structure")
        print("✅ Valid Python syntax in all files") 
        print("✅ Proper configuration files")
        print("✅ FastAPI application structure")
        print("✅ Unit test framework ready")
        print("\n🚀 Ready to proceed to Phase 2: LLM Integration")
        print("\nNext steps:")
        print("1. Run: python setup_dev.py")
        print("2. Activate venv: source venv/bin/activate") 
        print("3. Start Phase 2 implementation")
        return 0
    else:
        print("❌ PHASE 1 FOUNDATION: STRUCTURE VALIDATION FAILED")
        print("🔧 Please fix issues before proceeding")
        return 1

if __name__ == "__main__":
    sys.exit(main())