# Project Analyzer Python MCP Server - Usage Examples

## 🎯 Real-World Usage Examples

### 1. Basic Project Overview

Get a quick overview of your project structure:

```python
from project_analyzer_server import ProjectAnalyzerMCPServer

server = ProjectAnalyzerMCPServer()

# Get project structure in markdown format
structure = server.handle_project_structure({
    'project_path': '.',
    'output_format': 'markdown'
})
print(structure)
```

### 2. Code Review Preparation

Analyze specific files for code review:

```python
# Analyze only Python files that changed recently
analysis = server.handle_analyze_files({
    'project_path': '/path/to/project',
    'target_patterns': ['src/**/*.py', 'tests/**/*.py'],
    'output_format': 'markdown',
    'max_file_size': 100000  # 100KB limit
})
```

### 3. Documentation Generation

Generate documentation from code comments:

```python
# Configure for documentation
server.handle_configure_analyzer({
    'config': {
        'output_format': 'markdown',
        'supported_extensions': ['.py', '.js', '.md', '.rst'],
        'max_file_size': 500000,  # 500KB for docs
        'include_binary_info': False
    }
})

# Analyze documentation files
docs = server.handle_analyze_files({
    'project_path': '/path/to/project',
    'target_patterns': ['docs/**/*', '*.md', 'README*']
})
```

### 4. Dependency Analysis

Analyze configuration and dependency files:

```python
# Focus on config and dependency files
config_analysis = server.handle_analyze_files({
    'project_path': '/path/to/project',
    'target_patterns': [
        'package.json', 'requirements.txt', 'Pipfile',
        'setup.py', 'pyproject.toml', 'Dockerfile',
        'config/**/*', 'settings/**/*'
    ],
    'output_format': 'json'
})

import json
configs = json.loads(config_analysis)
for file_path, data in configs.items():
    print(f"Config file: {file_path} ({data['size']} bytes)")
```

### 5. Performance Analysis

Monitor large codebase analysis performance:

```python
import time

# Configure for large projects
server.handle_configure_analyzer({
    'config': {
        'max_file_size': 50000,  # 50KB limit
        'exclude_patterns': [
            '__pycache__', '.git', 'node_modules', 
            '*.pyc', '*.log', 'dist/', 'build/'
        ]
    }
})

start_time = time.time()
analysis = server.handle_analyze_files({
    'project_path': '/large/project',
    'target_patterns': ['**/*.py'],
    'output_format': 'json'
})
duration = time.time() - start_time

print(f"Analyzed project in {duration:.2f} seconds")
```

### 6. CI/CD Integration

Use in continuous integration:

```python
def analyze_changed_files(changed_files_list):
    """Analyze only files that changed in current PR/commit"""
    
    server = ProjectAnalyzerMCPServer()
    
    # Configure for CI environment
    server.handle_configure_analyzer({
        'config': {
            'max_file_size': 200000,  # 200KB
            'output_format': 'markdown',
            'include_binary_info': True
        }
    })
    
    analysis = server.handle_analyze_files({
        'project_path': '.',
        'target_patterns': changed_files_list,
        'output_format': 'markdown'
    })
    
    # Save analysis for CI report
    with open('code_analysis_report.md', 'w') as f:
        f.write(f"# Code Analysis Report\n\n")
        f.write(f"## Changed Files Analysis\n\n")
        f.write(analysis)
    
    return analysis

# Example usage in CI
changed_files = ['src/main.py', 'tests/test_main.py', 'config/settings.py']
analyze_changed_files(changed_files)
```

### 7. Interactive Project Explorer

Build an interactive project explorer:

```python
class ProjectExplorer:
    def __init__(self, project_path):
        self.server = ProjectAnalyzerMCPServer()
        self.project_path = project_path
        
    def explore_directory(self, directory_pattern):
        """Explore specific directory"""
        return self.server.handle_analyze_files({
            'project_path': self.project_path,
            'target_patterns': [f"{directory_pattern}/**/*"],
            'output_format': 'json'
        })
    
    def search_files(self, extension):
        """Search files by extension"""
        return self.server.handle_analyze_files({
            'project_path': self.project_path,
            'target_patterns': [f"**/*{extension}"],
            'output_format': 'json'
        })
    
    def get_structure(self):
        """Get full project structure"""
        return self.server.handle_project_structure({
            'project_path': self.project_path,
            'output_format': 'plain'
        })

# Usage
explorer = ProjectExplorer('/path/to/project')
python_files = explorer.search_files('.py')
tests_dir = explorer.explore_directory('tests')
structure = explorer.get_structure()
```

### 8. Code Quality Metrics

Extract code quality metrics:

```python
def analyze_code_quality(project_path):
    """Analyze code quality metrics"""
    server = ProjectAnalyzerMCPServer()
    
    # Get all Python files
    analysis = server.handle_analyze_files({
        'project_path': project_path,
        'target_patterns': ['**/*.py'],
        'output_format': 'json',
        'max_file_size': 1000000  # 1MB
    })
    
    import json
    files_data = json.loads(analysis)
    
    metrics = {
        'total_files': len(files_data),
        'total_size': 0,
        'large_files': [],
        'small_files': [],
        'binary_files': 0
    }
    
    for file_path, data in files_data.items():
        if data['type'] == 'binary':
            metrics['binary_files'] += 1
            continue
            
        size = data.get('size', 0)
        metrics['total_size'] += size
        
        if size > 10000:  # 10KB
            metrics['large_files'].append((file_path, size))
        elif size < 100:  # 100 bytes
            metrics['small_files'].append((file_path, size))
    
    return metrics

# Usage
metrics = analyze_code_quality('/path/to/project')
print(f"Project has {metrics['total_files']} Python files")
print(f"Total size: {metrics['total_size']:,} bytes")
print(f"Large files (>10KB): {len(metrics['large_files'])}")
```

### 9. MCP-Style Request Processing

Process requests in MCP format:

```python
import json

def process_mcp_requests(requests):
    """Process multiple MCP-style requests"""
    server = ProjectAnalyzerMCPServer()
    results = []
    
    for request in requests:
        request_json = json.dumps(request)
        result = server.process_mcp_request(request_json)
        results.append({
            'request': request,
            'result': result,
            'success': not result.startswith('Error')
        })
    
    return results

# Example requests
requests = [
    {
        "tool": "project_structure",
        "arguments": {
            "project_path": ".",
            "output_format": "markdown"
        }
    },
    {
        "tool": "analyze_files",
        "arguments": {
            "project_path": ".",
            "target_patterns": ["*.py"],
            "output_format": "json"
        }
    },
    {
        "tool": "configure_analyzer",
        "arguments": {
            "config": {
                "max_file_size": 100000,
                "output_format": "plain"
            }
        }
    }
]

results = process_mcp_requests(requests)
for i, result in enumerate(results):
    print(f"Request {i+1}: {'SUCCESS' if result['success'] else 'FAILED'}")
```

### 10. Advanced Filtering

Complex file filtering and analysis:

```python
def advanced_project_analysis(project_path):
    """Advanced analysis with custom filtering"""
    server = ProjectAnalyzerMCPServer()
    
    # Configure for advanced analysis
    server.handle_configure_analyzer({
        'config': {
            'max_file_size': 1000000,  # 1MB
            'supported_extensions': [
                '.py', '.js', '.ts', '.jsx', '.tsx',
                '.java', '.cpp', '.c', '.h', '.go',
                '.rs', '.php', '.rb', '.swift'
            ],
            'exclude_patterns': [
                '__pycache__', '.pytest_cache', 'node_modules',
                '.git', '.svn', 'dist', 'build', '*.pyc',
                '*.pyo', '*.pyd', '.DS_Store', 'Thumbs.db'
            ],
            'output_format': 'json'
        }
    })
    
    # Analyze different categories
    analyses = {}
    
    # Core application files
    analyses['core'] = server.handle_analyze_files({
        'project_path': project_path,
        'target_patterns': ['src/**/*', 'lib/**/*', 'core/**/*']
    })
    
    # Test files
    analyses['tests'] = server.handle_analyze_files({
        'project_path': project_path,
        'target_patterns': ['test/**/*', 'tests/**/*', '**/test_*.py', '**/*_test.py']
    })
    
    # Configuration files
    analyses['config'] = server.handle_analyze_files({
        'project_path': project_path,
        'target_patterns': [
            '*.json', '*.yaml', '*.yml', '*.toml', '*.ini',
            'config/**/*', 'settings/**/*', 'conf/**/*'
        ]
    })
    
    # Documentation
    analyses['docs'] = server.handle_analyze_files({
        'project_path': project_path,
        'target_patterns': [
            '*.md', '*.rst', '*.txt', 'docs/**/*',
            'README*', 'CHANGELOG*', 'LICENSE*'
        ]
    })
    
    return analyses

# Usage
project_analysis = advanced_project_analysis('/path/to/project')
for category, analysis in project_analysis.items():
    try:
        data = json.loads(analysis) if analysis.startswith('{') else {}
        print(f"{category.upper()}: {len(data)} files analyzed")
    except:
        print(f"{category.upper()}: {len(analysis)} characters")
```

## 🔧 Configuration Tips

### Optimal Settings for Different Use Cases

**Small Projects (<100 files):**
```python
{
    'max_file_size': 1000000,  # 1MB
    'output_format': 'markdown',
    'include_binary_info': True
}
```

**Large Projects (>1000 files):**
```python
{
    'max_file_size': 50000,    # 50KB
    'output_format': 'json',
    'include_binary_info': False,
    'exclude_patterns': ['dist/', 'build/', '__pycache__/', 'node_modules/']
}
```

**Documentation Focus:**
```python
{
    'supported_extensions': ['.md', '.rst', '.txt'],
    'max_file_size': 500000,   # 500KB
    'output_format': 'markdown'
}
```

**Code Review:**
```python
{
    'supported_extensions': ['.py', '.js', '.ts', '.java', '.cpp'],
    'max_file_size': 100000,   # 100KB
    'output_format': 'markdown',
    'exclude_patterns': ['test/', 'tests/', '*_test.py']
}
```