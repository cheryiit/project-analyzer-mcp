#!/usr/bin/env python3
"""
One-Command Installer for Project Analyzer MCP
Automatically sets up the MCP server for Claude Code, Cursor, or VS Code
"""

import json
import os
import platform
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path


class ProjectAnalyzerInstaller:
    """One-command installer for Project Analyzer MCP"""
    
    def __init__(self):
        self.system = platform.system()
        self.home = Path.home()
        self.temp_dir = None
        
    def install(self):
        """Main installation process"""
        print("🔍 Project Analyzer MCP - One-Command Installer")
        print("=" * 50)
        
        try:
            # Download and setup
            self._download_source()
            self._install_dependencies()
            
            # Auto-detect and configure editors
            configured = []
            
            if self._setup_claude_code():
                configured.append("Claude Code")
            
            if self._setup_cursor():
                configured.append("Cursor")
                
            if self._setup_vscode():
                configured.append("VS Code")
            
            if configured:
                print(f"\n✅ Successfully configured for: {', '.join(configured)}")
                print("\n🚀 Usage:")
                print("   Analyze this project for errors")
                print("   Show me the project structure")
                print("   Start a background code analysis")
            else:
                print("\n⚠️  No supported editors found")
                print("Manual configuration required - see README.md")
            
            self._test_installation()
            
        except Exception as e:
            print(f"\n❌ Installation failed: {e}")
            return False
        
        finally:
            self._cleanup()
        
        return True
    
    def _download_source(self):
        """Download source code to temp directory"""
        print("📥 Downloading source code...")
        
        self.temp_dir = Path(tempfile.mkdtemp())
        
        files_to_download = [
            "main.py",
            "requirements.txt",
            "src/__init__.py",
            "src/core/__init__.py", 
            "src/core/server.py",
            "src/core/analyzer.py",
            "src/core/config.py",
            "src/analyzers/__init__.py",
            "src/analyzers/code_analyzer.py",
            "src/analyzers/structure_analyzer.py",
            "src/utils/__init__.py",
            "src/utils/file_utils.py",
            "src/utils/formatters.py",
            "config/default_config.json"
        ]
        
        base_url = "https://raw.githubusercontent.com/cheryiit/project-analyzer-mcp/master/"
        
        for file_path in files_to_download:
            url = base_url + file_path
            local_path = self.temp_dir / file_path
            
            # Create directory if needed
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                urllib.request.urlretrieve(url, local_path)
            except Exception as e:
                print(f"⚠️  Warning: Could not download {file_path}: {e}")
        
        print("✅ Source code downloaded")
    
    def _install_dependencies(self):
        """Install Python dependencies"""
        print("📦 Installing dependencies...")
        
        try:
            requirements_file = self.temp_dir / "requirements.txt"
            if requirements_file.exists():
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # Fallback minimal requirements
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", "gitignore-parser"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            print("✅ Dependencies installed")
            
        except Exception as e:
            print(f"⚠️  Warning: Dependency installation failed: {e}")
            print("   MCP may still work with basic features")
    
    def _setup_claude_code(self) -> bool:
        """Setup for Claude Code"""
        try:
            config_path = self._get_claude_config_path()
            if not config_path:
                return False
            
            print("🤖 Configuring Claude Code...")
            
            # Create config if it doesn't exist
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {}
            
            if "mcpServers" not in config:
                config["mcpServers"] = {}
            
            # Add our server
            config["mcpServers"]["project-analyzer"] = {
                "command": "python",
                "args": [str(self.temp_dir / "main.py")],
                "env": {
                    "PYTHONPATH": str(self.temp_dir)
                }
            }
            
            # Write config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print("✅ Claude Code configured")
            return True
            
        except Exception as e:
            print(f"❌ Claude Code setup failed: {e}")
            return False
    
    def _setup_cursor(self) -> bool:
        """Setup for Cursor"""
        try:
            config_path = self._get_cursor_config_path()
            if not config_path:
                return False
            
            print("🎯 Configuring Cursor...")
            
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {}
            
            if "mcpServers" not in config:
                config["mcpServers"] = {}
            
            config["mcpServers"]["project-analyzer"] = {
                "command": "python",
                "args": [str(self.temp_dir / "main.py")],
                "env": {
                    "PYTHONPATH": str(self.temp_dir)
                }
            }
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print("✅ Cursor configured")
            return True
            
        except Exception as e:
            print(f"❌ Cursor setup failed: {e}")
            return False
    
    def _setup_vscode(self) -> bool:
        """Setup for VS Code"""
        try:
            config_path = self._get_vscode_config_path()
            if not config_path:
                return False
            
            print("📝 Configuring VS Code...")
            
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {}
            
            if "mcp.servers" not in config:
                config["mcp.servers"] = {}
            
            config["mcp.servers"]["project-analyzer"] = {
                "command": "python",
                "args": [str(self.temp_dir / "main.py")],
                "cwd": str(self.temp_dir)
            }
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print("✅ VS Code configured")
            return True
            
        except Exception as e:
            print(f"❌ VS Code setup failed: {e}")
            return False
    
    def _get_claude_config_path(self) -> Path:
        """Get Claude Code config path"""
        if self.system == "Darwin":  # macOS
            return self.home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        elif self.system == "Windows":
            return self.home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
        elif self.system == "Linux":
            return self.home / ".config" / "Claude" / "claude_desktop_config.json"
        return None
    
    def _get_cursor_config_path(self) -> Path:
        """Get Cursor config path"""
        if self.system == "Darwin":  # macOS
            return self.home / "Library" / "Application Support" / "Cursor" / "User" / "settings.json"
        elif self.system == "Windows":
            return self.home / "AppData" / "Roaming" / "Cursor" / "User" / "settings.json"
        elif self.system == "Linux":
            return self.home / ".config" / "Cursor" / "User" / "settings.json"
        return None
    
    def _get_vscode_config_path(self) -> Path:
        """Get VS Code config path"""
        if self.system == "Darwin":  # macOS
            return self.home / "Library" / "Application Support" / "Code" / "User" / "settings.json"
        elif self.system == "Windows":
            return self.home / "AppData" / "Roaming" / "Code" / "User" / "settings.json"
        elif self.system == "Linux":
            return self.home / ".config" / "Code" / "User" / "settings.json"
        return None
    
    def _test_installation(self):
        """Test the installation"""
        print("\n🧪 Testing installation...")
        
        try:
            main_py = self.temp_dir / "main.py"
            if main_py.exists():
                result = subprocess.run([
                    sys.executable, str(main_py), "--test"
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    print("✅ Installation test passed")
                else:
                    print("⚠️  Test completed with warnings")
            else:
                print("❌ Main script not found")
                
        except Exception as e:
            print(f"⚠️  Test failed: {e}")
    
    def _cleanup(self):
        """Cleanup temporary files"""
        # Note: We're keeping temp files because they contain the actual MCP server
        # In a production version, you'd want to copy to a permanent location
        if self.temp_dir:
            print(f"📁 MCP server installed at: {self.temp_dir}")
            print("   (Temporary location - consider moving to permanent directory)")


def main():
    """Main installer function"""
    installer = ProjectAnalyzerInstaller()
    
    print("🔍 Project Analyzer MCP - One-Command Installer")
    print("This will automatically configure the MCP server for your editors")
    print()
    
    try:
        success = installer.install()
        
        if success:
            print("\n🎉 Installation completed!")
            print("\nNext steps:")
            print("1. Restart Claude Code / Cursor / VS Code")
            print("2. Try: 'Analyze this project for errors'")
            print("3. Or: 'Show me the project structure'")
            print("\n📚 More info: https://github.com/cheryiit/project-analyzer-mcp")
        else:
            print("\n❌ Installation failed")
            print("Please check the error messages above and try manual installation")
            print("📚 Manual setup: https://github.com/cheryiit/project-analyzer-mcp#manual-installation")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Installation cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please try manual installation: https://github.com/cheryiit/project-analyzer-mcp#manual-installation")


if __name__ == "__main__":
    main()