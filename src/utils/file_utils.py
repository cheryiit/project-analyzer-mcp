"""File handling utilities"""

from pathlib import Path
from typing import List, Optional, Callable
import logging

try:
    from gitignore_parser import parse_gitignore
except ImportError:
    # Fallback if gitignore_parser is not available
    def parse_gitignore(ignore_file_path: Path) -> Callable:
        return lambda path: False


class FileUtils:
    """Utility class for file operations"""
    
    @staticmethod
    def parse_gitignore(ignore_file_path: Path) -> Callable:
        """Parse gitignore file and return ignore function"""
        if not ignore_file_path.exists():
            return lambda path: False
            
        try:
            return parse_gitignore(ignore_file_path)
        except Exception as e:
            logging.getLogger(__name__).warning(f"Failed to parse ignore file {ignore_file_path}: {e}")
            return lambda path: False
    
    @staticmethod
    def get_files_by_patterns(project_path: Path, 
                            patterns: List[str], 
                            ignore_func: Callable,
                            config) -> List[Path]:
        """Get files matching specific patterns"""
        files = []
        
        for pattern in patterns:
            pattern_path = project_path / pattern
            
            if pattern_path.exists():
                if pattern_path.is_file():
                    if not ignore_func(str(pattern_path.relative_to(project_path))):
                        files.append(pattern_path)
                elif pattern_path.is_dir():
                    files.extend(FileUtils.get_files_in_directory(
                        pattern_path, project_path, ignore_func, config
                    ))
            else:
                # Try glob pattern
                try:
                    for match in project_path.glob(pattern):
                        if match.is_file() and not ignore_func(str(match.relative_to(project_path))):
                            files.append(match)
                except Exception:
                    pass
        
        return list(set(files))  # Remove duplicates
    
    @staticmethod
    def get_files_in_directory(directory: Path, 
                             base_path: Path, 
                             ignore_func: Callable,
                             config) -> List[Path]:
        """Recursively get all files in directory"""
        files = []
        
        try:
            for item in directory.rglob('*'):
                if item.is_file():
                    relative_path = item.relative_to(base_path)
                    
                    if ignore_func(str(relative_path)):
                        continue
                        
                    if any(pattern in str(relative_path) for pattern in config.exclude_patterns):
                        continue
                        
                    if config.should_include_file(item):
                        files.append(item)
        except PermissionError:
            pass
            
        return files
    
    @staticmethod
    def walk_directory_for_structure(current_path: Path, 
                                   base_path: Path, 
                                   ignore_func: Callable, 
                                   output: List[str], 
                                   level: int,
                                   config):
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
            if any(pattern in str(relative_path) for pattern in config.exclude_patterns):
                continue
                
            indent = '    ' * level
            
            if item.is_dir():
                output.append(f"{indent}{item.name}/\n")
                FileUtils.walk_directory_for_structure(item, base_path, ignore_func, output, level + 1, config)
            else:
                output.append(f"{indent}{item.name}\n")
    
    @staticmethod
    def ensure_directory(path: Path) -> None:
        """Ensure directory exists"""
        path.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def safe_write_file(file_path: Path, content: str, encoding: str = 'utf-8') -> bool:
        """Safely write content to file"""
        try:
            FileUtils.ensure_directory(file_path.parent)
            file_path.write_text(content, encoding=encoding)
            return True
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to write file {file_path}: {e}")
            return False
    
    @staticmethod
    def get_python_files(project_root: Path) -> List[Path]:
        """Get all Python files in project"""
        python_files = []
        for py_file in project_root.rglob("*.py"):
            # Skip common directories that shouldn't be analyzed
            if any(part in str(py_file) for part in ['__pycache__', '.pytest_cache', 'venv', '.venv']):
                continue
            python_files.append(py_file)
        return python_files