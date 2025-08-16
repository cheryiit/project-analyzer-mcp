#!/usr/bin/env python3
"""
Easy MCP Setup for Claude Code, Cursor, and other editors
Bu script MCP server'ı farklı editörlere kolayca entegre etmek için kullanılır.
"""

import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional


class MCPSetup:
    """MCP server kurulum ve konfigürasyon yöneticisi"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.server_path = self.project_root / "main.py"
        
    def setup_claude_code(self) -> bool:
        """Claude Code için MCP kurulumu"""
        print("🤖 Setting up MCP for Claude Code...")
        
        try:
            # Claude MCP server ekle
            cmd = [
                "claude", "mcp", "add", "project-analyzer",
                "python", str(self.server_path.absolute())
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Claude Code MCP integration successful!")
                print("Usage in Claude Code: project_structure, analyze_files, analyze_code")
                return True
            else:
                print(f"❌ Claude Code setup failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Claude Code setup error: {e}")
            return False
    
    def setup_cursor(self) -> bool:
        """Cursor için MCP kurulumu"""
        print("🎯 Setting up MCP for Cursor...")
        
        try:
            # Cursor MCP config dosyası
            cursor_config = self._get_cursor_config_path()
            if not cursor_config:
                print("❌ Cursor config path not found")
                return False
            
            config_data = {
                "mcpServers": {
                    "project-analyzer": {
                        "command": "python",
                        "args": [str(self.server_path.absolute())],
                        "env": {
                            "PYTHONPATH": str(self.project_root)
                        }
                    }
                }
            }
            
            # Mevcut config varsa birleştir
            if cursor_config.exists():
                with open(cursor_config, 'r') as f:
                    existing = json.load(f)
                if "mcpServers" in existing:
                    existing["mcpServers"].update(config_data["mcpServers"])
                    config_data = existing
                else:
                    config_data.update(existing)
            
            # Config dosyasını yaz
            cursor_config.parent.mkdir(parents=True, exist_ok=True)
            with open(cursor_config, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            print("✅ Cursor MCP integration successful!")
            print(f"Config file: {cursor_config}")
            return True
            
        except Exception as e:
            print(f"❌ Cursor setup error: {e}")
            return False
    
    def setup_vscode(self) -> bool:
        """VS Code için MCP kurulumu"""
        print("📝 Setting up MCP for VS Code...")
        
        try:
            vscode_settings = self._get_vscode_settings_path()
            if not vscode_settings:
                print("❌ VS Code settings path not found")
                return False
            
            settings_data = {
                "mcp.servers": {
                    "project-analyzer": {
                        "command": "python",
                        "args": [str(self.server_path.absolute())],
                        "cwd": str(self.project_root)
                    }
                }
            }
            
            # Mevcut settings varsa birleştir
            if vscode_settings.exists():
                with open(vscode_settings, 'r') as f:
                    existing = json.load(f)
                existing.update(settings_data)
                settings_data = existing
            
            # Settings dosyasını yaz
            vscode_settings.parent.mkdir(parents=True, exist_ok=True)
            with open(vscode_settings, 'w') as f:
                json.dump(settings_data, f, indent=2)
            
            print("✅ VS Code MCP integration successful!")
            print(f"Settings file: {vscode_settings}")
            return True
            
        except Exception as e:
            print(f"❌ VS Code setup error: {e}")
            return False
    
    def setup_generic_mcp(self) -> Dict[str, Any]:
        """Generic MCP konfigürasyonu döndür"""
        return {
            "name": "project-analyzer-mcp",
            "description": "Enhanced Python-based MCP server for comprehensive project analysis",
            "version": "2.0.0",
            "server": {
                "command": "python",
                "args": [str(self.server_path.absolute())],
                "env": {
                    "PYTHONPATH": str(self.project_root)
                }
            },
            "tools": [
                "project_structure",
                "analyze_files", 
                "analyze_code",
                "configure_analyzer",
                "get_stats",
                "start_background_task",
                "get_background_result"
            ],
            "capabilities": {
                "async_support": True,
                "background_tasks": True,
                "file_analysis": True,
                "code_analysis": True,
                "project_structure": True
            }
        }
    
    def create_integration_guide(self) -> None:
        """Entegrasyon kılavuzu oluştur"""
        guide_content = """
# Project Analyzer MCP - Integration Guide

## Quick Setup

### Claude Code
```bash
python setup_mcp.py --claude-code
```

### Cursor
```bash
python setup_mcp.py --cursor
```

### VS Code
```bash
python setup_mcp.py --vscode
```

## Manual Setup

### Claude Code
```bash
claude mcp add project-analyzer python main.py
```

### Cursor
Add to your Cursor config:
```json
{
  "mcpServers": {
    "project-analyzer": {
      "command": "python",
      "args": ["main.py"],
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

### VS Code
Add to settings.json:
```json
{
  "mcp.servers": {
    "project-analyzer": {
      "command": "python",
      "args": ["main.py"],
      "cwd": "."
    }
  }
}
```

## Available Tools

- **project_structure**: Get project file structure
- **analyze_files**: Analyze specific files or patterns
- **analyze_code**: Comprehensive code analysis
- **configure_analyzer**: Update analyzer settings
- **get_stats**: Get project statistics
- **start_background_task**: Start async analysis
- **get_background_result**: Get async results

## Usage Examples

### Basic Analysis
```
Analyze this project for syntax errors and import issues
```

### File Structure
```
Show me the project structure, ignoring build files
```

### Background Analysis
```
Start a comprehensive code analysis in the background
```

## Configuration

The MCP server can be configured via:
- config/default_config.json
- Environment variables
- Runtime configuration through configure_analyzer tool

## Support

For issues and questions:
- GitHub: https://github.com/cheryiit/project-analyzer-mcp
- Check logs in: logs/project_errors.txt
"""
        
        guide_path = self.project_root / "docs" / "INTEGRATION_GUIDE.md"
        guide_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(guide_path, 'w') as f:
            f.write(guide_content)
        
        print(f"📚 Integration guide created: {guide_path}")
    
    def _get_cursor_config_path(self) -> Optional[Path]:
        """Cursor config dosya yolunu al"""
        system = platform.system()
        home = Path.home()
        
        if system == "Darwin":  # macOS
            return home / "Library" / "Application Support" / "Cursor" / "User" / "settings.json"
        elif system == "Windows":
            return home / "AppData" / "Roaming" / "Cursor" / "User" / "settings.json"
        elif system == "Linux":
            return home / ".config" / "Cursor" / "User" / "settings.json"
        
        return None
    
    def _get_vscode_settings_path(self) -> Optional[Path]:
        """VS Code settings dosya yolunu al"""
        system = platform.system()
        home = Path.home()
        
        if system == "Darwin":  # macOS
            return home / "Library" / "Application Support" / "Code" / "User" / "settings.json"
        elif system == "Windows":
            return home / "AppData" / "Roaming" / "Code" / "User" / "settings.json"
        elif system == "Linux":
            return home / ".config" / "Code" / "User" / "settings.json"
        
        return None
    
    def test_setup(self) -> bool:
        """MCP kurulumunu test et"""
        print("🧪 Testing MCP setup...")
        
        try:
            # Python server'ı test et
            cmd = [sys.executable, str(self.server_path), "--test"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ MCP server test successful!")
                return True
            else:
                print(f"❌ MCP server test failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ MCP test error: {e}")
            return False


def main():
    """Ana kurulum fonksiyonu"""
    setup = MCPSetup()
    
    print("🚀 Project Analyzer MCP Setup")
    print("=" * 40)
    
    # Komut satırı argümanlarını kontrol et
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg == "--claude-code":
            setup.setup_claude_code()
        elif arg == "--cursor":
            setup.setup_cursor()
        elif arg == "--vscode":
            setup.setup_vscode()
        elif arg == "--test":
            setup.test_setup()
        elif arg == "--all":
            print("Setting up for all supported editors...")
            setup.setup_claude_code()
            setup.setup_cursor()
            setup.setup_vscode()
        else:
            print(f"Unknown option: {arg}")
            print("Available options: --claude-code, --cursor, --vscode, --test, --all")
    else:
        # İnteraktif kurulum
        print("Select your editor:")
        print("1. Claude Code")
        print("2. Cursor")
        print("3. VS Code")
        print("4. All editors")
        print("5. Test setup")
        
        choice = input("Enter choice (1-5): ").strip()
        
        if choice == "1":
            setup.setup_claude_code()
        elif choice == "2":
            setup.setup_cursor()
        elif choice == "3":
            setup.setup_vscode()
        elif choice == "4":
            setup.setup_claude_code()
            setup.setup_cursor()
            setup.setup_vscode()
        elif choice == "5":
            setup.test_setup()
        else:
            print("Invalid choice")
    
    # Kılavuz oluştur
    setup.create_integration_guide()
    
    print("\n✨ Setup completed!")
    print("Check docs/INTEGRATION_GUIDE.md for detailed instructions.")


if __name__ == "__main__":
    main()