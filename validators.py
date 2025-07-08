"""Validation utility functions for the home network monitor."""

from typing import Dict

def validate_config(config: Dict):
    """
    Validates a monitoring configuration.
    Raises ValueError if validation fails.
    """
    name = config.get('name')
    url = config.get('url')
    ping_host = config.get('ping_host')
    enable_http = config.get('enable_http', False)
    enable_ping = config.get('enable_ping', False)

    if not name or not name.strip():
        raise ValueError("Site name is required.")

    if not enable_http and not enable_ping:
        raise ValueError("At least one test type (HTTP or Ping) must be enabled.")

    if enable_http and (not url or not url.strip()):
        raise ValueError("URL is required when HTTP test is enabled.")

    if enable_ping and (not ping_host or not ping_host.strip()):
        raise ValueError("Ping Host is required when Ping test is enabled.")

