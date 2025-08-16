"""Structure analysis for project organization"""

from pathlib import Path
from typing import List, Optional
import logging

from ..utils.file_utils import FileUtils
from ..utils.formatters import Formatter


class StructureAnalyzer:
    """Analyzes project structure and organization"""
    
    def __init__(self, project_root: Path, config):
        self.project_root = project_root
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def generate_project_structure(self, ignore_file: Optional[str] = None) -> str:
        """Generate hierarchical project structure"""
        ignore_file = ignore_file or self.config.default_ignore_file
        ignore_file_path = self.project_root / ignore_file
        ignore_func = FileUtils.parse_gitignore(ignore_file_path)
        
        structure_lines = []
        FileUtils.walk_directory_for_structure(
            self.project_root, self.project_root, ignore_func, structure_lines, 0, self.config
        )
        
        if self.config.output_format == 'markdown':
            return f"```\n{''.join(structure_lines)}```"
        else:
            return ''.join(structure_lines)
    
    def analyze_files(self, 
                     target_patterns: Optional[List[str]] = None,
                     ignore_file: Optional[str] = None) -> str:
        """Analyze file contents based on patterns or full project"""
        ignore_file = ignore_file or self.config.default_ignore_file
        ignore_file_path = self.project_root / ignore_file
        ignore_func = FileUtils.parse_gitignore(ignore_file_path)
        
        if target_patterns:
            files = FileUtils.get_files_by_patterns(
                self.project_root, target_patterns, ignore_func, self.config
            )
        else:
            files = FileUtils.get_files_in_directory(
                self.project_root, self.project_root, ignore_func, self.config
            )
        
        return Formatter.format_file_contents(
            files, self.project_root, self.config.output_format, self.config.include_binary_info
        )
    
    def get_project_stats(self) -> dict:
        """Get basic project statistics"""
        ignore_file_path = self.project_root / self.config.default_ignore_file
        ignore_func = FileUtils.parse_gitignore(ignore_file_path)
        
        all_files = FileUtils.get_files_in_directory(
            self.project_root, self.project_root, ignore_func, self.config
        )
        
        stats = {
            'total_files': len(all_files),
            'file_types': {},
            'total_size': 0,
            'largest_file': None,
            'largest_file_size': 0
        }
        
        for file_path in all_files:
            try:
                file_size = file_path.stat().st_size
                stats['total_size'] += file_size
                
                if file_size > stats['largest_file_size']:
                    stats['largest_file'] = str(file_path.relative_to(self.project_root))
                    stats['largest_file_size'] = file_size
                
                ext = file_path.suffix.lower()
                if ext in stats['file_types']:
                    stats['file_types'][ext] += 1
                else:
                    stats['file_types'][ext] = 1
                    
            except OSError:
                continue
        
        return stats