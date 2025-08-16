"""Main MCP Server implementation"""

import json
import sys
import asyncio
from pathlib import Path
from typing import Dict, Any
import logging

from .config import ProjectAnalyzerConfig
from .analyzer import ProjectAnalyzer
from ..utils.formatters import Formatter


class ProjectAnalyzerMCPServer:
    """Project Analyzer MCP Server - Enhanced modular version"""
    
    def __init__(self, config_dict: Dict[str, Any] = None):
        self.config = ProjectAnalyzerConfig(config_dict)
        self.analyzer = ProjectAnalyzer(self.config)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Background tasks tracking
        self._background_tasks = {}
        
    async def handle_project_structure_async(self, args: Dict[str, Any]) -> str:
        """Handle project structure generation asynchronously"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.handle_project_structure, args
        )
    
    def handle_project_structure(self, args: Dict[str, Any]) -> str:
        """Handle project structure generation"""
        project_path = Path(args.get('project_path', '.'))
        ignore_file = args.get('ignore_file')
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
    
    async def handle_analyze_files_async(self, args: Dict[str, Any]) -> str:
        """Handle file analysis asynchronously"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.handle_analyze_files, args
        )
    
    def handle_analyze_files(self, args: Dict[str, Any]) -> str:
        """Handle file analysis"""
        project_path = Path(args.get('project_path', '.'))
        target_patterns = args.get('target_patterns')
        ignore_file = args.get('ignore_file')
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
            self.config.update_config(config_dict)
            self.analyzer = ProjectAnalyzer(self.config)
            
            return f"Configuration updated successfully. New settings: {json.dumps(self.config.to_dict(), indent=2)}"
        except Exception as e:
            self.logger.error(f"Error configuring analyzer: {e}")
            return f"Error: {str(e)}"
    
    async def handle_analyze_code_async(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle code analysis asynchronously"""
        project_path = Path(args.get('project_path', '.'))
        analysis_type = args.get('analysis_type', 'comprehensive')
        output_format = args.get('output_format', 'markdown')
        save_results = args.get('save_results', False)
        
        try:
            # Run analysis
            if self.config.enable_background_mode:
                results = await self.analyzer.analyze_code_async(project_path, analysis_type)
            else:
                results = self.analyzer.analyze_code_sync(project_path, analysis_type)
            
            # Format results
            formatted_output = Formatter.format_analysis_results(results, output_format)
            
            # Save results if requested
            if save_results:
                output_file = project_path / "logs" / "project_errors.txt"
                from ..utils.file_utils import FileUtils
                FileUtils.safe_write_file(output_file, formatted_output)
            
            # Return both formatted text and structured data
            return {
                "content": [{"type": "text", "text": formatted_output}],
                "isError": len(results.get("errors", [])) > 0,
                "_meta": {
                    **results.get('_meta', {}),
                    "output_format": output_format,
                    "background_mode": self.config.enable_background_mode
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
    
    def handle_analyze_code(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle code analysis synchronously (for compatibility)"""
        try:
            # Try to get current event loop
            loop = asyncio.get_running_loop()
            # If we're in an event loop, run synchronously
            return asyncio.run_coroutine_threadsafe(
                self.handle_analyze_code_async(args), loop
            ).result(timeout=30)
        except RuntimeError:
            # No event loop running, safe to use asyncio.run
            return asyncio.run(self.handle_analyze_code_async(args))
    
    async def handle_get_stats_async(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get project statistics asynchronously"""
        project_path = Path(args.get('project_path', '.'))
        
        try:
            stats = await asyncio.get_event_loop().run_in_executor(
                None, self.analyzer.get_project_stats, project_path
            )
            
            return {
                "content": [{"type": "text", "text": json.dumps(stats, indent=2)}],
                "isError": False,
                "_meta": {
                    "project_path": str(project_path),
                    "stats": stats
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting project stats: {e}")
            return {
                "content": [{"type": "text", "text": f"Error getting stats: {str(e)}"}],
                "isError": True,
                "_meta": {
                    "project_path": str(project_path),
                    "error": str(e)
                }
            }
    
    def handle_get_stats(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get project statistics synchronously"""
        try:
            # Try to get current event loop
            loop = asyncio.get_running_loop()
            # If we're in an event loop, run synchronously
            return asyncio.run_coroutine_threadsafe(
                self.handle_get_stats_async(args), loop
            ).result(timeout=30)
        except RuntimeError:
            # No event loop running, safe to use asyncio.run
            return asyncio.run(self.handle_get_stats_async(args))
    
    async def start_background_task(self, task_name: str, args: Dict[str, Any]) -> str:
        """Start a background analysis task"""
        if not self.config.enable_background_mode:
            return "Background mode is disabled"
        
        task_id = f"{task_name}_{len(self._background_tasks)}"
        
        if task_name == "analyze_code":
            task = asyncio.create_task(self.handle_analyze_code_async(args))
        elif task_name == "analyze_files":
            task = asyncio.create_task(self.handle_analyze_files_async(args))
        elif task_name == "project_structure":
            task = asyncio.create_task(self.handle_project_structure_async(args))
        else:
            return f"Unknown task type: {task_name}"
        
        self._background_tasks[task_id] = task
        return f"Background task started: {task_id}"
    
    async def get_background_task_result(self, task_id: str) -> Dict[str, Any]:
        """Get result from background task"""
        if task_id not in self._background_tasks:
            return {"error": f"Task {task_id} not found"}
        
        task = self._background_tasks[task_id]
        
        if task.done():
            try:
                result = task.result()
                del self._background_tasks[task_id]  # Clean up
                return {"result": result, "status": "completed"}
            except Exception as e:
                del self._background_tasks[task_id]  # Clean up
                return {"error": str(e), "status": "failed"}
        else:
            return {"status": "running"}
    
    def run_standalone(self):
        """Run as standalone script for testing"""
        try:
            print("=== Project Analyzer MCP Server v2.0 ===")
            print("Testing enhanced modular functionality...\n")
            
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
            
            # Test code analysis (sync version for testing)
            print("\n=== Testing Code Analysis ===")
            try:
                project_path = Path('.')
                results = self.analyzer.analyze_code_sync(project_path, 'comprehensive')
                formatted_output = Formatter.format_analysis_results(results, 'markdown')
                
                print(f"Errors: {results.get('_meta', {}).get('errors_count', 0)}")
                print(f"Warnings: {results.get('_meta', {}).get('warnings_count', 0)}")
                print(formatted_output[:200] + "..." if len(formatted_output) > 200 else formatted_output)
            except Exception as e:
                print(f"Code analysis error: {e}")
            
            # Test project stats (sync version for testing)
            print("\n=== Testing Project Stats ===")
            try:
                stats = self.analyzer.get_project_stats(Path('.'))
                import json
                stats_json = json.dumps(stats, indent=2)
                print(stats_json[:300] + "..." if len(stats_json) > 300 else stats_json)
            except Exception as e:
                print(f"Stats error: {e}")
            
        except Exception as e:
            print(f"Error during testing: {e}")
    
    async def process_mcp_request_async(self, request_json: str) -> str:
        """Process MCP request asynchronously"""
        try:
            request = json.loads(request_json)
            tool_name = request.get('tool')
            arguments = request.get('arguments', {})
            
            if tool_name == 'project_structure':
                return await self.handle_project_structure_async(arguments)
            elif tool_name == 'analyze_files':
                return await self.handle_analyze_files_async(arguments)
            elif tool_name == 'analyze_code':
                result = await self.handle_analyze_code_async(arguments)
                return json.dumps(result)
            elif tool_name == 'configure_analyzer':
                return self.handle_configure_analyzer(arguments)
            elif tool_name == 'get_stats':
                result = await self.handle_get_stats_async(arguments)
                return json.dumps(result)
            elif tool_name == 'start_background_task':
                task_name = arguments.get('task_name')
                task_args = arguments.get('task_args', {})
                return await self.start_background_task(task_name, task_args)
            elif tool_name == 'get_background_result':
                task_id = arguments.get('task_id')
                result = await self.get_background_task_result(task_id)
                return json.dumps(result)
            else:
                return f"Unknown tool: {tool_name}"
                
        except Exception as e:
            return f"Error processing request: {str(e)}"
    
    def process_mcp_request(self, request_json: str) -> str:
        """Process MCP request (compatibility method)"""
        try:
            # Try to get current event loop
            loop = asyncio.get_running_loop()
            # If we're in an event loop, run synchronously
            return asyncio.run_coroutine_threadsafe(
                self.process_mcp_request_async(request_json), loop
            ).result(timeout=30)
        except RuntimeError:
            # No event loop running, safe to use asyncio.run
            return asyncio.run(self.process_mcp_request_async(request_json))