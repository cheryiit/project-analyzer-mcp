#!/usr/bin/env python3
"""
Enhanced Project Analyzer MCP Server
Based on architect_design Python scripts but with more flexibility and MCP integration
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Local imports
from gitignore_parser import parse_gitignore
from code_analyzer import CodeAnalyzer


class ProjectAnalyzerConfig:
    """Configuration class for the project analyzer"""
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        self.config = config_dict or {}
        
        # Default configuration
        self.project_name = self.config.get('project_name', 'Project')
        self.default_ignore_file = self.config.get('default_ignore_file', '.gitignore')
        self.max_file_size = self.config.get('max_file_size', 1024 * 1024)  # 1MB
        self.supported_extensions = self.config.get('supported_extensions', [
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
            '.go', '.rs', '.php', '.rb', '.swift', '.kt', '.scala', '.sh',
            '.md', '.txt', '.json', '.yaml', '.yml', '.xml', '.html', '.css'
        ])
        self.exclude_patterns = self.config.get('exclude_patterns', [
            '__pycache__', '.pytest_cache', 'node_modules', '.git',
            '.vscode', '.idea', '*.pyc', '*.pyo', '*.pyd', '.DS_Store'
        ])
        self.include_binary_info = self.config.get('include_binary_info', True)
        self.output_format = self.config.get('output_format', 'markdown')  # markdown, plain, json
        
    def should_include_file(self, file_path: Path) -> bool:
        """Check if file should be included based on configuration"""
        # Check file size
        try:
            if file_path.stat().st_size > self.max_file_size:
                return False
        except OSError:
            return False
            
        # Check extension
        if self.supported_extensions and file_path.suffix not in self.supported_extensions:
            return False
            
        return True


class ProjectAnalyzer:
    """Core project analysis functionality"""
    
    def __init__(self, config: ProjectAnalyzerConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def parse_gitignore(self, ignore_file_path: Path) -> callable:
        """Parse gitignore file and return ignore function"""
        if not ignore_file_path.exists():
            return lambda path: False
            
        try:
            return parse_gitignore(ignore_file_path)
        except Exception as e:
            self.logger.warning(f"Failed to parse ignore file {ignore_file_path}: {e}")
            return lambda path: False
    
    def generate_project_structure(self, 
                                 project_path: Path, 
                                 ignore_file: Optional[str] = None) -> str:
        """Generate hierarchical project structure"""
        ignore_file = ignore_file or self.config.default_ignore_file
        ignore_file_path = project_path / ignore_file
        ignore_func = self.parse_gitignore(ignore_file_path)
        
        structure_lines = []
        self._walk_directory(project_path, project_path, ignore_func, structure_lines, 0)
        
        if self.config.output_format == 'markdown':
            return f"```\n{''.join(structure_lines)}```"
        else:
            return ''.join(structure_lines)
    
    def _walk_directory(self, 
                       current_path: Path, 
                       base_path: Path, 
                       ignore_func: callable, 
                       output: List[str], 
                       level: int):
        """Recursively walk directory and build structure"""
        try:
            items = sorted(current_path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
        except PermissionError:
            return
            
        for item in items:
            relative_path = item.relative_to(base_path)
            
            # Check if should be ignored
            if ignore_func(str(relative_path)):
                continue
                
            # Check against exclude patterns
            if any(pattern in str(relative_path) for pattern in self.config.exclude_patterns):
                continue
                
            indent = '    ' * level
            
            if item.is_dir():
                output.append(f"{indent}{item.name}/\n")
                self._walk_directory(item, base_path, ignore_func, output, level + 1)
            else:
                output.append(f"{indent}{item.name}\n")
    
    def analyze_files(self, 
                     project_path: Path, 
                     target_patterns: Optional[List[str]] = None,
                     ignore_file: Optional[str] = None) -> str:
        """Analyze file contents based on patterns or full project"""
        ignore_file = ignore_file or self.config.default_ignore_file
        ignore_file_path = project_path / ignore_file
        ignore_func = self.parse_gitignore(ignore_file_path)
        
        if target_patterns:
            files = self._get_files_by_patterns(project_path, target_patterns, ignore_func)
        else:
            files = self._get_all_files(project_path, ignore_func)
        
        return self._format_file_contents(files, project_path)
    
    def _get_files_by_patterns(self, 
                              project_path: Path, 
                              patterns: List[str], 
                              ignore_func: callable) -> List[Path]:
        """Get files matching specific patterns"""
        files = []
        
        for pattern in patterns:
            pattern_path = project_path / pattern
            
            if pattern_path.exists():
                if pattern_path.is_file():
                    if not ignore_func(str(pattern_path.relative_to(project_path))):
                        files.append(pattern_path)
                elif pattern_path.is_dir():
                    files.extend(self._get_files_in_directory(pattern_path, project_path, ignore_func))
            else:
                # Try glob pattern
                try:
                    for match in project_path.glob(pattern):
                        if match.is_file() and not ignore_func(str(match.relative_to(project_path))):
                            files.append(match)
                except Exception:
                    pass
        
        return list(set(files))  # Remove duplicates
    
    def _get_all_files(self, project_path: Path, ignore_func: callable) -> List[Path]:
        """Get all files in project"""
        return self._get_files_in_directory(project_path, project_path, ignore_func)
    
    def _get_files_in_directory(self, 
                               directory: Path, 
                               base_path: Path, 
                               ignore_func: callable) -> List[Path]:
        """Recursively get all files in directory"""
        files = []
        
        try:
            for item in directory.rglob('*'):
                if item.is_file():
                    relative_path = item.relative_to(base_path)
                    
                    if ignore_func(str(relative_path)):
                        continue
                        
                    if any(pattern in str(relative_path) for pattern in self.config.exclude_patterns):
                        continue
                        
                    if self.config.should_include_file(item):
                        files.append(item)
        except PermissionError:
            pass
            
        return files
    
    def _format_file_contents(self, files: List[Path], base_path: Path) -> str:
        """Format file contents for output"""
        if self.config.output_format == 'json':
            return self._format_as_json(files, base_path)
        elif self.config.output_format == 'markdown':
            return self._format_as_markdown(files, base_path)
        else:
            return self._format_as_plain(files, base_path)
    
    def _format_as_json(self, files: List[Path], base_path: Path) -> str:
        """Format files as JSON"""
        result = {}
        
        for file_path in files:
            relative_path = str(file_path.relative_to(base_path))
            try:
                content = file_path.read_text(encoding='utf-8')
                result[relative_path] = {
                    'content': content,
                    'size': file_path.stat().st_size,
                    'type': 'text'
                }
            except UnicodeDecodeError:
                if self.config.include_binary_info:
                    result[relative_path] = {
                        'content': None,
                        'size': file_path.stat().st_size,
                        'type': 'binary'
                    }
            except Exception as e:
                result[relative_path] = {
                    'content': None,
                    'error': str(e),
                    'type': 'error'
                }
        
        return json.dumps(result, indent=2, ensure_ascii=False)
    
    def _format_as_markdown(self, files: List[Path], base_path: Path) -> str:
        """Format files as Markdown"""
        output = ["# File Contents\n\n"]
        
        for file_path in files:
            relative_path = str(file_path.relative_to(base_path))
            output.append(f"## {relative_path}\n\n")
            
            try:
                content = file_path.read_text(encoding='utf-8')
                # Detect language for syntax highlighting
                ext = file_path.suffix.lstrip('.')
                lang_map = {
                    'py': 'python', 'js': 'javascript', 'ts': 'typescript',
                    'jsx': 'jsx', 'tsx': 'tsx', 'java': 'java', 'cpp': 'cpp',
                    'c': 'c', 'h': 'c', 'go': 'go', 'rs': 'rust', 'php': 'php',
                    'rb': 'ruby', 'swift': 'swift', 'kt': 'kotlin', 'scala': 'scala',
                    'sh': 'bash', 'json': 'json', 'yaml': 'yaml', 'yml': 'yaml',
                    'xml': 'xml', 'html': 'html', 'css': 'css'
                }
                lang = lang_map.get(ext, ext)
                
                output.append(f"```{lang}\n{content}\n```\n\n")
            except UnicodeDecodeError:
                if self.config.include_binary_info:
                    size = file_path.stat().st_size
                    output.append(f"*Binary file ({size} bytes)*\n\n")
            except Exception as e:
                output.append(f"*Error reading file: {str(e)}*\n\n")
            
            output.append("---\n\n")
        
        return ''.join(output)
    
    def _format_as_plain(self, files: List[Path], base_path: Path) -> str:
        """Format files as plain text"""
        output = []
        
        for file_path in files:
            relative_path = str(file_path.relative_to(base_path))
            output.append(f"{relative_path}:\n\n")
            
            try:
                content = file_path.read_text(encoding='utf-8')
                output.append(content)
            except UnicodeDecodeError:
                if self.config.include_binary_info:
                    size = file_path.stat().st_size
                    output.append(f"Binary file ({size} bytes)\n")
            except Exception as e:
                output.append(f"Error reading file: {str(e)}\n")
            
            output.append("\n\n" + "="*50 + "\n\n")
        
        return ''.join(output)


class ProjectAnalyzerMCPServer:
    """Project Analyzer MCP Server - Direct replacement for original project-analyzer"""
    
    def __init__(self):
        self.config = ProjectAnalyzerConfig()
        self.analyzer = ProjectAnalyzer(self.config)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def handle_project_structure(self, args: Dict[str, Any]) -> str:
        """Handle project structure generation"""
        project_path = Path(args.get('project_path', '.'))
        ignore_file = args.get('ignore_file')
        # Use config default if not specified in args
        output_format = args.get('output_format', self.config.output_format)
        
        # Update config for this request
        old_format = self.config.output_format
        self.config.output_format = output_format
        
        try:
            structure = self.analyzer.generate_project_structure(project_path, ignore_file)
            return structure
        except Exception as e:
            self.logger.error(f"Error generating project structure: {e}")
            return f"Error: {str(e)}"
        finally:
            self.config.output_format = old_format
    
    def handle_analyze_files(self, args: Dict[str, Any]) -> str:
        """Handle file analysis"""
        project_path = Path(args.get('project_path', '.'))
        target_patterns = args.get('target_patterns')
        ignore_file = args.get('ignore_file')
        # Use config default if not specified in args
        output_format = args.get('output_format', self.config.output_format)
        max_file_size = args.get('max_file_size', self.config.max_file_size)
        
        # Update config for this request
        old_format = self.config.output_format
        old_max_size = self.config.max_file_size
        self.config.output_format = output_format
        self.config.max_file_size = max_file_size
        
        try:
            analysis = self.analyzer.analyze_files(project_path, target_patterns, ignore_file)
            return analysis
        except Exception as e:
            self.logger.error(f"Error analyzing files: {e}")
            return f"Error: {str(e)}"
        finally:
            self.config.output_format = old_format
            self.config.max_file_size = old_max_size
    
    def handle_configure_analyzer(self, args: Dict[str, Any]) -> str:
        """Handle analyzer configuration"""
        config_dict = args.get('config', {})
        
        try:
            # Update configuration
            self.config = ProjectAnalyzerConfig(config_dict)
            self.analyzer = ProjectAnalyzer(self.config)
            
            return f"Configuration updated successfully. New settings: {json.dumps(config_dict, indent=2)}"
        except Exception as e:
            self.logger.error(f"Error configuring analyzer: {e}")
            return f"Error: {str(e)}"
    
    def _handle_analyze_code(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle code analysis using CodeAnalyzer"""
        project_path = Path(args.get('project_path', '.'))
        analysis_type = args.get('analysis_type', 'comprehensive')
        output_format = args.get('output_format', 'markdown')
        save_results = args.get('save_results', False)
        
        try:
            # Create code analyzer
            code_analyzer = CodeAnalyzer(project_path)
            
            # Run analysis
            if analysis_type == 'comprehensive':
                results = code_analyzer.analyze_all()
            else:
                results = code_analyzer.analyze_specific(analysis_type)
            
            # Format results
            formatted_output = code_analyzer.format_results(results, output_format)
            
            # Save results if requested
            if save_results:
                output_file = project_path / "storage" / "logs" / "project_errors.txt"
                code_analyzer.save_results(results, output_file)
            
            # Return both formatted text and structured data
            return {
                "content": [{"type": "text", "text": formatted_output}],
                "isError": len(results.get("errors", [])) > 0,
                "_meta": {
                    "analysis_type": analysis_type,
                    "errors_count": len(results.get("errors", [])),
                    "warnings_count": len(results.get("warnings", [])),
                    "project_path": str(project_path),
                    "output_format": output_format
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error during code analysis: {e}")
            return {
                "content": [{"type": "text", "text": f"Error during code analysis: {str(e)}"}],
                "isError": True,
                "_meta": {
                    "analysis_type": analysis_type,
                    "project_path": str(project_path),
                    "error": str(e)
                }
            }
    
    def run_standalone(self):
        """Run as standalone script for testing"""
        # Test the analyzer
        try:
            # Test project structure
            print("=== Testing Project Structure ===")
            structure = self.handle_project_structure({'project_path': '.'})
            print(structure[:500] + "..." if len(structure) > 500 else structure)
            
            # Test file analysis on specific patterns
            print("\n=== Testing File Analysis ===")
            analysis = self.handle_analyze_files({
                'project_path': '.',
                'target_patterns': ['*.py'],
                'output_format': 'plain'
            })
            print(analysis[:500] + "..." if len(analysis) > 500 else analysis)
            
        except Exception as e:
            print(f"Error during testing: {e}")
    
    def process_mcp_request(self, request_json: str) -> str:
        """Process MCP request (simplified for current use)"""
        try:
            request = json.loads(request_json)
            tool_name = request.get('tool')
            arguments = request.get('arguments', {})
            
            if tool_name == 'project_structure':
                return self.handle_project_structure(arguments)
            elif tool_name == 'analyze_files':
                return self.handle_analyze_files(arguments)
            elif tool_name == 'analyze_code':
                return self._handle_analyze_code(arguments)
            elif tool_name == 'configure_analyzer':
                return self.handle_configure_analyzer(arguments)
            else:
                return f"Unknown tool: {tool_name}"
                
        except Exception as e:
            return f"Error processing request: {str(e)}"


def main():
    """Main entry point"""
    server = ProjectAnalyzerMCPServer()
    
    # Check if running in test mode
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        server.run_standalone()
    else:
        # For now, just run a simple test
        print("Project Analyzer Python MCP Server")
        print("Available tools: project_structure, analyze_files, analyze_code, configure_analyzer")
        
        # Test the new code analysis tool
        print("\n=== Testing Code Analysis ===")
        try:
            code_analysis = server._handle_analyze_code({
                'project_path': '/Users/yigitkiraz/TrBotMaster',
                'analysis_type': 'comprehensive',
                'output_format': 'markdown',
                'save_results': True
            })
            print("Code analysis completed successfully:")
            print(f"Errors: {code_analysis['_meta']['errors_count']}")
            print(f"Warnings: {code_analysis['_meta']['warnings_count']}")
            print(code_analysis['content'][0]['text'][:300] + "...")
        except Exception as e:
            print(f"Code analysis test failed: {e}")
        server.run_standalone()


if __name__ == "__main__":
    main()