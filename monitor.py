"""Network monitoring functionality."""

import subprocess
import multiprocessing
import json
import os
import platform
from urllib.parse import urljoin
import time
import requests
import re
import logging
from typing import Dict, List
import config

logger = logging.getLogger(__name__)


def _failed_ping() -> Dict:
    """A ping result representing total failure (100% loss, no timings)."""
    return {'success': False, 'avg_ms': None, 'min_ms': None,
            'max_ms': None, 'packet_loss_percent': 100.0}


def _result_row(timestamp, site_config, *, http_success=None, ping_success=None,
                ping_packet_loss_percent=None, overall_success=False) -> Dict:
    """A monitoring-result row with no successful measurements, for failure paths."""
    return {
        'timestamp': timestamp,
        'site_name': site_config['name'],
        'site_url': site_config.get('url'),
        'ping_host': site_config.get('ping_host'),
        'http_status_code': None,
        'http_response_time_ms': None,
        'http_success': http_success,
        'ping_avg_ms': None,
        'ping_min_ms': None,
        'ping_max_ms': None,
        'ping_packet_loss_percent': ping_packet_loss_percent,
        'ping_success': ping_success,
        'overall_success': overall_success,
    }


class _HeaderOnlySession(requests.Session):
    def resolve_redirects(self, *args, **kwargs):
        # Requests otherwise consumes redirect bodies even with stream=True.
        # Follow Location ourselves, closing each response without reading it.
        return iter(())


def _http_headers(url):
    start = time.monotonic()
    with _HeaderOnlySession() as session:
        session.headers.update({'User-Agent': 'NetworkMonitor/1.0'})
        request = session.prepare_request(requests.Request('GET', url))
        for _ in range(6):
            remaining = config.HTTP_TIMEOUT_SECONDS - (time.monotonic() - start)
            if remaining <= 0:
                raise requests.exceptions.Timeout('HTTP deadline expired')
            settings = session.merge_environment_settings(request.url, {}, True, None, None)
            with session.send(request, timeout=remaining, allow_redirects=False,
                              **settings) as response:
                if response.is_redirect:
                    next_url = urljoin(request.url, session.get_redirect_target(response))
                    next_request = session.prepare_request(requests.Request('GET', next_url))
                    authorization = request.headers.get('Authorization')
                    if authorization and not session.should_strip_auth(request.url, next_request.url):
                        # Carry credentials only to destinations permitted by Requests.
                        # Explicit destination credentials take precedence.
                        next_request.headers.setdefault('Authorization', authorization)
                    request = next_request
                    continue
                return {'success': 200 <= response.status_code < 300,
                        'status_code': response.status_code,
                        'response_time_ms': (time.monotonic() - start) * 1000}
    raise requests.exceptions.TooManyRedirects('More than five redirects')


def _http_worker(url, connection):
    try:
        connection.send(_http_headers(url))
    except Exception:
        connection.send({'success': False, 'status_code': None,
                         'response_time_ms': None})
    finally:
        connection.close()


class NetworkMonitor:
    """Performs network monitoring checks."""

    def ping_host(self, host: str, count: int = config.PING_COUNT) -> Dict:
        """Ping a host and return statistics."""
        try:
            # Build ping command based on the operating system
            system = platform.system()
            timeout_ms = str(int(config.PING_TIMEOUT_SECONDS * 1000))
            if system == 'Windows':
                # .NET returns numeric status/timings without localized ping text.
                script = r"""
$ErrorActionPreference = 'Stop'
$ping = New-Object System.Net.NetworkInformation.Ping
$times = @()
try {
    for ($i = 0; $i -lt [int]$env:HOME_NET_PING_COUNT; $i++) {
        try {
            $reply = $ping.Send($env:HOME_NET_PING_HOST, [int]$env:HOME_NET_PING_TIMEOUT_MS)
            if ($reply.Status -eq [System.Net.NetworkInformation.IPStatus]::Success) {
                $times += [double]$reply.RoundtripTime
            }
        } catch { }
        if ($i + 1 -lt [int]$env:HOME_NET_PING_COUNT) { Start-Sleep -Milliseconds 1000 }
    }
    $stats = $times | Measure-Object -Minimum -Maximum -Average
    @{ received = $times.Count; min_ms = $stats.Minimum;
       max_ms = $stats.Maximum; avg_ms = $stats.Average } | ConvertTo-Json -Compress
} finally { $ping.Dispose() }
"""
                cmd = ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script]
            else:
                timeout = timeout_ms if system == 'Darwin' else str(config.PING_TIMEOUT_SECONDS)
                cmd = ['ping', '-c', str(count), '-W', timeout, '--', host]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=count * (config.PING_TIMEOUT_SECONDS + 1) + 5,
                env={**os.environ, 'LC_ALL': 'C', 'HOME_NET_PING_HOST': host,
                     'HOME_NET_PING_COUNT': str(count), 'HOME_NET_PING_TIMEOUT_MS': timeout_ms}
            )
            
            if result.returncode == 0:
                if system == 'Windows':
                    stats = json.loads(result.stdout)
                    received = stats['received']
                    if not isinstance(received, int) or not 0 <= received <= count:
                        return _failed_ping()
                    if not received:
                        return _failed_ping()
                    return {'success': True, 'avg_ms': stats['avg_ms'],
                            'min_ms': stats['min_ms'], 'max_ms': stats['max_ms'],
                            'packet_loss_percent': (count - received) * 100.0 / count}
                return self._parse_ping_output(result.stdout)
            else:
                logger.warning(f"Ping failed for {host}: {result.stderr}")
                return _failed_ping()

        except subprocess.TimeoutExpired:
            logger.error(f"Ping timeout for {host}")
            return _failed_ping()
        except Exception as e:
            logger.error(f"Ping error for {host}: {e}", exc_info=True)
            return _failed_ping()
    
    def _parse_ping_output(self, output: str) -> Dict:
        """Parse ping command output to extract statistics."""
        try:
            # Look for packet loss percentage
            packet_loss_match = re.search(r'(\d+(?:\.\d+)?)% packet loss', output)
            if packet_loss_match is None:
                packet_loss_match = re.search(r'\((\d+(?:\.\d+)?)% loss\)', output)
            if packet_loss_match is None:
                return _failed_ping()
            packet_loss = float(packet_loss_match.group(1))
            if not 0 <= packet_loss <= 100:
                return _failed_ping()
            
            # Look for timing statistics: "min/avg/max[/stddev] = 1/2/3[/4] ms".
            # One regex covers both the Linux (rtt) and macOS/BSD (round-trip) headers.
            timing_match = re.search(r'= ([\d.]+)/([\d.]+)/([\d.]+)/', output)
            if timing_match:
                min_ms = float(timing_match.group(1))
                avg_ms = float(timing_match.group(2))
                max_ms = float(timing_match.group(3))
            else:
                min_ms = avg_ms = max_ms = None
            
            if timing_match is None:
                windows_timing = re.search(
                    r'Minimum = (\d+)ms, Maximum = (\d+)ms, Average = (\d+)ms', output)
                if windows_timing:
                    min_ms, max_ms, avg_ms = map(float, windows_timing.groups())
            success = packet_loss < 100.0 and avg_ms is not None
            
            return {
                'success': success,
                'avg_ms': avg_ms,
                'min_ms': min_ms,
                'max_ms': max_ms,
                'packet_loss_percent': packet_loss
            }
        
        except Exception as e:
            logger.error(f"Error parsing ping output: {e}", exc_info=True)
            return _failed_ping()
    
    def check_http(self, url: str) -> Dict:
        """Read only headers, with a hard deadline covering DNS and redirects."""
        failure = {'success': False, 'status_code': None, 'response_time_ms': None}
        context = multiprocessing.get_context('spawn')
        receive, send = context.Pipe(duplex=False)
        worker = context.Process(target=_http_worker, args=(url, send), daemon=True)
        started = False
        try:
            worker.start()
            started = True
            send.close()
            if receive.poll(config.HTTP_TIMEOUT_SECONDS):
                return receive.recv()
            logger.warning("HTTP deadline expired")
            return failure
        except (OSError, EOFError):
            logger.warning("HTTP worker failed")
            return failure
        finally:
            send.close()
            receive.close()
            if started:
                worker.join(timeout=0.1)
                if worker.is_alive():
                    worker.terminate()
                    worker.join(timeout=1)
                if worker.is_alive():
                    worker.kill()
                    worker.join()
                worker.close()

    def monitor_site(self, site_config: Dict) -> Dict:
        """Monitor a single site with optional HTTP and ping checks."""
        timestamp = config.utc_now()
        
        # Perform HTTP check only if URL is specified and HTTP is enabled
        url = site_config.get('url')
        enable_http = site_config.get('enable_http', True)
        
        if url and url.strip() and enable_http:
            http_result = self.check_http(url)
            http_enabled = True
        else:
            # Skip HTTP test - create a "not tested" result
            http_result = {
                'success': None,  # None means not tested
                'status_code': None,
                'response_time_ms': None
            }
            http_enabled = False
        
        # Perform ping check only if ping_host is specified and ping is enabled
        ping_host = site_config.get('ping_host')
        enable_ping = site_config.get('enable_ping', True)
        
        if ping_host and ping_host.strip() and enable_ping:
            ping_result = self.ping_host(ping_host)
            ping_enabled = True
        else:
            # Skip ping test - create a "not tested" result
            ping_result = {
                'success': None,  # None means not tested
                'avg_ms': None,
                'min_ms': None,
                'max_ms': None,
                'packet_loss_percent': None
            }
            ping_enabled = False
        
        # Validate that at least one test is enabled
        if not http_enabled and not ping_enabled:
            logger.error(f"Site {site_config['name']}: No tests enabled - must specify either 'url' or 'ping_host'")
            return _result_row(timestamp, site_config)
        
        # Determine overall success. At least one test is enabled here (the
        # neither-enabled case returned above), so `else` covers ping-only and
        # keeps overall_success always bound.
        if http_enabled and ping_enabled:
            # Both tests enabled - site is healthy if either works
            overall_success = http_result['success'] or ping_result['success']
        elif http_enabled:
            # Only HTTP test enabled
            overall_success = http_result['success']
        else:
            # Only ping test enabled
            overall_success = ping_result['success']
        
        result = {
            'timestamp': timestamp,
            'site_name': site_config['name'],
            'site_url': site_config.get('url'),
            'ping_host': site_config.get('ping_host'),
            'http_status_code': http_result['status_code'],
            'http_response_time_ms': http_result['response_time_ms'],
            'http_success': http_result['success'],
            'ping_avg_ms': ping_result['avg_ms'],
            'ping_min_ms': ping_result['min_ms'],
            'ping_max_ms': ping_result['max_ms'],
            'ping_packet_loss_percent': ping_result['packet_loss_percent'],
            'ping_success': ping_result['success'],
            'overall_success': overall_success
        }
        
        # Create log message
        if http_enabled:
            http_status = http_result['success']
        else:
            http_status = "skipped"
            
        if ping_enabled:
            ping_status = ping_result['success']
        else:
            ping_status = "skipped"
        
        logger.info(f"Monitored {site_config['name']}: HTTP={http_status}, Ping={ping_status}, Overall={overall_success}")
        
        return result
    
    def monitor_all_sites(self, site_configs: List[Dict]) -> list:
        """Monitor all configured sites."""
        results = []

        for site_config in site_configs:
            try:
                result = self.monitor_site(site_config)
                results.append(result)
            except Exception as e:
                logger.error(f"Error monitoring {site_config['name']}: {e}", exc_info=True)
                has_http = bool(site_config.get('url')) and site_config.get('enable_http', True)
                has_ping = bool(site_config.get('ping_host')) and site_config.get('enable_ping', True)
                results.append(_result_row(
                    config.utc_now(), site_config,
                    http_success=False if has_http else None,
                    ping_success=False if has_ping else None,
                    ping_packet_loss_percent=100.0 if has_ping else None,
                ))
        
        return results
