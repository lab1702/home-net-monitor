"""Logging configuration for the home network monitor."""

import logging

def get_logger(name: str) -> logging.Logger:
    """Get a namespaced logger instance."""
    return logging.getLogger(f"home_net_monitor.{name}")
