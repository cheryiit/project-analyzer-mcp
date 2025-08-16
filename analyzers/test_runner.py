"""
Enhanced Test Runner for TrBotMaster
Runs all tests and generates comprehensive reports
"""

import subprocess
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestRunner:
    """Enhanced test runner with comprehensive reporting"""
    
    def __init__(self):
        self.project_root = project_root
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        
    def run_pytest_suite(self, test_path: str, test_name: str) -> Dict[str, Any]:
        """Run a pytest suite and capture results"""
        print(f"\n🧪 Running {test_name}...")
        
        cmd = [
            sys.executable, "-m", "pytest", 
            str(test_path),
            "-v",
            "--tb=short",
            "--json-report",
            f"--json-report-file={self.project_root}/tests/results_{test_name}.json"
        ]
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Try to load JSON report
            json_file = self.project_root / f"tests/results_{test_name}.json"
            json_data = None
            if json_file.exists():
                try:
                    with open(json_file, 'r') as f:
                        json_data = json.load(f)
                except Exception as e:
                    print(f"Warning: Could not load JSON report for {test_name}: {e}")
            
            return {
                'name': test_name,
                'path': str(test_path),
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'duration': duration,
                'json_data': json_data,
                'success': result.returncode == 0
            }
            
        except subprocess.TimeoutExpired:
            return {
                'name': test_name,
                'path': str(test_path),
                'returncode': -1,
                'stdout': '',
                'stderr': 'Test timed out after 5 minutes',
                'duration': 300,
                'json_data': None,
                'success': False
            }
        except Exception as e:
            return {
                'name': test_name,
                'path': str(test_path),
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'duration': 0,
                'json_data': None,
                'success': False
            }
    
    def run_custom_tests(self) -> Dict[str, Any]:
        """Run custom integration tests"""
        print("\n🔧 Running custom integration tests...")
        
        try:
            # Import and run the enhanced integration tests
            from tests.enhanced_integration_tests import run_comprehensive_tests
            
            start_time = time.time()
            summary = run_comprehensive_tests()
            end_time = time.time()
            
            success = summary['total_errors'] == 0 and summary['total_exceptions'] == 0
            
            return {
                'name': 'custom_integration',
                'path': 'tests/enhanced_integration_tests.py',
                'returncode': 0 if success else 1,
                'stdout': f"Completed with {summary['total_errors']} errors, {summary['total_warnings']} warnings, {summary['total_exceptions']} exceptions",
                'stderr': '',
                'duration': end_time - start_time,
                'json_data': summary,
                'success': success
            }
            
        except Exception as e:
            return {
                'name': 'custom_integration',
                'path': 'tests/enhanced_integration_tests.py',
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'duration': 0,
                'json_data': None,
                'success': False
            }
    
    def discover_test_files(self) -> List[Dict[str, str]]:
        """Discover all test files in the project"""
        test_files = []
        
        # Core test directories
        test_dirs = [
            ('parser-tests', 'Parser Tests'),
            ('ui-tests', 'UI Tests'),
            ('service-tests', 'Service Tests'),
            ('core-tests', 'Core Tests'),
            ('integration-tests', 'Integration Tests'),
            ('bot-detection', 'Bot Detection Tests')
        ]
        
        for dir_name, display_name in test_dirs:
            test_dir = self.project_root / 'tests' / dir_name
            if test_dir.exists():
                for test_file in test_dir.glob('test_*.py'):
                    test_files.append({
                        'path': test_file,
                        'name': f"{dir_name}_{test_file.stem}",
                        'display_name': f"{display_name} - {test_file.stem}"
                    })
        
        # Root level test files
        for test_file in (self.project_root / 'tests').glob('test_*.py'):
            test_files.append({
                'path': test_file,
                'name': f"root_{test_file.stem}",
                'display_name': f"Root Tests - {test_file.stem}"
            })
        
        return test_files
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and collect results"""
        self.start_time = time.time()
        
        print("🚀 Starting comprehensive test suite...")
        print(f"📁 Project root: {self.project_root}")
        
        all_results = {}
        
        # Discover test files
        test_files = self.discover_test_files()
        print(f"📋 Found {len(test_files)} test files")
        
        # Run pytest on each test file
        for test_info in test_files:
            result = self.run_pytest_suite(test_info['path'], test_info['name'])
            all_results[test_info['name']] = result
        
        # Run custom integration tests
        custom_result = self.run_custom_tests()
        all_results['custom_integration'] = custom_result
        
        self.end_time = time.time()
        self.test_results = all_results
        
        return all_results
    
    def generate_summary_report(self) -> str:
        """Generate a summary report of all test results"""
        if not self.test_results:
            return "No test results available."
        
        total_duration = self.end_time - self.start_time if self.start_time and self.end_time else 0
        
        report = []
        report.append("=" * 80)
        report.append("COMPREHENSIVE TEST SUITE REPORT")
        report.append("=" * 80)
        report.append(f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Duration: {total_duration:.2f} seconds")
        report.append("")
        
        # Summary statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['success'])
        failed_tests = total_tests - passed_tests
        
        report.append("SUMMARY:")
        report.append(f"  Total Test Suites: {total_tests}")
        report.append(f"  Passed: {passed_tests}")
        report.append(f"  Failed: {failed_tests}")
        report.append(f"  Success Rate: {(passed_tests/total_tests*100):.1f}%")
        report.append("")
        
        # Detailed results
        report.append("DETAILED RESULTS:")
        for name, result in self.test_results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            duration = f"{result['duration']:.2f}s"
            report.append(f"  {status} {name:<30} ({duration})")
            
            if not result['success']:
                if result['stderr']:
                    # Show first few lines of stderr
                    stderr_lines = result['stderr'].split('\n')[:3]
                    for line in stderr_lines:
                        if line.strip():
                            report.append(f"    Error: {line.strip()}")
        
        report.append("")
        
        # Critical issues summary
        critical_issues = []
        performance_issues = []
        
        for name, result in self.test_results.items():
            if not result['success']:
                critical_issues.append(f"{name}: {result['stderr'][:100]}")
            
            if result['duration'] > 30:  # Tests taking more than 30 seconds
                performance_issues.append(f"{name}: {result['duration']:.2f}s")
        
        if critical_issues:
            report.append("CRITICAL ISSUES:")
            for issue in critical_issues[:10]:  # Show first 10
                report.append(f"  ❌ {issue}")
            if len(critical_issues) > 10:
                report.append(f"  ... and {len(critical_issues) - 10} more issues")
            report.append("")
        
        if performance_issues:
            report.append("PERFORMANCE ISSUES:")
            for issue in performance_issues:
                report.append(f"  ⚠️  {issue}")
            report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS:")
        if failed_tests == 0:
            report.append("  🎉 All tests passed! Great job!")
        else:
            report.append(f"  🔧 Fix {failed_tests} failing test suite(s)")
            report.append("  📝 Review error messages above for specific issues")
        
        if performance_issues:
            report.append("  ⚡ Optimize slow tests for better performance")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_detailed_report(self) -> Path:
        """Save detailed test report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.project_root / f"test_report_{timestamp}.json"
        
        detailed_report = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'total_duration': self.end_time - self.start_time if self.start_time and self.end_time else 0,
                'project_root': str(self.project_root)
            },
            'summary': {
                'total_suites': len(self.test_results),
                'passed': sum(1 for result in self.test_results.values() if result['success']),
                'failed': sum(1 for result in self.test_results.values() if not result['success'])
            },
            'results': self.test_results
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(detailed_report, f, indent=2, default=str)
        
        return report_file
    
    def check_environment(self) -> Dict[str, Any]:
        """Check test environment and dependencies"""
        print("🔍 Checking test environment...")
        
        env_check = {
            'python_version': sys.version,
            'project_root_exists': self.project_root.exists(),
            'tests_directory_exists': (self.project_root / 'tests').exists(),
            'dependencies': {}
        }
        
        # Check for pytest
        try:
            import pytest
            env_check['dependencies']['pytest'] = pytest.__version__
        except ImportError:
            env_check['dependencies']['pytest'] = 'NOT INSTALLED'
        
        # Check for other test dependencies
        test_deps = ['unittest', 'mock', 'pathlib']
        for dep in test_deps:
            try:
                module = __import__(dep)
                if hasattr(module, '__version__'):
                    env_check['dependencies'][dep] = module.__version__
                else:
                    env_check['dependencies'][dep] = 'Available'
            except ImportError:
                env_check['dependencies'][dep] = 'NOT AVAILABLE'
        
        return env_check


def main():
    """Main entry point for test runner"""
    runner = TestRunner()
    
    # Check environment
    env_check = runner.check_environment()
    
    if not env_check['project_root_exists']:
        print("❌ Project root not found!")
        sys.exit(1)
    
    if not env_check['tests_directory_exists']:
        print("❌ Tests directory not found!")
        sys.exit(1)
    
    # Run all tests
    try:
        print("🧪 Running comprehensive test suite...")
        results = runner.run_all_tests()
        
        # Generate and display summary
        summary_report = runner.generate_summary_report()
        print(summary_report)
        
        # Save detailed report
        detailed_report_file = runner.save_detailed_report()
        print(f"\n📄 Detailed report saved to: {detailed_report_file}")
        
        # Exit with appropriate code
        failed_count = sum(1 for result in results.values() if not result['success'])
        if failed_count > 0:
            print(f"\n❌ {failed_count} test suite(s) failed.")
            sys.exit(1)
        else:
            print("\n✅ All tests passed!")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Fatal error during test execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()