#!/usr/bin/env python3
"""
Development environment setup script.
Creates virtual environment and installs dependencies.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    """Setup development environment."""
    print("🚀 AI Command Gateway - Development Setup")
    print("=" * 50)
    
    base_path = Path(__file__).parent
    venv_path = base_path / "venv"
    
    # Check if virtual environment exists
    if venv_path.exists():
        print("ℹ️  Virtual environment already exists")
    else:
        # Create virtual environment
        if not run_command(f"python3 -m venv {venv_path}", "Creating virtual environment"):
            return 1
    
    # Install dependencies
    pip_path = venv_path / "bin" / "pip"
    requirements_path = base_path / "requirements.txt"
    
    if not run_command(f"{pip_path} install -r {requirements_path}", "Installing dependencies"):
        return 1
    
    print("\n" + "=" * 50)
    print("🎉 Development environment setup complete!")
    print("\nTo activate the environment:")
    print(f"source {venv_path}/bin/activate")
    print("\nTo run the service:")
    print("python -m uvicorn gateway.api.main:app --reload --port 8080")
    print("\nTo run tests:")
    print("python -m pytest tests/ -v")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())