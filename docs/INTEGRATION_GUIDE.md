
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
