"""
Advanced code analysis tests to detect common errors before runtime.
This module performs static analysis to catch issues that IDEs typically catch.
"""

import ast
import importlib
import inspect
import os
import sys
import traceback
from pathlib import Path
from typing import Dict, List, Tuple, Any, Set
import pytest
import subprocess


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

        # Write to project_errors.txt AND print to terminal
        self._save_and_print_results()

        return {"errors": self.errors, "warnings": self.warnings}

    def _get_python_files(self) -> List[Path]:
        """Get all Python files in the project"""
        python_files = []

        # Skip venv, __pycache__, .git, storage
        skip_dirs = {
            "venv",
            "__pycache__",
            ".git",
            "storage",
            ".pytest_cache",
            "node_modules",
        }

        for root, dirs, files in os.walk(self.project_root):
            # Remove skip directories from dirs list to prevent walking into
            # them
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
                    # Check if it's a missing dependency or internal import
                    # issue
                    error_msg = str(e)
                    if "No module named" in error_msg:
                        if any(
                            pkg in error_msg
                            for pkg in ["selenium", "streamlit", "loguru", "pandas"]
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
                                f"Function '{call_name}' requires {
                                    func_def['required_args']
                                } args "
                                f"but {total_provided} provided"
                            )
                        elif total_provided > func_def["total_args"]:
                            self.errors.append(
                                f"PARAMETER ERROR in {file_path}:{call_line}: "
                                f"Function '{call_name}' takes {
                                    func_def['total_args']
                                } args "
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
                defined_names.update(
                    [
                        "print",
                        "str",
                        "int",
                        "float",
                        "list",
                        "dict",
                        "len",
                        "range",
                        "enumerate",
                        "Exception",
                        "ValueError",
                        "TypeError",
                        "ImportError",
                        "KeyError",
                        "AttributeError",
                        "FileNotFoundError",
                        "SyntaxError",
                        "KeyboardInterrupt",
                        "StopIteration",
                        "isinstance",
                        "hasattr",
                        "getattr",
                        "setattr",
                        "delattr",
                        "bool",
                        "tuple",
                        "set",
                        "max",
                        "min",
                        "sum",
                        "abs",
                        "all",
                        "any",
                        "open",
                        "iter",
                        "next",
                        "zip",
                        "map",
                        "filter",
                        "sorted",
                        "reversed",
                        "format",
                        "repr",
                        "hash",
                        "id",
                        "type",
                        "super",
                        "property",
                        "staticmethod",
                        "classmethod",
                        "callable",
                        "vars",
                        "dir",
                        "globals",
                        "locals",
                        "exec",
                        "eval",
                        "compile",
                        "input",
                        "round",
                        "pow",
                        "divmod",
                        "chr",
                        "ord",
                    ]
                )

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
                                    f"UNDEFINED VARIABLE in {file_path}:{
                                        node.lineno
                                    }: '{node.id}' may be undefined"
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
                                    if first_arg != "self" and not item.name.startswith(
                                        "_"
                                    ):
                                        # Skip static methods and class methods
                                        # (basic check)
                                        has_decorator = any(
                                            isinstance(dec, ast.Name)
                                            and dec.id
                                            in ["staticmethod", "classmethod"]
                                            for dec in item.decorator_list
                                        )
                                        if not has_decorator:
                                            self.errors.append(
                                                f"METHOD ERROR in {file_path}:{
                                                    item.lineno
                                                }: "
                                                f"Method '{
                                                    item.name
                                                }' should have 'self' as first parameter"
                                            )
                                else:
                                    # Method with no parameters
                                    self.errors.append(
                                        f"METHOD ERROR in {file_path}:{item.lineno}: "
                                        f"Method '{
                                            item.name
                                        }' should have 'self' as first parameter"
                                    )

            except Exception as e:
                self.warnings.append(
                    f"Could not check class methods in {file_path}: {e}"
                )

    def _save_and_print_results(self):
        """Save results to project_errors.txt and print to terminal"""
        # Import config for proper path handling
        try:
            from config.settings import LOGS_DIR
            output_file = LOGS_DIR / "project_errors.txt"
        except ImportError:
            # Fallback if config import fails
            output_file = Path("storage/logs/project_errors.txt")
        
        # Ensure logs directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to project_errors.txt in logs directory
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("Errors:\n")
            for error in self.errors:
                f.write(f"  • {error}\n")

            f.write("\nWarnings:\n")
            for warning in self.warnings:
                f.write(f"  • {warning}\n")

        # Print to terminal
        print("\n" + "=" * 60)
        print("🔍 COMPREHENSIVE CODE ANALYSIS REPORT")
        print("=" * 60)

        if self.errors:
            print(f"\n❌ ERRORS FOUND ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS FOUND ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ NO ISSUES FOUND - CODE LOOKS GOOD!")

        print("\n" + "=" * 60)

        # Fail test if critical errors found
        if self.errors:
            pytest.fail(f"Critical errors found: {len(self.errors)} errors")

    def save_results(self, results: Dict[str, Any]) -> None:
        """Save results to project_errors.txt and print to terminal"""
        # Import config for proper path handling
        try:
            from config.settings import LOGS_DIR
            output_file = LOGS_DIR / "project_errors.txt"
        except ImportError:
            # Fallback if config import fails
            output_file = Path("storage/logs/project_errors.txt")
        
        # Ensure logs directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to project_errors.txt in logs directory
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("Errors:\n")
            for error in self.errors:
                f.write(f"  • {error}\n")

            f.write("\nWarnings:\n")
            for warning in self.warnings:
                f.write(f"  • {warning}\n")

        # Print to terminal
        print("\n" + "=" * 60)
        print("🔍 COMPREHENSIVE CODE ANALYSIS REPORT")
        print("=" * 60)

        if self.errors:
            print(f"\n❌ ERRORS FOUND ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS FOUND ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ NO ISSUES FOUND - CODE LOOKS GOOD!")

        print("\n" + "=" * 60)

        # Fail test if critical errors found
        if self.errors:
            pytest.fail(f"Critical errors found: {len(self.errors)} errors")


# Test class
class TestCodeAnalysis:
    """Test class for code analysis"""

    def setup_method(self):
        """Setup for each test"""
        self.project_root = Path(__file__).parent.parent
        self.analyzer = CodeAnalyzer(self.project_root)

    def test_syntax_errors(self):
        """Test for syntax errors"""
        python_files = self.analyzer._get_python_files()
        self.analyzer._check_syntax_errors(python_files)

        if self.analyzer.errors:
            error_msg = "\n".join(self.analyzer.errors)
            pytest.fail(f"Syntax errors found:\n{error_msg}")

    def test_import_errors(self):
        """Test for import errors"""
        python_files = self.analyzer._get_python_files()
        self.analyzer._check_import_errors(python_files)

        # Filter out known external dependency warnings and parser test files
        critical_errors = []
        for error in self.analyzer.errors:
            # Skip external dependencies
            if any(
                pkg in error
                for pkg in [
                    "selenium",
                    "streamlit",
                    "loguru",
                    "pandas",
                    "playwright",
                    "webdriver",
                    "beautifulsoup4",
                ]
            ):
                continue
            # Skip parser test files and conftest issues
            if any(
                skip in error for skip in ["test_", "conftest", "parser", "_parser"]
            ):
                continue
            critical_errors.append(error)

        if critical_errors:
            error_msg = "\n".join(critical_errors)
            pytest.fail(f"Import errors found:\n{error_msg}")

    def test_parameter_mismatches(self):
        """Test for parameter mismatches"""
        python_files = self.analyzer._get_python_files()
        self.analyzer._check_parameter_mismatches(python_files)

        if self.analyzer.errors:
            error_msg = "\n".join(self.analyzer.errors)
            pytest.fail(f"Parameter errors found:\n{error_msg}")

    def test_class_method_signatures(self):
        """Test for class method signature issues"""
        python_files = self.analyzer._get_python_files()
        self.analyzer._check_class_method_signatures(python_files)

        if self.analyzer.errors:
            error_msg = "\n".join(self.analyzer.errors)
            pytest.fail(f"Class method errors found:\n{error_msg}")

    def test_comprehensive_analysis(self):
        """Run comprehensive analysis and report all issues"""
        results = self.analyzer.analyze_all()

        # Note: Printing and saving to project_errors.txt is handled in analyze_all()
        # This test will fail if critical errors are found


def test_flake8_compliance():
    """Test code compliance using flake8"""
    try:
        result = subprocess.run(
            ["flake8", "--config=tests/.flake8", "."],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        if result.returncode != 0:
            pytest.fail(f"Flake8 errors found:\\n{result.stdout}")

    except FileNotFoundError:
        pytest.skip("Flake8 not installed")


if __name__ == "__main__":
    # Allow running this file directly for quick analysis
    analyzer = CodeAnalyzer(Path(__file__).parent.parent.parent)
    results = analyzer.analyze_all()

    # Results are already printed by _save_and_print_results()
    print("Analysis complete! Check project_errors.txt for details.")
