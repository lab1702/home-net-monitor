"""Unit tests for the home network monitor application."""

import tempfile
import os
from unittest.mock import patch, MagicMock

# Import modules to test
from validators import validate_config
from database import DatabaseManager

# Zero-dep assertions: bare `assert` covers equality; only "did it raise?"
# needs a helper.
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
        # DuckDB won't open an existing empty file; remove it so it creates a
        # fresh valid database at this path.
        os.unlink(self.db_path)
        
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
        assert len(configs) == 1
        assert configs.iloc[0]['name'] == 'Test Site'
    
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
        assert len(enabled_configs) == 1
        assert enabled_configs[0]['name'] == 'Enabled Site'


class TestRegressions(TestDatabaseManager):
    def _site(self, name='Site', **changes):
        site = {'name': name, 'url': 'https://example.com', 'ping_host': None,
                'enable_http': True, 'enable_ping': False, 'enabled': True}
        site.update(changes)
        self.db.insert_configuration(site)
        return site

    def _result(self, site, age_seconds=0):
        from datetime import datetime, timedelta
        from monitor import _result_row
        result = _result_row(datetime.now() - timedelta(seconds=age_seconds), site,
                             http_success=True, overall_success=True)
        self.db.insert_monitoring_result(result)

    def test_empty_configuration_stays_empty(self):
        site = self._site()
        self.db.delete_configuration(int(self.db.get_all_configurations().iloc[0]['id']))
        with patch('config.MONITOR_SITES', [site]):
            reopened = DatabaseManager(self.db_path)
        assert reopened.get_all_configurations().empty

    def test_documented_false_ping_default(self):
        path = self.db_path + '-defaults'
        try:
            with patch('config.MONITOR_SITES', [{'name': 'HTTP', 'url': 'https://example.com', 'ping_host': False}]):
                db = DatabaseManager(path)
            assert db.get_enabled_configurations()[0]['enable_ping'] is False
            assert db.get_enabled_configurations()[0]['ping_host'] is None
        finally:
            for suffix in ('', '.lock'):
                if os.path.exists(path + suffix):
                    os.unlink(path + suffix)

    def test_current_status_excludes_disabled_deleted_and_renamed_sites(self):
        for name in ('Enabled', 'Disabled', 'Deleted', 'Renamed'):
            self._result(self._site(name))
        ids = self.db.get_all_configurations().set_index('name')['id']
        self.db.delete_configuration(int(ids['Deleted']))
        self.db.update_configuration(int(ids['Disabled']), {'name': 'Disabled', 'enabled': False})
        self.db.update_configuration(int(ids['Renamed']), {'name': 'New', 'url': 'https://example.com',
                                                         'enable_http': True, 'enable_ping': False})
        status = self.db.get_current_status().set_index('site_name')
        assert set(status.index) == {'Enabled', 'New'}
        assert status.loc['Enabled', 'overall_success'] == True
        import pandas as pd
        assert pd.isna(status.loc['New', 'overall_success'])
        assert len(self.db.get_recent_results()) == 4

    def test_stale_status_and_changed_target_are_unknown(self):
        import config
        import pandas as pd
        site = self._site()
        self._result(site, config.STATUS_MAX_AGE_SECONDS + 1)
        assert pd.isna(self.db.get_current_status().iloc[0]['overall_success'])
        self._result(site)
        assert self.db.get_current_status().iloc[0]['overall_success'] == True
        site['url'] = 'https://changed.example'
        self.db.update_configuration(int(self.db.get_all_configurations().iloc[0]['id']), site)
        assert pd.isna(self.db.get_current_status().iloc[0]['overall_success'])

    def test_health_requires_recent_cycle_even_with_old_results(self):
        from datetime import datetime, timedelta
        from database import database_connection
        import health_check
        self._result(self._site(), 3600)
        with patch('config.DATABASE_PATH', self.db_path):
            assert health_check.main() == 1
            self.db.record_heartbeat()
            assert health_check.main() == 0
            with database_connection(self.db_path) as conn:
                conn.execute('UPDATE monitoring_heartbeat SET completed_at = ?',
                             (datetime.now() - timedelta(days=1),))
            assert health_check.main() == 1

    def test_empty_monitoring_cycle_records_health(self):
        from monitoring_service import MonitoringService
        service = MonitoringService.__new__(MonitoringService)
        service.db = self.db
        service.monitor = MagicMock()
        service.monitor.monitor_all_sites.return_value = []
        service.run_monitoring_cycle()
        import health_check
        with patch('config.DATABASE_PATH', self.db_path):
            assert health_check.main() == 0

    def test_database_access_waits_for_other_process(self):
        import subprocess
        import sys
        from concurrent.futures import ThreadPoolExecutor, TimeoutError
        child = subprocess.Popen(
            [sys.executable, '-c',
             'from database import database_connection; import sys; '
             'ctx = database_connection(sys.argv[1]); ctx.__enter__(); '
             'print("locked", flush=True); sys.stdin.readline(); ctx.__exit__(None, None, None)',
             self.db_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, env={**os.environ, 'GIT_NO_LAZY_FETCH': '1', 'OPENBLAS_NUM_THREADS': '1'})
        try:
            assert child.stdout.readline().strip() == 'locked'
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(self.db.get_all_configurations)
                try:
                    assert_raises(TimeoutError, future.result, timeout=0.2)
                finally:
                    child.stdin.write('\n')
                    child.stdin.flush()
                assert future.result(timeout=10).empty
            assert child.wait(timeout=10) == 0, child.stderr.read()
        finally:
            if child.poll() is None:
                child.kill()
                child.wait()
            for pipe in (child.stdin, child.stdout, child.stderr):
                pipe.close()

    def test_configuration_names_are_not_parsed_as_ids(self):
        from streamlit.testing.v1 import AppTest
        self._site('Router ID: branch')
        def app():
            from config_management import render_config_management
            render_config_management()
        with patch('config_management.DatabaseManager', return_value=self.db):
            page = AppTest.from_function(app).run()
        assert not page.exception
        assert page.selectbox[0].value == int(self.db.get_all_configurations().iloc[0]['id'])

    def teardown_method(self):
        super().teardown_method()
        if os.path.exists(self.db_path + '.lock'):
            os.unlink(self.db_path + '.lock')


class TestMonitorRegressions:
    def test_decimal_packet_loss_and_unknown_output(self):
        from monitor import NetworkMonitor
        monitor = NetworkMonitor()
        result = monitor._parse_ping_output('3 packets transmitted, 1 received, 66.6667% packet loss\nrtt min/avg/max/mdev = 1.0/2.0/3.0/0.1 ms')
        assert result['success'] is True
        assert result['packet_loss_percent'] == 66.6667
        assert result['avg_ms'] == 2.0
        assert monitor._parse_ping_output('unexpected output')['success'] is False
        assert monitor._parse_ping_output('101% packet loss')['success'] is False

    def test_platform_ping_commands_and_windows_output(self):
        from monitor import NetworkMonitor
        import config
        for system, count_flag, timeout_flag, timeout in (
                ('Linux', '-c', '-W', str(config.PING_TIMEOUT_SECONDS)),
                ('Darwin', '-c', '-W', str(config.PING_TIMEOUT_SECONDS * 1000)),
                ('Windows', '-n', '-w', str(config.PING_TIMEOUT_SECONDS * 1000))):
            response = MagicMock(returncode=0, stdout='Packets: Sent = 3, Received = 2, Lost = 1 (33% loss),\nMinimum = 1ms, Maximum = 3ms, Average = 2ms')
            with patch('monitor.platform.system', return_value=system), patch('monitor.subprocess.run', return_value=response) as run:
                result = NetworkMonitor().ping_host('example.com')
            args = run.call_args.args[0]
            assert args[args.index(count_flag) + 1] == str(config.PING_COUNT)
            assert args[args.index(timeout_flag) + 1] == timeout
            assert result['packet_loss_percent'] == 33
            assert result['avg_ms'] == 2

    def test_http_never_consumes_redirect_or_final_bodies(self):
        import requests
        from monitor import _http_headers
        responses = []
        for status in (302, 200):
            response = requests.Response()
            response.status_code = status
            response.url = 'https://example.com'
            response.raw = MagicMock()
            response.headers['Location'] = '/next'
            responses.append(response)
        with patch('requests.adapters.HTTPAdapter.send', side_effect=responses) as send:
            result = _http_headers('https://example.com')
        assert result['success'] is True
        assert send.call_count == 2
        assert send.call_args.args[0].url == 'https://example.com/next'
        for response in responses:
            response.raw.read.assert_not_called()
            response.raw.stream.assert_not_called()
            response.raw.close.assert_called()

    def test_http_worker_is_terminated_at_deadline(self):
        from monitor import NetworkMonitor
        context = MagicMock()
        receive, send = MagicMock(), MagicMock()
        context.Pipe.return_value = (receive, send)
        receive.poll.return_value = False
        context.Process.return_value.is_alive.return_value = True
        with patch('monitor.multiprocessing.get_context', return_value=context):
            result = NetworkMonitor().check_http('https://example.com')
        assert result['success'] is False
        context.Process.return_value.terminate.assert_called_once()
        context.Process.return_value.kill.assert_called_once()
        receive.close.assert_called_once()

    def test_http_worker_result_is_returned(self):
        from monitor import NetworkMonitor
        context = MagicMock()
        receive, send = MagicMock(), MagicMock()
        context.Pipe.return_value = (receive, send)
        receive.poll.return_value = True
        receive.recv.return_value = {'success': True, 'status_code': 200, 'response_time_ms': 5}
        context.Process.return_value.is_alive.return_value = False
        with patch('monitor.multiprocessing.get_context', return_value=context):
            assert NetworkMonitor().check_http('https://example.com')['status_code'] == 200

    def test_interval_environment_is_read_and_validated(self):
        import subprocess
        import sys
        for value in ('123', '0', '-1', 'invalid'):
            result = subprocess.run([sys.executable, '-c', 'import config; print(config.CHECK_INTERVAL_SECONDS)'],
                                    env={**os.environ, 'GIT_NO_LAZY_FETCH': '1', 'CHECK_INTERVAL_SECONDS': value},
                                    capture_output=True, text=True)
            if value == '123':
                assert result.returncode == 0 and result.stdout.strip() == value
            else:
                assert result.returncode != 0

    def test_runner_returns_nonzero_for_failure(self):
        from contextlib import redirect_stdout
        from io import StringIO
        class Failing:
            def test_failure(self):
                assert False, 'deliberate failure'
        class BrokenCleanup:
            def test_success(self):
                pass
            def teardown_method(self):
                raise ValueError('cleanup failed')
        with redirect_stdout(StringIO()):
            assert run_tests([Failing]) == 1
            assert run_tests([BrokenCleanup]) == 1


def run_tests(test_classes=None):
    """Run every test and return a process-friendly status, including cleanup errors."""
    if test_classes is None:
        test_classes = [value for name, value in globals().items()
                        if name.startswith('Test') and isinstance(value, type)]
    failures = 0
    for test_class in test_classes:
        for method_name in sorted(name for name in dir(test_class) if name.startswith('test_')):
            test_instance = test_class()
            print(f"Running {test_class.__name__}.{method_name}...")
            try:
                if hasattr(test_instance, 'setup_method'):
                    test_instance.setup_method()
                getattr(test_instance, method_name)()
                print("  ✓ PASSED")
            except Exception as exc:
                failures += 1
                print(f"  ✗ FAILED: {exc}")
            finally:
                try:
                    if hasattr(test_instance, 'teardown_method'):
                        test_instance.teardown_method()
                except Exception as exc:
                    failures += 1
                    print(f"  ✗ FAILED cleanup: {exc}")
    print(f"\nTest run completed: {failures} failures.")
    return int(failures > 0)


if __name__ == '__main__':
    import sys
    sys.exit(run_tests())
