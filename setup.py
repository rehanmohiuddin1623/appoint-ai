#!/usr/bin/env python3
"""
Installation and Setup Script for Medical Appointment Booking AI Agent
======================================================================

This script helps set up the development environment and install dependencies.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Error: {result.stderr}")
            return False
        print(f"✅ {description} completed successfully")
        return True
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def create_virtual_environment():
    """Create a virtual environment"""
    venv_path = Path("venv")
    if venv_path.exists():
        print("📦 Virtual environment already exists")
        return True
    
    return run_command("python -m venv venv", "Creating virtual environment")

def activate_and_install():
    """Install dependencies in virtual environment"""
    if sys.platform == "win32":
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
    else:
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
    
    # Upgrade pip first
    if not run_command(f"{pip_cmd} install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install requirements
    return run_command(f"{pip_cmd} install -r requirements.txt", "Installing dependencies")

def setup_environment_file():
    """Create .env file if it doesn't exist with proper values"""
    env_file = Path(".env")
    if env_file.exists():
        print("📝 .env file already exists")
        return True
    
    env_content = """# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# FastAPI Configuration  
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=True

# Audio Configuration
AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=1

# TTS Configuration
TTS_PROVIDER=openai
TTS_VOICE=alloy
TTS_SPEED=1.0

# Appointment Configuration
DEFAULT_APPOINTMENT_DURATION=30  # minutes
"""
    
    try:
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Created .env file")
        print("📝 Please update your OPENAI_API_KEY in the .env file")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def main():
    """Main setup function"""
    print("🏥 Medical Appointment Booking AI Agent - Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    if not create_virtual_environment():
        print("❌ Failed to create virtual environment")
        sys.exit(1)
    
    # Install dependencies
    if not activate_and_install():
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Setup environment file
    if not setup_environment_file():
        print("❌ Failed to setup environment file")
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next Steps:")
    print("1. Update your .env file with your OpenAI API key")
    print("2. Activate the virtual environment:")
    if sys.platform == "win32":
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("3. Run the application:")
    print("   python main.py")
    print("\n📖 API Documentation will be available at:")
    print("   http://localhost:8000/docs")

if __name__ == "__main__":
    main()
