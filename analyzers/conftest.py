"""
Pytest configuration file for TrBotMaster tests
Enhanced version with comprehensive test coverage support
"""

import os
import sys
import pytest
import asyncio
from pathlib import Path
from typing import Generator, Dict, Any, Optional
from unittest.mock import Mock, MagicMock, patch
import tempfile
import shutil

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import test profile manager
from tests.test_profiles.test_profile_manager import get_test_profile_manager

# Set test mode environment variable
os.environ["TRBOT_TEST_MODE"] = "1"

# Configure test database
os.environ["TRBOT_TEST_DB"] = str(project_root / "test_travian_bot.db")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment once per session."""
    # Initialize test profile manager
    test_profile_manager = get_test_profile_manager()
    
    # Clean up old test profiles but keep current one
    test_profile_manager.cleanup_old_test_profiles(keep_current=True)
    
    # Create or get test profile
    success, test_profile_path = test_profile_manager.get_or_create_test_profile()
    if success:
        print(f"Test profile ready at: {test_profile_path}")
    
    # Mark that we are in test mode - prevents creating full browser profiles
    if "PYTEST_CURRENT_TEST" not in os.environ:
        os.environ["PYTEST_CURRENT_TEST"] = "true"
        should_cleanup = True
    else:
        should_cleanup = False
    
    yield
    
    # Cleanup after all tests
    if should_cleanup and "PYTEST_CURRENT_TEST" in os.environ:
        os.environ.pop("PYTEST_CURRENT_TEST", None)


@pytest.fixture
def test_profile_path():
    """Get the test profile path for tests that need it."""
    test_profile_manager = get_test_profile_manager()
    return test_profile_manager.get_test_profile_path()


@pytest.fixture
def test_html_file():
    """Fixture to get test HTML files from parser test pages."""
    def _get_test_file(parser_name: str, file_name: str) -> str:
        """Get path to test HTML file."""
        test_file_path = (
            project_root
            / "core"
            / "parsers"
            / "parser-test-pages"
            / parser_name
            / file_name
        )
        
        if not test_file_path.exists():
            pytest.fail(f"Test file not found: {test_file_path}")
            
        return str(test_file_path)
    
    return _get_test_file


@pytest.fixture
def load_test_html():
    """Fixture to load test HTML content."""
    def _load_html(parser_name: str, file_name: str) -> str:
        """Load HTML content from test file."""
        test_file_path = (
            project_root
            / "core"
            / "parsers"
            / "parser-test-pages"
            / parser_name
            / file_name
        )
        
        if not test_file_path.exists():
            pytest.fail(f"Test file not found: {test_file_path}")
            
        with open(test_file_path, "r", encoding="utf-8") as f:
            return f.read()
    
    return _load_html


@pytest.fixture
def mock_browser_service():
    """Enhanced mock browser service for comprehensive testing."""
    class MockBrowserService:
        def __init__(self):
            self.current_url = "https://ts1.travian.com"
            self.page_content = "<html></html>"
            self.is_healthy = True
            self.error_count = 0
            self.call_log = []
            
        async def navigate(self, url: str) -> bool:
            self.call_log.append(f"navigate:{url}")
            if not self.is_healthy:
                raise Exception("Browser service unhealthy")
            self.current_url = url
            return True
            
        async def get_current_url(self) -> str:
            self.call_log.append("get_current_url")
            if not self.is_healthy:
                raise Exception("Browser service unhealthy")
            return self.current_url
            
        async def parse_current_page(self, parser_type: str = None) -> dict:
            self.call_log.append(f"parse_current_page:{parser_type}")
            if not self.is_healthy:
                raise Exception("Browser service unhealthy")
            return {"is_login_page": False}
            
        async def type_text(self, selector: str, text: str) -> bool:
            self.call_log.append(f"type_text:{selector}:{text}")
            if not self.is_healthy:
                raise Exception("Browser service unhealthy")
            return True
            
        async def click(self, selector: str) -> bool:
            self.call_log.append(f"click:{selector}")
            if not self.is_healthy:
                raise Exception("Browser service unhealthy")
            return True
            
        async def get_login_status(self) -> dict:
            self.call_log.append("get_login_status")
            if not self.is_healthy:
                raise Exception("Browser service unhealthy")
            return {"is_logged_in": False}
            
        def set_unhealthy(self):
            """Simulate service failure for error testing"""
            self.is_healthy = False
            
        def set_healthy(self):
            """Restore service health"""
            self.is_healthy = True
    
    return MockBrowserService()


@pytest.fixture
def mock_account_service():
    """Enhanced mock account service with error simulation capabilities."""
    class MockAccountService:
        def __init__(self):
            self.accounts = []
            self.is_available = True
            self.error_mode = None
            self.call_log = []
            
        def list_accounts(self, include_inactive: bool = True):
            self.call_log.append(f"list_accounts:{include_inactive}")
            if not self.is_available:
                raise AttributeError("'NoneType' object has no attribute 'list_accounts'")
            if self.error_mode == "database_error":
                raise Exception("Database connection failed")
            return self.accounts
            
        def get_account(self, account_id: int):
            self.call_log.append(f"get_account:{account_id}")
            if not self.is_available:
                return None
            if self.error_mode == "not_found":
                return None
            return {"id": account_id, "email": "test@test.com", "server": "ts1.travian.com"}
            
        def create_account(self, **kwargs):
            self.call_log.append(f"create_account:{kwargs}")
            if not self.is_available:
                raise Exception("Account service not available")
            if self.error_mode == "validation_error":
                return False, "Invalid email format", None
            account = {"id": len(self.accounts) + 1, **kwargs}
            self.accounts.append(account)
            return True, "Account created successfully", account
            
        def delete_account(self, account_id: int, delete_profile: bool = True):
            self.call_log.append(f"delete_account:{account_id}:{delete_profile}")
            if not self.is_available:
                raise Exception("Account service not available")
            if self.error_mode == "not_found":
                return False, "Account not found"
            return True, "Account deleted successfully"
            
        def start_account_bot(self, account_id: int):
            self.call_log.append(f"start_account_bot:{account_id}")
            if not self.is_available:
                raise Exception("Account service not available")
            if self.error_mode == "bot_start_error":
                return False, "Failed to start bot"
            return True, "Bot started successfully"
            
        def stop_account_bot(self, account_id: int):
            self.call_log.append(f"stop_account_bot:{account_id}")
            if not self.is_available:
                raise Exception("Account service not available")
            return True, "Bot stopped successfully"
            
        def set_unavailable(self):
            """Simulate service unavailability"""
            self.is_available = False
            
        def set_available(self):
            """Restore service availability"""
            self.is_available = True
            
        def set_error_mode(self, mode: str):
            """Set specific error mode for testing"""
            self.error_mode = mode
            
        def clear_error_mode(self):
            """Clear error mode"""
            self.error_mode = None
    
    return MockAccountService()


@pytest.fixture
def mock_bot_manager():
    """Enhanced mock bot manager with comprehensive functionality."""
    class MockBotManager:
        def __init__(self):
            self.profiles = {}
            self.running_sessions = {}
            self.is_healthy = True
            self.call_log = []
            
        def create_profile(self, name: str, **kwargs):
            self.call_log.append(f"create_profile:{name}")
            if not self.is_healthy:
                return False, "Bot manager unavailable"
            if name in self.profiles:
                return False, "Profile already exists"
            self.profiles[name] = {"name": name, **kwargs}
            return True, "Profile created successfully"
            
        def delete_profile(self, name: str):
            self.call_log.append(f"delete_profile:{name}")
            if not self.is_healthy:
                return False, "Bot manager unavailable"
            if name not in self.profiles:
                return False, "Profile not found"
            del self.profiles[name]
            return True, "Profile deleted successfully"
            
        def get_profile(self, name: str):
            self.call_log.append(f"get_profile:{name}")
            if not self.is_healthy:
                return None
            return self.profiles.get(name)
            
        def start_profile(self, name: str):
            self.call_log.append(f"start_profile:{name}")
            if not self.is_healthy:
                return False, "Bot manager unavailable"
            if name not in self.profiles:
                return False, "Profile not found"
            self.running_sessions[name] = True
            return True, "Profile started successfully"
            
        def stop_profile(self, name: str):
            self.call_log.append(f"stop_profile:{name}")
            if not self.is_healthy:
                return False, "Bot manager unavailable"
            if name in self.running_sessions:
                del self.running_sessions[name]
            return True, "Profile stopped successfully"
            
        def is_profile_running(self, name: str):
            self.call_log.append(f"is_profile_running:{name}")
            if not self.is_healthy:
                return False
            return name in self.running_sessions
            
        def get_running_sessions(self):
            self.call_log.append("get_running_sessions")
            if not self.is_healthy:
                return {}
            return self.running_sessions.copy()
            
        def set_unhealthy(self):
            """Simulate bot manager failure"""
            self.is_healthy = False
            
        def set_healthy(self):
            """Restore bot manager health"""
            self.is_healthy = True
    
    return MockBotManager()


@pytest.fixture
def test_file_path():
    """Get path to test files."""
    def _get_path(filename: str) -> Path:
        test_files_dir = project_root / "tests" / "test_files"
        test_files_dir.mkdir(exist_ok=True)
        
        file_path = test_files_dir / filename
        if not file_path.exists():
            # Create empty file if it doesn't exist
            file_path.touch()
            
        return file_path
    
    return _get_path


@pytest.fixture
def temp_directory():
    """Create temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_test_data():
    """Provide sample test data for various test scenarios."""
    return {
        "accounts": [
            {
                "id": 1,
                "email": "test1@example.com",
                "server": "https://ts1.travian.com",
                "tribe": "romans",
                "is_active": True,
                "profile_name": "test_profile_1"
            },
            {
                "id": 2,
                "email": "test2@example.com",
                "server": "https://ts2.travian.com",
                "tribe": "gauls",
                "is_active": False,
                "profile_name": None
            }
        ],
        "profiles": [
            {
                "name": "test_profile_1",
                "user_agent": "Mozilla/5.0 Test Agent",
                "is_running": False
            }
        ]
    }


@pytest.fixture
def error_scenarios():
    """Provide different error scenarios for testing."""
    return {
        "service_unavailable": "Service not available",
        "database_error": "Database connection failed",
        "validation_error": "Invalid input data",
        "network_error": "Network connection timeout",
        "permission_error": "Permission denied",
        "file_not_found": "Required file not found",
        "browser_error": "Browser launch failed"
    }


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Clean up test files after each test."""
    yield
    
    # Clean up any temporary test files
    test_files_dir = project_root / "tests" / "test_files"
    if test_files_dir.exists():
        import shutil
        shutil.rmtree(test_files_dir, ignore_errors=True)


@pytest.fixture
def patch_streamlit():
    """Patch streamlit functions for testing."""
    with patch('streamlit.error') as mock_error, \
         patch('streamlit.success') as mock_success, \
         patch('streamlit.warning') as mock_warning, \
         patch('streamlit.info') as mock_info, \
         patch('streamlit.rerun') as mock_rerun:
        
        yield {
            'error': mock_error,
            'success': mock_success,
            'warning': mock_warning,
            'info': mock_info,
            'rerun': mock_rerun
        }


@pytest.fixture
def capture_exceptions():
    """Capture and log exceptions during tests for analysis."""
    exceptions = []
    
    def exception_handler(exc_type, exc_value, exc_traceback):
        exceptions.append({
            'type': exc_type,
            'value': exc_value,
            'traceback': exc_traceback
        })
        # Still raise the exception
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    original_hook = sys.excepthook
    sys.excepthook = exception_handler
    
    yield exceptions
    
    sys.excepthook = original_hook


# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture
def integration_test_setup():
    """Setup for integration tests with all components."""
    from core.models.database import init_database
    from core.managers.bot import MultiBotManager as BotManager
    from core.services.account_service import AccountService
    
    # Initialize test database
    init_database()
    
    # Create components
    bot_manager = BotManager()
    account_service = AccountService(bot_manager)
    
    return {
        'bot_manager': bot_manager,
        'account_service': account_service
    }


@pytest.fixture
def performance_monitor():
    """Monitor test performance and resource usage."""
    import time
    import psutil
    
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss
    
    yield
    
    end_time = time.time()
    end_memory = psutil.Process().memory_info().rss
    
    duration = end_time - start_time
    memory_delta = end_memory - start_memory
    
    if duration > 5:  # Log slow tests
        print(f"SLOW TEST: {duration:.2f}s")
    if memory_delta > 50 * 1024 * 1024:  # Log memory-heavy tests (>50MB)
        print(f"MEMORY HEAVY TEST: {memory_delta / 1024 / 1024:.2f}MB")
