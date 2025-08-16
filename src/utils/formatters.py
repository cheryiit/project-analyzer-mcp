"""Output formatting utilities"""

import json
from pathlib import Path
from typing import List, Dict, Any


class Formatter:
    """Handles different output formats for analysis results"""
    
    @staticmethod
    def format_file_contents(files: List[Path], base_path: Path, output_format: str = 'markdown', include_binary_info: bool = True) -> str:
        """Format file contents for output"""
        if output_format == 'json':
            return Formatter._format_as_json(files, base_path, include_binary_info)
        elif output_format == 'markdown':
            return Formatter._format_as_markdown(files, base_path, include_binary_info)
        else:
            return Formatter._format_as_plain(files, base_path, include_binary_info)
    
    @staticmethod
    def _format_as_json(files: List[Path], base_path: Path, include_binary_info: bool) -> str:
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
                if include_binary_info:
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
    
    @staticmethod
    def _format_as_markdown(files: List[Path], base_path: Path, include_binary_info: bool) -> str:
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
                if include_binary_info:
                    size = file_path.stat().st_size
                    output.append(f"*Binary file ({size} bytes)*\n\n")
            except Exception as e:
                output.append(f"*Error reading file: {str(e)}*\n\n")
            
            output.append("---\n\n")
        
        return ''.join(output)
    
    @staticmethod
    def _format_as_plain(files: List[Path], base_path: Path, include_binary_info: bool) -> str:
        """Format files as plain text"""
        output = []
        
        for file_path in files:
            relative_path = str(file_path.relative_to(base_path))
            output.append(f"{relative_path}:\n\n")
            
            try:
                content = file_path.read_text(encoding='utf-8')
                output.append(content)
            except UnicodeDecodeError:
                if include_binary_info:
                    size = file_path.stat().st_size
                    output.append(f"Binary file ({size} bytes)\n")
            except Exception as e:
                output.append(f"Error reading file: {str(e)}\n")
            
            output.append("\n\n" + "="*50 + "\n\n")
        
        return ''.join(output)
    
    @staticmethod
    def format_analysis_results(results: Dict[str, Any], output_format: str = 'markdown') -> str:
        """Format analysis results"""
        if output_format == 'json':
            return json.dumps(results, indent=2, ensure_ascii=False)
        elif output_format == 'markdown':
            return Formatter._format_analysis_markdown(results)
        else:
            return Formatter._format_analysis_plain(results)
    
    @staticmethod
    def _format_analysis_markdown(results: Dict[str, Any]) -> str:
        """Format analysis results as markdown"""
        output = ["# Code Analysis Results\n\n"]
        
        if "errors" in results and results["errors"]:
            output.append("## Errors\n\n")
            for error in results["errors"]:
                output.append(f"- {error}\n")
            output.append("\n")
        
        if "warnings" in results and results["warnings"]:
            output.append("## Warnings\n\n")
            for warning in results["warnings"]:
                output.append(f"- {warning}\n")
            output.append("\n")
        
        if "summary" in results:
            output.append("## Summary\n\n")
            output.append(f"{results['summary']}\n\n")
        
        return ''.join(output)
    
    @staticmethod
    def _format_analysis_plain(results: Dict[str, Any]) -> str:
        """Format analysis results as plain text"""
        output = ["Code Analysis Results\n", "="*50, "\n\n"]
        
        if "errors" in results and results["errors"]:
            output.append("ERRORS:\n")
            for error in results["errors"]:
                output.append(f"  - {error}\n")
            output.append("\n")
        
        if "warnings" in results and results["warnings"]:
            output.append("WARNINGS:\n")
            for warning in results["warnings"]:
                output.append(f"  - {warning}\n")
            output.append("\n")
        
        if "summary" in results:
            output.append("SUMMARY:\n")
            output.append(f"{results['summary']}\n\n")
        
        return ''.join(output)