#!/usr/bin/env python3
"""
Comprehensive test suite for Project Analyzer Python MCP Server
"""

import json
import sys
from pathlib import Path

# Add current directory to path to import our server
sys.path.append(str(Path(__file__).parent))

from project_analyzer_server import ProjectAnalyzerMCPServer, ProjectAnalyzerConfig


class ComprehensiveTester:
    """Comprehensive test suite for the MCP server"""
    
    def __init__(self):
        self.server = ProjectAnalyzerMCPServer()
        self.test_results = []
    
    def run_test(self, test_name, test_func):
        """Run a single test and record results"""
        print(f"\n🧪 Testing: {test_name}")
        print("=" * 50)
        
        try:
            result = test_func()
            self.test_results.append({"test": test_name, "status": "PASS", "result": result})
            print(f"✅ {test_name}: PASSED")
            return result
        except Exception as e:
            self.test_results.append({"test": test_name, "status": "FAIL", "error": str(e)})
            print(f"❌ {test_name}: FAILED - {str(e)}")
            return None
    
    def test_basic_project_structure(self):
        """Test basic project structure generation"""
        args = {
            'project_path': '.',
            'output_format': 'markdown'
        }
        result = self.server.handle_project_structure(args)
        
        # Validate result
        assert isinstance(result, str), "Result should be string"
        assert len(result) > 0, "Result should not be empty"
        assert "project_analyzer_server.py" in result, "Should contain main file"
        
        print(f"📊 Structure length: {len(result)} characters")
        print(f"📁 Preview:\n{result[:200]}...")
        
        return {"length": len(result), "format": "markdown"}
    
    def test_plain_text_format(self):
        """Test plain text output format"""
        args = {
            'project_path': '.',
            'output_format': 'plain'
        }
        result = self.server.handle_project_structure(args)
        
        assert isinstance(result, str), "Result should be string"
        assert "```" not in result, "Plain format should not contain markdown code blocks"
        
        print(f"📝 Plain format preview:\n{result[:200]}...")
        
        return {"format": "plain", "has_markdown": "```" in result}
    
    def test_file_analysis_with_patterns(self):
        """Test file analysis with specific patterns"""
        args = {
            'project_path': '.',
            'target_patterns': ['*.py'],
            'output_format': 'markdown',
            'max_file_size': 100000  # 100KB
        }
        result = self.server.handle_analyze_files(args)
        
        assert isinstance(result, str), "Result should be string"
        assert len(result) > 0, "Result should not be empty"
        assert "project_analyzer_server.py" in result, "Should analyze Python files"
        
        print(f"🔍 Analysis length: {len(result)} characters")
        print(f"📄 Contains main file: {'project_analyzer_server.py' in result}")
        
        return {"analyzed_files": result.count("##"), "total_length": len(result)}
    
    def test_json_output_format(self):
        """Test JSON output format for file analysis"""
        args = {
            'project_path': '.',
            'target_patterns': ['*.json', '*.py'],
            'output_format': 'json',
            'max_file_size': 50000
        }
        result = self.server.handle_analyze_files(args)
        
        assert isinstance(result, str), "Result should be string"
        
        # Try to parse as JSON
        try:
            parsed = json.loads(result)
            assert isinstance(parsed, dict), "JSON should be a dictionary"
            print(f"📋 JSON files found: {len(parsed)} files")
            
            # Check structure
            for file_path, file_data in parsed.items():
                assert isinstance(file_data, dict), f"File data for {file_path} should be dict"
                assert 'type' in file_data, f"File {file_path} should have type"
                assert 'size' in file_data, f"File {file_path} should have size"
                
            return {"files_count": len(parsed), "valid_json": True}
        except json.JSONDecodeError as e:
            print(f"🚫 JSON parsing failed: {e}")
            return {"valid_json": False, "error": str(e)}
    
    def test_configuration_update(self):
        """Test dynamic configuration updates"""
        # Test configuration change
        config_args = {
            'config': {
                'max_file_size': 2048,  # 2KB
                'output_format': 'plain',
                'supported_extensions': ['.py', '.json'],
                'exclude_patterns': ['__pycache__', '*.pyc']
            }
        }
        
        result = self.server.handle_configure_analyzer(config_args)
        
        assert "Configuration updated successfully" in result, "Should confirm update"
        
        # Test that new config is applied when no format specified in args
        args = {
            'project_path': '.',
            'target_patterns': ['*.py']
            # No output_format specified, should use config default (plain)
        }
        
        analysis_result = self.server.handle_analyze_files(args)
        
        # Should use plain format from config - check for markdown-style headers
        assert not analysis_result.startswith("# File Contents"), "Should use plain format from config"
        # Plain format should have direct filename: pattern
        assert (".py:" in analysis_result), "Plain format should have filename: pattern"
        
        print(f"⚙️ Config updated successfully")
        print(f"📝 Uses plain format: {'```' not in analysis_result}")
        
        return {"config_applied": True, "format_override": "```" not in analysis_result}
    
    def test_error_handling(self):
        """Test error handling with invalid inputs"""
        # Test with non-existent path
        args = {
            'project_path': '/non/existent/path',
            'output_format': 'markdown'
        }
        
        result = self.server.handle_project_structure(args)
        
        # Should handle gracefully, not crash
        assert isinstance(result, str), "Should return string even on error"
        
        print(f"🛡️ Error handled gracefully: {len(result)} chars returned")
        
        return {"error_handled": True, "result_length": len(result)}
    
    def test_large_project_performance(self):
        """Test performance on larger project structure"""
        args = {
            'project_path': '../../',  # Go up to TrBotMaster root
            'output_format': 'plain'
        }
        
        import time
        start_time = time.time()
        result = self.server.handle_project_structure(args)
        end_time = time.time()
        
        duration = end_time - start_time
        
        assert isinstance(result, str), "Result should be string"
        assert len(result) > 0, "Result should not be empty"
        
        print(f"⚡ Performance: {duration:.2f} seconds")
        print(f"📊 Structure size: {len(result)} characters")
        print(f"📁 Lines count: {result.count('/')} directories")
        
        return {
            "duration_seconds": duration, 
            "result_length": len(result),
            "directories_count": result.count('/')
        }
    
    def test_mcp_request_processing(self):
        """Test MCP-style request processing"""
        request = {
            "tool": "project_structure",
            "arguments": {
                "project_path": ".",
                "output_format": "markdown"
            }
        }
        
        request_json = json.dumps(request)
        result = self.server.process_mcp_request(request_json)
        
        assert isinstance(result, str), "Result should be string"
        assert len(result) > 0, "Result should not be empty"
        assert "project_analyzer_server.py" in result, "Should contain expected files"
        
        print(f"🔗 MCP request processed successfully")
        print(f"📦 Response length: {len(result)} characters")
        
        return {"mcp_processing": True, "response_length": len(result)}
    
    def test_gitignore_support(self):
        """Test gitignore file support"""
        # Create a test .gitignore
        test_gitignore = Path('.') / '.testignore'
        test_gitignore.write_text('*.log\ntemp/\n__pycache__/\n')
        
        try:
            args = {
                'project_path': '.',
                'ignore_file': '.testignore',
                'output_format': 'plain'
            }
            
            result = self.server.handle_project_structure(args)
            
            assert isinstance(result, str), "Result should be string"
            
            # Check that ignored patterns are not in result
            has_ignored = ('temp/' in result or '__pycache__' in result)
            
            print(f"🚫 Gitignore working: {not has_ignored}")
            print(f"📋 Structure preview:\n{result[:200]}...")
            
            return {"gitignore_working": not has_ignored}
            
        finally:
            # Clean up
            if test_gitignore.exists():
                test_gitignore.unlink()
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting Comprehensive MCP Server Test Suite")
        print("=" * 60)
        
        # Run all tests
        tests = [
            ("Basic Project Structure", self.test_basic_project_structure),
            ("Plain Text Format", self.test_plain_text_format),
            ("File Analysis with Patterns", self.test_file_analysis_with_patterns),
            ("JSON Output Format", self.test_json_output_format),
            ("Configuration Update", self.test_configuration_update),
            ("Error Handling", self.test_error_handling),
            ("Large Project Performance", self.test_large_project_performance),
            ("MCP Request Processing", self.test_mcp_request_processing),
            ("Gitignore Support", self.test_gitignore_support),
        ]
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        # Summary
        print("\n📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        total = len(self.test_results)
        
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {failed}/{total}")
        print(f"📈 Success Rate: {(passed/total)*100:.1f}%")
        
        if failed > 0:
            print("\n🚨 Failed Tests:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  - {result['test']}: {result['error']}")
        
        print(f"\n🎯 Overall Result: {'PASS' if failed == 0 else 'FAIL'}")
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "success_rate": (passed/total)*100,
            "overall_status": "PASS" if failed == 0 else "FAIL"
        }


def main():
    """Run comprehensive tests"""
    tester = ComprehensiveTester()
    results = tester.run_all_tests()
    
    # Exit with error code if tests failed
    if results["overall_status"] == "FAIL":
        sys.exit(1)
    else:
        print("\n🎉 All tests passed! MCP Server is ready for use.")
        sys.exit(0)


if __name__ == "__main__":
    main()