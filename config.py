"""Configuration settings for the home network monitor."""

import os
from typing import List, Dict

# Database configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "network_monitor.db")

# Sites to monitor
# Each site needs:
#   - name: Display name for the dashboard (required)
#   - url: HTTPS URL for HTTP connectivity tests (optional)
#   - ping_host: Hostname or IP address for ping tests (optional)
#
# At least one of 'url' or 'ping_host' must be specified
#
# Configuration options:
#   - Both url and ping_host: Full monitoring (HTTP + ping)
#   - Only url: HTTP-only monitoring (for sites that block ping)
#   - Only ping_host: Ping-only monitoring (for servers without web interface)
#
# The system considers a site healthy if ANY enabled test passes

MONITOR_SITES = [
    {
        "name": "Google",
        "url": "https://www.google.com",
        "ping_host": "8.8.8.8"  # Google's public DNS - reliable for ping
    },
    {
        "name": "GitHub",
        "url": "https://github.com",
        "ping_host": "github.com"
    },
    {
        "name": "Cloudflare",
        "url": "https://www.cloudflare.com",
        "ping_host": "1.1.1.1"  # Cloudflare's public DNS - reliable for ping
    },
    {
        "name": "Amazon",
        "url": "https://www.amazon.com",
        "ping_host": "amazon.com"
    },
    {
        "name": "Microsoft",
        "url": "https://www.microsoft.com",
        "ping_host": None  # Skip ping test - Microsoft blocks ICMP
    },
    {
        "name": "Netflix",
        "url": "https://www.netflix.com",
        "ping_host": None  # Skip ping test - Netflix blocks ICMP
    },
    {
        "name": "Google DNS Secondary",
        "ping_host": "8.8.4.4"  # Ping-only: DNS server has no web interface
        # No 'url' field - only ping monitoring
    }
    # To add more sites, uncomment and modify the examples below:
    # {
    #     "name": "Local Router",
    #     "url": "http://192.168.1.1",  # Adjust to your router's IP
    #     "ping_host": "192.168.1.1"
    # },
    # {
    #     "name": "OpenDNS",
    #     "url": "https://www.opendns.com",
    #     "ping_host": "208.67.222.222"  # OpenDNS server
    # },
    # {
    #     "name": "Your Website",
    #     "url": "https://yoursite.com",
    #     "ping_host": "yoursite.com"
    # },
    # {
    #     "name": "Mail Server",
    #     "ping_host": "mail.example.com"  # Ping-only: no web interface
    # }
]

# Monitoring configuration
CHECK_INTERVAL_SECONDS = 60  # Check sites once per minute
HTTP_TIMEOUT_SECONDS = 10
PING_TIMEOUT_SECONDS = 5
PING_COUNT = 3

# Streamlit configuration
STREAMLIT_PAGE_TITLE = "Home Network Monitor"
STREAMLIT_PAGE_ICON = "📡"
STREAMLIT_LAYOUT = "wide"
