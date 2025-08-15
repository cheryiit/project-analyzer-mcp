"""
Code Analysis Module for MCP Project Analyzer
Based on core-tests/test_code_analysis.py
"""

import ast
import importlib
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, Set
import json


class CodeAnalyzer:
    """Analyzes Python code for common errors"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.errors = []
        self.warnings = []

    def analyze_all(self) -> Dict[str, List[str]]:
        """Run all analysis checks"""
        self.errors = []
        self.warnings = []

        # Get all Python files
        python_files = self._get_python_files()

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
        
        python_files = self._get_python_files()
        
        if analysis_type == "syntax":
            self._check_syntax_errors(python_files)
        elif analysis_type == "imports":
            self._check_import_errors(python_files)
        elif analysis_type == "parameters":
            self._check_parameter_mismatches(python_files)
        elif analysis_type == "methods":
            self._check_class_method_signatures(python_files)
        elif analysis_type == "comprehensive":
            return self.analyze_all()
        else:
            self.errors.append(f"Unknown analysis type: {analysis_type}")
            
        return {"errors": self.errors, "warnings": self.warnings}

    def _get_python_files(self) -> List[Path]:
        """Get all Python files in the project"""
        python_files = []

        # Skip venv, __pycache__, .git, storage
        skip_dirs = {
            "venv", "__pycache__", ".git", "storage", ".pytest_cache", 
            "node_modules", "mcp-servers"
        }

        for root, dirs, files in os.walk(self.project_root):
            # Remove skip directories from dirs list to prevent walking into them
            dirs[:] = [d for d in dirs if d not in skip_dirs]

            for file in files:
                if file.endswith(".py"):
                    python_files.append(Path(root) / file)

        return python_files

    def _check_syntax_errors(self, files: List[Path]) -> None:
        """Check for Python syntax errors"""
        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                ast.parse(content, filename=str(file_path))

            except SyntaxError as e:
                self.errors.append(
                    f"SYNTAX ERROR in {file_path}: Line {e.lineno}: {e.msg}"
                )
            except Exception as e:
                self.warnings.append(f"Could not parse {file_path}: {e}")

    def _check_import_errors(self, files: List[Path]) -> None:
        """Check for import errors"""
        # Add project root to Python path
        sys.path.insert(0, str(self.project_root))

        for file_path in files:
            try:
                # Get relative module path
                rel_path = file_path.relative_to(self.project_root)

                # Skip __init__.py files and files in venv
                if rel_path.name == "__init__.py" or "venv" in str(rel_path):
                    continue

                # Convert path to module name
                module_parts = list(rel_path.parts[:-1]) + [rel_path.stem]
                module_name = ".".join(module_parts)

                # Try to import the module
                try:
                    # Remove from cache if already imported
                    if module_name in sys.modules:
                        del sys.modules[module_name]

                    importlib.import_module(module_name)

                except ImportError as e:
                    # Check if it's a missing dependency or internal import issue
                    error_msg = str(e)
                    if "No module named" in error_msg:
                        if any(
                            pkg in error_msg
                            for pkg in ["selenium", "streamlit", "loguru", "pandas", "playwright"]
                        ):
                            # External dependency issue
                            self.warnings.append(
                                f"MISSING DEPENDENCY in {file_path}: {error_msg}"
                            )
                        else:
                            # Internal import issue
                            self.errors.append(
                                f"IMPORT ERROR in {file_path}: {error_msg}"
                            )
                    else:
                        self.errors.append(f"IMPORT ERROR in {file_path}: {error_msg}")

                except Exception as e:
                    # Other errors during import (like parameter mismatches)
                    self.errors.append(f"IMPORT ERROR in {file_path}: {str(e)}")

            except Exception as e:
                self.warnings.append(f"Could not check imports for {file_path}: {e}")

        # Remove project root from Python path
        if str(self.project_root) in sys.path:
            sys.path.remove(str(self.project_root))

    def _check_parameter_mismatches(self, files: List[Path]) -> None:
        """Check for function/method parameter mismatches"""
        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content, filename=str(file_path))

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

                        defaults_count = (
                            len(node.args.defaults) if node.args.defaults else 0
                        )
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
                                f"PARAMETER ERROR in {file_path}:{call_line}: "
                                f"Function '{call_name}' requires {func_def['required_args']} args "
                                f"but {total_provided} provided"
                            )
                        elif total_provided > func_def["total_args"]:
                            self.errors.append(
                                f"PARAMETER ERROR in {file_path}:{call_line}: "
                                f"Function '{call_name}' takes {func_def['total_args']} args "
                                f"but {total_provided} provided"
                            )

            except Exception as e:
                self.warnings.append(f"Could not check parameters in {file_path}: {e}")

    def _check_undefined_variables(self, files: List[Path]) -> None:
        """Check for undefined variables (basic check)"""
        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content, filename=str(file_path))

                # Track defined names per scope
                defined_names = set()

                # Add built-in names and common Python functions
                defined_names.update([
                    "print", "str", "int", "float", "list", "dict", "len", "range",
                    "enumerate", "Exception", "ValueError", "TypeError", "ImportError",
                    "KeyError", "AttributeError", "FileNotFoundError", "SyntaxError",
                    "KeyboardInterrupt", "StopIteration", "isinstance", "hasattr",
                    "getattr", "setattr", "delattr", "bool", "tuple", "set", "max",
                    "min", "sum", "abs", "all", "any", "open", "iter", "next", "zip",
                    "map", "filter", "sorted", "reversed", "format", "repr", "hash",
                    "id", "type", "super", "property", "staticmethod", "classmethod",
                    "callable", "vars", "dir", "globals", "locals", "exec", "eval",
                    "compile", "input", "round", "pow", "divmod", "chr", "ord"
                ])

                for node in ast.walk(tree):
                    # Track imports
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
                                    f"UNDEFINED VARIABLE in {file_path}:{node.lineno}: "
                                    f"'{node.id}' may be undefined"
                                )

            except Exception as e:
                self.warnings.append(
                    f"Could not check undefined variables in {file_path}: {e}"
                )

    def _check_class_method_signatures(self, files: List[Path]) -> None:
        """Check for class method signature issues"""
        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content, filename=str(file_path))

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                # Check if method has 'self' parameter
                                if item.args.args:
                                    first_arg = item.args.args[0].arg
                                    if first_arg != "self" and not item.name.startswith("_"):
                                        # Skip static methods and class methods (basic check)
                                        has_decorator = any(
                                            isinstance(dec, ast.Name)
                                            and dec.id in ["staticmethod", "classmethod"]
                                            for dec in item.decorator_list
                                        )
                                        if not has_decorator:
                                            self.errors.append(
                                                f"METHOD ERROR in {file_path}:{item.lineno}: "
                                                f"Method '{item.name}' should have 'self' as first parameter"
                                            )
                                else:
                                    # Method with no parameters
                                    self.errors.append(
                                        f"METHOD ERROR in {file_path}:{item.lineno}: "
                                        f"Method '{item.name}' should have 'self' as first parameter"
                                    )

            except Exception as e:
                self.warnings.append(
                    f"Could not check class methods in {file_path}: {e}"
                )

    def format_results(self, results: Dict[str, List[str]], output_format: str = "markdown") -> str:
        """Format analysis results in specified format"""
        if output_format == "json":
            return json.dumps(results, indent=2, ensure_ascii=False)
        elif output_format == "markdown":
            return self._format_as_markdown(results)
        else:
            return self._format_as_plain(results)

    def _format_as_markdown(self, results: Dict[str, List[str]]) -> str:
        """Format results as Markdown"""
        output = ["# Code Analysis Report\n\n"]
        
        if results["errors"]:
            output.append(f"## ❌ Errors ({len(results['errors'])})\n\n")
            for error in results["errors"]:
                output.append(f"- {error}\n")
            output.append("\n")
        
        if results["warnings"]:
            output.append(f"## ⚠️ Warnings ({len(results['warnings'])})\n\n")
            for warning in results["warnings"]:
                output.append(f"- {warning}\n")
            output.append("\n")
        
        if not results["errors"] and not results["warnings"]:
            output.append("## ✅ No Issues Found\n\nCode analysis completed successfully with no errors or warnings.\n")
        
        return ''.join(output)

    def _format_as_plain(self, results: Dict[str, List[str]]) -> str:
        """Format results as plain text"""
        output = ["Code Analysis Report\n", "=" * 50, "\n\n"]
        
        if results["errors"]:
            output.append(f"ERRORS ({len(results['errors'])}):\n")
            for error in results["errors"]:
                output.append(f"  • {error}\n")
            output.append("\n")
        
        if results["warnings"]:
            output.append(f"WARNINGS ({len(results['warnings'])}):\n")
            for warning in results["warnings"]:
                output.append(f"  • {warning}\n")
            output.append("\n")
        
        if not results["errors"] and not results["warnings"]:
            output.append("NO ISSUES FOUND\n\nCode analysis completed successfully.\n")
        
        return ''.join(output)

    def save_results(self, results: Dict[str, List[str]], output_file: Path) -> None:
        """Save results to file"""
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("Code Analysis Results\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("Errors:\n")
            for error in results["errors"]:
                f.write(f"  • {error}\n")

            f.write("\nWarnings:\n")
            for warning in results["warnings"]:
                f.write(f"  • {warning}\n")