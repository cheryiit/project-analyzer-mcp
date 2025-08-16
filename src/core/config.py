"""Configuration management for the Project Analyzer"""

from pathlib import Path
from typing import Dict, Any, List, Optional


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
        
        # Background operation settings
        self.enable_background_mode = self.config.get('enable_background_mode', True)
        self.max_concurrent_analyses = self.config.get('max_concurrent_analyses', 3)
        self.cache_results = self.config.get('cache_results', True)
        self.auto_cleanup = self.config.get('auto_cleanup', True)
        
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
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update configuration with new values"""
        self.config.update(new_config)
        self.__init__(self.config)  # Reinitialize with updated config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'project_name': self.project_name,
            'default_ignore_file': self.default_ignore_file,
            'max_file_size': self.max_file_size,
            'supported_extensions': self.supported_extensions,
            'exclude_patterns': self.exclude_patterns,
            'include_binary_info': self.include_binary_info,
            'output_format': self.output_format,
            'enable_background_mode': self.enable_background_mode,
            'max_concurrent_analyses': self.max_concurrent_analyses,
            'cache_results': self.cache_results,
            'auto_cleanup': self.auto_cleanup
        }