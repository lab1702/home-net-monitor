"""Network monitoring functionality."""

import subprocess
import time
import requests
import re
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NetworkMonitor:
    """Performs network monitoring checks."""
    
    def __init__(self):
        self.session = requests.Session()
        # Set a reasonable user agent
        self.session.headers.update({
            'User-Agent': 'NetworkMonitor/1.0 (+https://github.com/home-net-monitor)'
        })
    
    def ping_host(self, host: str, count: int = config.PING_COUNT) -> Dict:
        """Ping a host and return statistics."""
        try:
            # Build ping command based on the operating system
            cmd = ['ping', '-c', str(count), '-W', str(config.PING_TIMEOUT_SECONDS), host]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=config.PING_TIMEOUT_SECONDS + 5
            )
            
            if result.returncode == 0:
                return self._parse_ping_output(result.stdout)
            else:
                logger.warning(f"Ping failed for {host}: {result.stderr}")
                return {
                    'success': False,
                    'avg_ms': None,
                    'min_ms': None,
                    'max_ms': None,
                    'packet_loss_percent': 100.0
                }
        
        except subprocess.TimeoutExpired:
            logger.error(f"Ping timeout for {host}")
            return {
                'success': False,
                'avg_ms': None,
                'min_ms': None,
                'max_ms': None,
                'packet_loss_percent': 100.0
            }
        except Exception as e:
            logger.error(f"Ping error for {host}: {e}")
            return {
                'success': False,
                'avg_ms': None,
                'min_ms': None,
                'max_ms': None,
                'packet_loss_percent': 100.0
            }
    
    def _parse_ping_output(self, output: str) -> Dict:
        """Parse ping command output to extract statistics."""
        try:
            # Look for packet loss percentage
            packet_loss_match = re.search(r'(\d+)% packet loss', output)
            packet_loss = float(packet_loss_match.group(1)) if packet_loss_match else 0.0
            
            # Look for timing statistics (min/avg/max)
            timing_match = re.search(r'min/avg/max/stddev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+) ms', output)
            if timing_match:
                min_ms = float(timing_match.group(1))
                avg_ms = float(timing_match.group(2))
                max_ms = float(timing_match.group(3))
            else:
                # Try alternative format
                timing_match = re.search(r'= ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+) ms', output)
                if timing_match:
                    min_ms = float(timing_match.group(1))
                    avg_ms = float(timing_match.group(2))
                    max_ms = float(timing_match.group(3))
                else:
                    min_ms = avg_ms = max_ms = None
            
            success = packet_loss < 100.0
            
            return {
                'success': success,
                'avg_ms': avg_ms,
                'min_ms': min_ms,
                'max_ms': max_ms,
                'packet_loss_percent': packet_loss
            }
        
        except Exception as e:
            logger.error(f"Error parsing ping output: {e}")
            return {
                'success': False,
                'avg_ms': None,
                'min_ms': None,
                'max_ms': None,
                'packet_loss_percent': 100.0
            }
    
    def check_http(self, url: str) -> Dict:
        """Check HTTP response for a URL."""
        try:
            start_time = time.time()
            response = self.session.get(
                url,
                timeout=config.HTTP_TIMEOUT_SECONDS,
                allow_redirects=True
            )
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'response_time_ms': response_time_ms
            }
        
        except requests.exceptions.Timeout:
            logger.warning(f"HTTP timeout for {url}")
            return {
                'success': False,
                'status_code': None,
                'response_time_ms': None
            }
        except requests.exceptions.ConnectionError:
            logger.warning(f"HTTP connection error for {url}")
            return {
                'success': False,
                'status_code': None,
                'response_time_ms': None
            }
        except Exception as e:
            logger.error(f"HTTP error for {url}: {e}")
            return {
                'success': False,
                'status_code': None,
                'response_time_ms': None
            }
    
    def monitor_site(self, site_config: Dict) -> Dict:
        """Monitor a single site with optional HTTP and ping checks."""
        timestamp = datetime.now()
        
        # Perform HTTP check only if URL is specified
        url = site_config.get('url')
        if url and url.strip():  # Skip if None, False, or empty string
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
        
        # Perform ping check only if ping_host is specified
        ping_host = site_config.get('ping_host')
        if ping_host and ping_host.strip():  # Skip if None, False, or empty string
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
            # Return a failed result
            return {
                'timestamp': timestamp,
                'site_name': site_config['name'],
                'site_url': site_config.get('url'),
                'ping_host': site_config.get('ping_host'),
                'http_status_code': None,
                'http_response_time_ms': None,
                'http_success': None,
                'ping_avg_ms': None,
                'ping_min_ms': None,
                'ping_max_ms': None,
                'ping_packet_loss_percent': None,
                'ping_success': None,
                'overall_success': False
            }
        
        # Determine overall success
        if http_enabled and ping_enabled:
            # Both tests enabled - site is healthy if either works
            overall_success = http_result['success'] or ping_result['success']
        elif http_enabled:
            # Only HTTP test enabled
            overall_success = http_result['success']
        elif ping_enabled:
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
    
    def monitor_all_sites(self) -> list:
        """Monitor all configured sites."""
        results = []
        
        for site_config in config.MONITOR_SITES:
            try:
                result = self.monitor_site(site_config)
                results.append(result)
            except Exception as e:
                logger.error(f"Error monitoring {site_config['name']}: {e}")
                # Create a failed result
                failed_result = {
                    'timestamp': datetime.now(),
                    'site_name': site_config['name'],
                    'site_url': site_config['url'],
                    'ping_host': site_config.get('ping_host'),
                    'http_status_code': None,
                    'http_response_time_ms': None,
                    'http_success': False,
                    'ping_avg_ms': None,
                    'ping_min_ms': None,
                    'ping_max_ms': None,
                    'ping_packet_loss_percent': 100.0 if site_config.get('ping_host') else None,
                    'ping_success': False if site_config.get('ping_host') else None,
                    'overall_success': False
                }
                results.append(failed_result)
        
        return results
