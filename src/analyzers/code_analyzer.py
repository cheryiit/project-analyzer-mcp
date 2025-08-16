"""
Code Analysis Module for MCP Project Analyzer
Enhanced version with better error handling and async support
"""

import ast
import importlib
import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple, Any, Set
import json
import logging
from concurrent.futures import ThreadPoolExecutor

from ..utils.file_utils import FileUtils
from ..utils.formatters import Formatter


class CodeAnalyzer:
    """Analyzes Python code for common errors with async support"""

    def __init__(self, project_root: Path, max_workers: int = 3):
        self.project_root = project_root
        self.max_workers = max_workers
        self.errors = []
        self.warnings = []
        self.logger = logging.getLogger(__name__)

    async def analyze_all_async(self) -> Dict[str, List[str]]:
        """Run all analysis checks asynchronously"""
        self.errors = []
        self.warnings = []

        # Get all Python files
        python_files = FileUtils.get_python_files(self.project_root)

        # Run all checks concurrently
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            loop = asyncio.get_event_loop()
            
            tasks = [
                loop.run_in_executor(executor, self._check_syntax_errors, python_files),
                loop.run_in_executor(executor, self._check_import_errors, python_files),
                loop.run_in_executor(executor, self._check_parameter_mismatches, python_files),
                loop.run_in_executor(executor, self._check_undefined_variables, python_files),
                loop.run_in_executor(executor, self._check_class_method_signatures, python_files)
            ]
            
            await asyncio.gather(*tasks)

        return {"errors": self.errors, "warnings": self.warnings}

    def analyze_all(self) -> Dict[str, List[str]]:
        """Run all analysis checks synchronously"""
        self.errors = []
        self.warnings = []

        # Get all Python files
        python_files = FileUtils.get_python_files(self.project_root)

        # Run all checks
        self._check_syntax_errors(python_files)
        self._check_import_errors(python_files)
        self._check_parameter_mismatches(python_files)
        self._check_undefined_variables(python_files)
        self._check_class_method_signatures(python_files)

        return {"errors": self.errors, "warnings": self.warnings}

    def analyze_specific(self, analysis_type: str) -> Dict[str, List[str]]:
        """Run specific analysis type"""
        self.errors = []
        self.warnings = []
        
        python_files = FileUtils.get_python_files(self.project_root)
        
        if analysis_type == "syntax":
            self._check_syntax_errors(python_files)
        elif analysis_type == "imports":
            self._check_import_errors(python_files)
        elif analysis_type == "parameters":
            self._check_parameter_mismatches(python_files)
        elif analysis_type == "variables":
            self._check_undefined_variables(python_files)
        elif analysis_type == "methods":
            self._check_class_method_signatures(python_files)
        else:
            self.warnings.append(f"Unknown analysis type: {analysis_type}")
        
        return {"errors": self.errors, "warnings": self.warnings}

    def _check_syntax_errors(self, python_files: List[Path]) -> None:
        """Check for syntax errors in Python files"""
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                ast.parse(content)
            except SyntaxError as e:
                self.errors.append(f"Syntax error in {py_file}: {e}")
            except UnicodeDecodeError:
                self.warnings.append(f"Could not decode {py_file}")
            except Exception as e:
                self.warnings.append(f"Error reading {py_file}: {e}")

    def _check_import_errors(self, python_files: List[Path]) -> None:
        """Check for import errors"""
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            self._check_module_exists(alias.name, py_file)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            self._check_module_exists(node.module, py_file)
                            
            except Exception as e:
                self.warnings.append(f"Could not check imports for {py_file}: {e}")

    def _check_module_exists(self, module_name: str, file_path: Path) -> None:
        """Check if a module can be imported"""
        try:
            # Add project root to path temporarily
            original_path = sys.path.copy()
            if str(self.project_root) not in sys.path:
                sys.path.insert(0, str(self.project_root))
            
            importlib.import_module(module_name)
            
        except ImportError:
            # Check if it's a local module that might not exist
            if '.' in module_name or module_name.startswith('_'):
                self.warnings.append(f"Potential missing module '{module_name}' in {file_path}")
            else:
                self.errors.append(f"Cannot import '{module_name}' in {file_path}")
        except Exception as e:
            self.warnings.append(f"Error checking module '{module_name}' in {file_path}: {e}")
        finally:
            sys.path = original_path

    def _check_parameter_mismatches(self, python_files: List[Path]) -> None:
        """Check for function/method parameter mismatches - Enhanced version"""
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content, filename=str(py_file))
                
                # Find all function/method calls and definitions
                function_calls = []
                function_defs = {}
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name):
                            func_name = node.func.id
                            args_count = len(node.args)
                            kwargs_count = len(node.keywords)
                            function_calls.append(
                                (func_name, args_count, kwargs_count, node.lineno)
                            )
                    
                    elif isinstance(node, ast.FunctionDef):
                        # Count parameters
                        args_count = len(node.args.args)
                        # Subtract 'self' for methods in classes
                        if args_count > 0 and node.args.args[0].arg == "self":
                            args_count -= 1
                        
                        defaults_count = len(node.args.defaults) if node.args.defaults else 0
                        required_args = args_count - defaults_count
                        
                        function_defs[node.name] = {
                            "required_args": required_args,
                            "total_args": args_count,
                            "line": node.lineno,
                        }
                
                # Check for mismatches
                for call_name, call_args, call_kwargs, call_line in function_calls:
                    if call_name in function_defs:
                        func_def = function_defs[call_name]
                        total_provided = call_args + call_kwargs
                        
                        if total_provided < func_def["required_args"]:
                            self.errors.append(
                                f"PARAMETER ERROR in {py_file}:{call_line}: "
                                f"Function '{call_name}' requires {func_def['required_args']} args "
                                f"but {total_provided} provided"
                            )
                        elif total_provided > func_def["total_args"]:
                            self.errors.append(
                                f"PARAMETER ERROR in {py_file}:{call_line}: "
                                f"Function '{call_name}' accepts max {func_def['total_args']} args "
                                f"but {total_provided} provided"
                            )
                                
            except Exception as e:
                self.warnings.append(f"Could not check parameters for {py_file}: {e}")

    def _check_undefined_variables(self, python_files: List[Path]) -> None:
        """Check for undefined variables - Enhanced version"""
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content, filename=str(py_file))
                
                # Track defined names in different scopes
                defined_names = set()
                
                # Collect imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            defined_names.add(alias.asname or alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        for alias in node.names:
                            defined_names.add(alias.asname or alias.name)
                    
                    # Track assignments
                    elif isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                defined_names.add(target.id)
                    
                    # Track function definitions
                    elif isinstance(node, ast.FunctionDef):
                        defined_names.add(node.name)
                    
                    # Track class definitions
                    elif isinstance(node, ast.ClassDef):
                        defined_names.add(node.name)
                    
                    # Check variable usage
                    elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                        if node.id not in defined_names:
                            # Skip some common cases
                            if not (node.id.startswith("_") or node.id.isupper()):
                                self.warnings.append(
                                    f"UNDEFINED VARIABLE in {py_file}:{node.lineno}: '{node.id}' may be undefined"
                                )
                            
            except Exception as e:
                self.warnings.append(f"Could not check variables for {py_file}: {e}")

    def _check_class_method_signatures(self, python_files: List[Path]) -> None:
        """Check for class method signature issues - Enhanced version"""
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content, filename=str(py_file))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                # Check if method has 'self' parameter
                                if item.args.args:
                                    first_arg = item.args.args[0].arg
                                    if first_arg != "self" and not item.name.startswith("_"):
                                        # Skip static methods and class methods
                                        has_decorator = any(
                                            isinstance(dec, ast.Name)
                                            and dec.id in ["staticmethod", "classmethod"]
                                            for dec in item.decorator_list
                                        )
                                        if not has_decorator:
                                            self.errors.append(
                                                f"METHOD ERROR in {py_file}:{item.lineno}: "
                                                f"Method '{item.name}' should have 'self' as first parameter"
                                            )
                                else:
                                    # Method with no parameters
                                    self.errors.append(
                                        f"METHOD ERROR in {py_file}:{item.lineno}: "
                                        f"Method '{item.name}' should have 'self' as first parameter"
                                    )
                                    
            except Exception as e:
                self.warnings.append(f"Could not check class methods for {py_file}: {e}")

    def format_results(self, results: Dict[str, Any], output_format: str = 'markdown') -> str:
        """Format analysis results"""
        return Formatter.format_analysis_results(results, output_format)

    def save_results(self, results: Dict[str, Any], output_file: Path = None) -> bool:
        """Save analysis results to file with enhanced reporting"""
        try:
            if output_file is None:
                # Default to logs directory
                output_file = Path("logs") / "project_errors.txt"
            
            # Ensure directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create comprehensive report
            report_lines = []
            report_lines.append("=" * 60)
            report_lines.append("🔍 COMPREHENSIVE CODE ANALYSIS REPORT")
            report_lines.append("=" * 60)
            report_lines.append(f"Analysis Date: {self._get_timestamp()}")
            report_lines.append(f"Project Path: {self.project_root}")
            report_lines.append("")
            
            errors = results.get('errors', [])
            warnings = results.get('warnings', [])
            
            if errors:
                report_lines.append(f"❌ ERRORS FOUND ({len(errors)}):")
                for error in errors:
                    report_lines.append(f"  • {error}")
                report_lines.append("")
            
            if warnings:
                report_lines.append(f"⚠️  WARNINGS FOUND ({len(warnings)}):")
                for warning in warnings:
                    report_lines.append(f"  • {warning}")
                report_lines.append("")
            
            if not errors and not warnings:
                report_lines.append("✅ NO ISSUES FOUND - CODE LOOKS GOOD!")
                report_lines.append("")
            
            # Add summary
            report_lines.append("📊 SUMMARY:")
            report_lines.append(f"  Total Errors: {len(errors)}")
            report_lines.append(f"  Total Warnings: {len(warnings)}")
            report_lines.append(f"  Analysis Status: {'❌ FAILED' if errors else '✅ PASSED'}")
            report_lines.append("=" * 60)
            
            # Write to file
            report_content = "\n".join(report_lines)
            return FileUtils.safe_write_file(output_file, report_content)
            
        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")
            return False
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def print_terminal_report(self, results: Dict[str, Any]) -> None:
        """Print detailed report to terminal"""
        errors = results.get('errors', [])
        warnings = results.get('warnings', [])
        
        print("\n" + "=" * 60)
        print("🔍 COMPREHENSIVE CODE ANALYSIS REPORT")
        print("=" * 60)
        
        if errors:
            print(f"\n❌ ERRORS FOUND ({len(errors)}):")
            for error in errors:
                print(f"  • {error}")
        
        if warnings:
            print(f"\n⚠️  WARNINGS FOUND ({len(warnings)}):")
            for warning in warnings:
                print(f"  • {warning}")
        
        if not errors and not warnings:
            print("\n✅ NO ISSUES FOUND - CODE LOOKS GOOD!")
        
        print("\n" + "=" * 60)
        print(f"📊 SUMMARY: {len(errors)} errors, {len(warnings)} warnings")
        print("=" * 60)

    async def run_background_analysis(self, analysis_type: str = 'comprehensive') -> Dict[str, Any]:
        """Run analysis in background mode"""
        try:
            if analysis_type == 'comprehensive':
                results = await self.analyze_all_async()
            else:
                results = self.analyze_specific(analysis_type)
            
            # Add metadata
            results['_meta'] = {
                'analysis_type': analysis_type,
                'project_path': str(self.project_root),
                'errors_count': len(results.get('errors', [])),
                'warnings_count': len(results.get('warnings', [])),
                'timestamp': str(asyncio.get_event_loop().time())
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Background analysis failed: {e}")
            return {
                'errors': [f"Analysis failed: {str(e)}"],
                'warnings': [],
                '_meta': {
                    'analysis_type': analysis_type,
                    'project_path': str(self.project_root),
                    'error': str(e)
                }
            }