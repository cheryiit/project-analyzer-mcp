# Project Analyzer Python MCP Server

Enhanced Python-based MCP server for comprehensive project analysis, inspired by the architect_design scripts but with more flexibility and MCP integration.

## Features

- **Hierarchical Project Structure**: Generate tree-like project structures respecting gitignore rules
- **File Content Analysis**: Analyze and extract file contents with various formatting options
- **Flexible Configuration**: Configurable file size limits, supported extensions, and output formats
- **Multiple Output Formats**: Plain text, Markdown, and JSON output
- **Pattern-based Analysis**: Analyze specific files or directories using glob patterns
- **Binary File Handling**: Smart handling of binary files with size information
- **Gitignore Support**: Full gitignore parsing and filtering

## Configuration Options

The server supports various configuration options:

```json
{
  "project_name": "MyProject",
  "default_ignore_file": ".gitignore",
  "max_file_size": 1048576,
  "supported_extensions": [".py", ".js", ".ts", ".md"],
  "exclude_patterns": ["__pycache__", "node_modules", ".git"],
  "include_binary_info": true,
  "output_format": "markdown"
}
```

## Available Tools

### 1. project_structure

Generate hierarchical project structure.

**Parameters:**
- `project_path` (string): Path to project root directory (default: ".")
- `ignore_file` (string): Custom ignore file name (optional)
- `output_format` (string): "plain" or "markdown" (default: "markdown")

### 2. analyze_files

Analyze project files with content extraction.

**Parameters:**
- `project_path` (string): Path to project root directory (default: ".")
- `target_patterns` (array): Specific file patterns to analyze (optional)
- `ignore_file` (string): Custom ignore file name (optional)
- `output_format` (string): "plain", "markdown", or "json" (default: "markdown")
- `max_file_size` (number): Maximum file size to analyze in bytes (default: 1MB)

### 3. configure_analyzer

Configure analyzer settings dynamically.

**Parameters:**
- `config` (object): Configuration object with analyzer settings

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python project_analyzer_server.py
```

## MCP Integration

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "project-analyzer-python": {
      "command": "python",
      "args": ["/path/to/project_analyzer_server.py"],
      "cwd": "/path/to/project-analyzer-python"
    }
  }
}
```

## Usage Examples

### Get Project Structure
```json
{
  "tool": "project_structure",
  "arguments": {
    "project_path": "/path/to/project",
    "output_format": "markdown"
  }
}
```

### Analyze Specific Files
```json
{
  "tool": "analyze_files",
  "arguments": {
    "project_path": "/path/to/project",
    "target_patterns": ["*.py", "config/*.json"],
    "output_format": "json"
  }
}
```

### Configure Analyzer
```json
{
  "tool": "configure_analyzer",
  "arguments": {
    "config": {
      "max_file_size": 2097152,
      "output_format": "markdown",
      "supported_extensions": [".py", ".js", ".ts", ".md", ".json"]
    }
  }
}
```

## Differences from Original architect_design

1. **MCP Integration**: Full MCP server implementation with proper tool definitions
2. **Dynamic Configuration**: Runtime configuration changes without restart
3. **Multiple Output Formats**: Support for plain, markdown, and JSON output
4. **Pattern Matching**: Glob pattern support for flexible file selection
5. **Better Error Handling**: Comprehensive error handling and logging
6. **Binary File Support**: Smart binary file detection and handling
7. **Size Limits**: Configurable file size limits
8. **Extension Filtering**: Configurable supported file extensions