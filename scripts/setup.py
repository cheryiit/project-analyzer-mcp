#!/usr/bin/env python3
"""Setup script for the Project Analyzer MCP Server"""

import subprocess
import sys
from pathlib import Path


def install_requirements():
    """Install Python requirements"""
    requirements_file = Path(__file__).parent.parent / "requirements.txt"
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False


def test_installation():
    """Test the installation"""
    try:
        # Import the main modules to check they work
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        
        from src.core.server import ProjectAnalyzerMCPServer
        from src.core.config import ProjectAnalyzerConfig
        
        # Create a test instance
        server = ProjectAnalyzerMCPServer()
        config = server.config
        
        print("✅ Installation test passed")
        print(f"   - Server version: 2.0.0")
        print(f"   - Background mode: {'enabled' if config.enable_background_mode else 'disabled'}")
        print(f"   - Max concurrent analyses: {config.max_concurrent_analyses}")
        return True
        
    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        return False


def main():
    """Main setup function"""
    print("🔧 Setting up Project Analyzer MCP Server v2.0...")
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Test installation
    if not test_installation():
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\nUsage:")
    print("  python main.py --test          # Run tests")
    print("  python main.py --async-test    # Test async functionality")
    print("  python main.py                 # Start server")


if __name__ == "__main__":
    main()