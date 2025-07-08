"""Unit tests for the home network monitor application."""

import tempfile
import os
from unittest.mock import patch, MagicMock

# Import modules to test
from validators import validate_config
from database import DatabaseManager
from logging_config import setup_logging, get_logger

# Simple assertion function to replace pytest
def assert_equal(actual, expected, message=""):
    if actual != expected:
        raise AssertionError(f"Expected {expected}, got {actual}. {message}")

def assert_true(condition, message=""):
    if not condition:
        raise AssertionError(f"Expected True, got False. {message}")

def assert_raises(exception_type, func, *args, **kwargs):
    try:
        func(*args, **kwargs)
        raise AssertionError(f"Expected {exception_type.__name__} to be raised")
    except exception_type:
        pass  # Expected exception was raised


class TestValidators:
    """Test cases for the validators module."""
    
    def test_validate_config_valid_http_and_ping(self):
        """Test validation with valid HTTP and ping configuration."""
        config = {
            'name': 'Test Site',
            'url': 'https://example.com',
            'ping_host': 'example.com',
            'enable_http': True,
            'enable_ping': True
        }
        # Should not raise an exception
        validate_config(config)
    
    def test_validate_config_valid_http_only(self):
        """Test validation with valid HTTP-only configuration."""
        config = {
            'name': 'Test Site',
            'url': 'https://example.com',
            'enable_http': True,
            'enable_ping': False
        }
        # Should not raise an exception
        validate_config(config)
    
    def test_validate_config_valid_ping_only(self):
        """Test validation with valid ping-only configuration."""
        config = {
            'name': 'Test Site',
            'ping_host': 'example.com',
            'enable_http': False,
            'enable_ping': True
        }
        # Should not raise an exception
        validate_config(config)
    
    def test_validate_config_missing_name(self):
        """Test validation fails when name is missing."""
        config = {
            'url': 'https://example.com',
            'enable_http': True
        }
        assert_raises(ValueError, validate_config, config)
    
    def test_validate_config_empty_name(self):
        """Test validation fails when name is empty."""
        config = {
            'name': '   ',  # Empty name
            'url': 'https://example.com',
            'enable_http': True
        }
        assert_raises(ValueError, validate_config, config)
    
    def test_validate_config_no_tests_enabled(self):
        """Test validation fails when no tests are enabled."""
        config = {
            'name': 'Test Site',
            'url': 'https://example.com',
            'ping_host': 'example.com',
            'enable_http': False,
            'enable_ping': False
        }
        assert_raises(ValueError, validate_config, config)
    
    def test_validate_config_http_enabled_missing_url(self):
        """Test validation fails when HTTP is enabled but URL is missing."""
        config = {
            'name': 'Test Site',
            'enable_http': True,
            'enable_ping': False
        }
        assert_raises(ValueError, validate_config, config)
    
    def test_validate_config_ping_enabled_missing_host(self):
        """Test validation fails when ping is enabled but host is missing."""
        config = {
            'name': 'Test Site',
            'enable_http': False,
            'enable_ping': True
        }
        assert_raises(ValueError, validate_config, config)


class TestDatabaseManager:
    """Test cases for the DatabaseManager class."""
    
    def setup_method(self):
        """Set up test environment."""
        # Create a temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Mock config.DATABASE_PATH to use temp file
        with patch('config.DATABASE_PATH', self.db_path):
            with patch('config.MONITOR_SITES', []):  # Empty sites for testing
                self.db = DatabaseManager(self.db_path)
    
    def teardown_method(self):
        """Clean up test environment."""
        # Remove temporary database file
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_insert_valid_configuration(self):
        """Test inserting a valid configuration."""
        config = {
            'name': 'Test Site',
            'url': 'https://example.com',
            'ping_host': 'example.com',
            'enabled': True,
            'enable_http': True,
            'enable_ping': True
        }
        
        # Should not raise an exception
        self.db.insert_configuration(config)
        
        # Verify configuration was inserted
        configs = self.db.get_all_configurations()
        assert_equal(len(configs), 1)
        assert_equal(configs.iloc[0]['name'], 'Test Site')
    
    def test_insert_invalid_configuration(self):
        """Test inserting an invalid configuration raises an error."""
        config = {
            'name': '',  # Invalid empty name
            'url': 'https://example.com',
            'enable_http': True
        }
        
        assert_raises(ValueError, self.db.insert_configuration, config)
    
    def test_get_enabled_configurations(self):
        """Test getting only enabled configurations."""
        config1 = {
            'name': 'Enabled Site',
            'url': 'https://enabled.com',
            'enabled': True,
            'enable_http': True,
            'enable_ping': False
        }
        config2 = {
            'name': 'Disabled Site',
            'url': 'https://disabled.com',
            'enabled': False,
            'enable_http': True,
            'enable_ping': False
        }
        
        self.db.insert_configuration(config1)
        self.db.insert_configuration(config2)
        
        enabled_configs = self.db.get_enabled_configurations()
        assert_equal(len(enabled_configs), 1)
        assert_equal(enabled_configs[0]['name'], 'Enabled Site')


class TestLoggingConfig:
    """Test cases for the logging configuration."""
    
    def test_setup_logging_creates_logger(self):
        """Test that setup_logging creates a logger."""
        logger = setup_logging()
        assert_equal(logger.name, 'home_net_monitor')
        assert_equal(logger.level, 20)  # INFO level
    
    def test_get_logger_creates_named_logger(self):
        """Test that get_logger creates a logger with the correct name."""
        logger = get_logger('test_module')
        assert_equal(logger.name, 'home_net_monitor.test_module')
    
    def test_setup_logging_with_file(self):
        """Test that setup_logging can create a file handler."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            log_file = temp_file.name
        
        try:
            logger = setup_logging(log_file=log_file)
            assert_equal(len(logger.handlers), 2)  # Console and file handlers
            
            # Test that log file was created
            assert_true(os.path.exists(log_file))
        finally:
            # Clean up
            if os.path.exists(log_file):
                os.unlink(log_file)


if __name__ == '__main__':
    # Run tests if this file is executed directly
    import sys
    
    # Simple test runner
    test_classes = [TestValidators, TestDatabaseManager, TestLoggingConfig]
    
    for test_class in test_classes:
        test_instance = test_class()
        
        # Run setup if it exists
        if hasattr(test_instance, 'setup_method'):
            test_instance.setup_method()
        
        # Run all test methods
        for method_name in dir(test_instance):
            if method_name.startswith('test_'):
                print(f"Running {test_class.__name__}.{method_name}...")
                try:
                    method = getattr(test_instance, method_name)
                    method()
                    print(f"  ✓ PASSED")
                except Exception as e:
                    print(f"  ✗ FAILED: {e}")
        
        # Run teardown if it exists
        if hasattr(test_instance, 'teardown_method'):
            test_instance.teardown_method()
    
    print("\nTest run completed.")
