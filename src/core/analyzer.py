"""Main analyzer orchestration"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
import asyncio

from .config import ProjectAnalyzerConfig
from ..analyzers.code_analyzer import CodeAnalyzer
from ..analyzers.structure_analyzer import StructureAnalyzer


class ProjectAnalyzer:
    """Core project analysis orchestrator"""
    
    def __init__(self, config: ProjectAnalyzerConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def create_code_analyzer(self, project_path: Path) -> CodeAnalyzer:
        """Create a code analyzer instance"""
        return CodeAnalyzer(project_path, self.config.max_concurrent_analyses)
    
    def create_structure_analyzer(self, project_path: Path) -> StructureAnalyzer:
        """Create a structure analyzer instance"""
        return StructureAnalyzer(project_path, self.config)
    
    def generate_project_structure(self, 
                                 project_path: Path, 
                                 ignore_file: Optional[str] = None) -> str:
        """Generate hierarchical project structure"""
        structure_analyzer = self.create_structure_analyzer(project_path)
        return structure_analyzer.generate_project_structure(ignore_file)
    
    def analyze_files(self, 
                     project_path: Path, 
                     target_patterns: Optional[List[str]] = None,
                     ignore_file: Optional[str] = None) -> str:
        """Analyze file contents based on patterns or full project"""
        structure_analyzer = self.create_structure_analyzer(project_path)
        return structure_analyzer.analyze_files(target_patterns, ignore_file)
    
    async def analyze_code_async(self, 
                               project_path: Path,
                               analysis_type: str = 'comprehensive') -> Dict[str, Any]:
        """Run code analysis asynchronously"""
        if not self.config.enable_background_mode:
            return self.analyze_code_sync(project_path, analysis_type)
        
        code_analyzer = self.create_code_analyzer(project_path)
        return await code_analyzer.run_background_analysis(analysis_type)
    
    def analyze_code_sync(self, 
                         project_path: Path,
                         analysis_type: str = 'comprehensive') -> Dict[str, Any]:
        """Run code analysis synchronously"""
        code_analyzer = self.create_code_analyzer(project_path)
        
        try:
            if analysis_type == 'comprehensive':
                results = code_analyzer.analyze_all()
            else:
                results = code_analyzer.analyze_specific(analysis_type)
            
            # Add metadata
            results['_meta'] = {
                'analysis_type': analysis_type,
                'project_path': str(project_path),
                'errors_count': len(results.get('errors', [])),
                'warnings_count': len(results.get('warnings', [])),
                'sync_mode': True
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Code analysis failed: {e}")
            return {
                'errors': [f"Analysis failed: {str(e)}"],
                'warnings': [],
                '_meta': {
                    'analysis_type': analysis_type,
                    'project_path': str(project_path),
                    'error': str(e),
                    'sync_mode': True
                }
            }
    
    def get_project_stats(self, project_path: Path) -> Dict[str, Any]:
        """Get comprehensive project statistics"""
        structure_analyzer = self.create_structure_analyzer(project_path)
        return structure_analyzer.get_project_stats()