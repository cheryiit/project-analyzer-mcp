# 🔍 Project Analyzer MCP

Enhanced Python-based MCP server for comprehensive project analysis with async support, designed for **Claude Code**, **Cursor**, and **VS Code**.

## 🚀 Quick Install

### Claude Code (Recommended)
```bash
# One-liner install from GitHub
curl -sSL https://raw.githubusercontent.com/cheryiit/project-analyzer-mcp/master/installer.py | python
```

**Or manual config:**
```bash
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Add to your config:
```json
{
  "mcpServers": {
    "project-analyzer": {
      "command": "python",
      "args": ["-c", "exec(__import__('urllib.request').urlopen('https://raw.githubusercontent.com/cheryiit/project-analyzer-mcp/master/main.py').read())"],
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

### Alternative Setup Methods

**Direct GitHub download:**
```bash
# Download and setup
git clone https://github.com/cheryiit/project-analyzer-mcp.git
cd project-analyzer-mcp
python installer.py
```

**NPX-style (for consistency with other MCP servers):**
```json
{
  "mcpServers": {
    "project-analyzer": {
      "command": "python",
      "args": ["-c", "import os,subprocess,tempfile,urllib.request; d=tempfile.mkdtemp(); urllib.request.urlretrieve('https://raw.githubusercontent.com/cheryiit/project-analyzer-mcp/master/main.py', os.path.join(d,'main.py')); subprocess.run(['python', os.path.join(d,'main.py')])"]
    }
  }
}
```

## 🛠️ Available Tools

- **`project_structure`** - Get hierarchical project structure
- **`analyze_files`** - Analyze specific files or patterns
- **`analyze_code`** - Comprehensive code analysis (syntax, imports, parameters)
- **`configure_analyzer`** - Runtime configuration updates
- **`get_stats`** - Project statistics and file info
- **`start_background_task`** - Start async analysis tasks
- **`get_background_result`** - Get async task results

## 💬 Usage in Claude Code

### Basic Analysis
```
Analyze this project for syntax errors and import issues
```

### File Structure
```
Show me the project structure, ignoring build and cache files
```

### Background Analysis
```
Start a comprehensive code analysis in the background and show me when it's done
```

### Specific File Analysis
```
Analyze all Python files in the src/ directory for parameter mismatches
```

## ⚡ Features

- **🔍 Deep Code Analysis** - Syntax errors, import issues, parameter mismatches
- **🏗️ Project Structure** - Hierarchical view with gitignore support
- **⚡ Async Processing** - Background analysis for large projects
- **📊 Comprehensive Reports** - Terminal output + file logging
- **🎯 Multi-Editor Support** - Claude Code, Cursor, VS Code
- **🔧 Flexible Config** - JSON config + runtime updates

## 🏗️ Architecture

```
📦 project-analyzer-mcp/
├── 🐍 main.py              # Entry point
├── 📁 src/
│   ├── core/               # Server & orchestration
│   ├── analyzers/          # Code & structure analysis  
│   └── utils/              # File handling & formatting
├── 📁 config/              # Configuration files
└── 🔧 installer.py         # One-command installer
```

## 🔧 Configuration

Default config supports most use cases. For custom settings:

```json
{
  "project_name": "MyProject",
  "max_file_size": 1048576,
  "output_format": "markdown",
  "enable_background_mode": true,
  "max_concurrent_analyses": 3,
  "supported_extensions": [".py", ".js", ".ts", ".jsx", ".tsx"]
}
```

## 🚀 Advanced Usage

### Manual Installation
```bash
git clone https://github.com/cheryiit/project-analyzer-mcp.git
cd project-analyzer-mcp
pip install -r requirements.txt
python main.py --test
```

### Claude Code Manual Config
```json
{
  "mcpServers": {
    "project-analyzer": {
      "command": "python",
      "args": ["/path/to/project-analyzer-mcp/main.py"],
      "env": {
        "PYTHONPATH": "/path/to/project-analyzer-mcp"
      }
    }
  }
}
```

### Cursor Config
Add to Cursor settings:
```json
{
  "mcpServers": {
    "project-analyzer": {
      "command": "python", 
      "args": ["/path/to/main.py"]
    }
  }
}
```

## 🧪 Testing

```bash
# Test basic functionality
python main.py --test

# Test async features  
python main.py --async-test

# Test MCP integration
claude mcp get project-analyzer
```

## 🔍 Troubleshooting

### Server Won't Connect
```bash
# Test directly
echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05"},"id":1}' | python main.py

# Check Claude logs
tail -f ~/.claude/logs/mcp-server-project-analyzer.log
```

### Permission Issues
```bash
# Try project scope instead of user
claude mcp add project-analyzer --scope project

# Or reinstall with different permissions
claude mcp remove project-analyzer
curl -sSL https://raw.githubusercontent.com/cheryiit/project-analyzer-mcp/master/installer.py | python
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🌟 Why This MCP?

- **🚀 Production Ready** - Used in real development workflows
- **⚡ Fast & Async** - Background processing for large codebases
- **🎯 Multi-Editor** - Works with Claude Code, Cursor, VS Code
- **🔍 Comprehensive** - Beyond basic file reading, real code analysis
- **🛠️ Flexible** - Configurable for any project type
- **📚 Well Documented** - Clear examples and troubleshooting

---

**Made with ❤️ for the Claude Code community**

*Transform your development workflow with intelligent project analysis directly in Claude Code!*