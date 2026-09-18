#!/usr/bin/env python3
"""Health check script for the monitoring service."""

import os
import sys
from datetime import datetime, timedelta

import config
from database import database_connection


def main():
    """Require a recently completed monitoring cycle, including empty cycles."""
    try:
        if not os.path.exists(config.DATABASE_PATH):
            print("Database file does not exist")
            return 1
        with database_connection(config.DATABASE_PATH) as conn:
            cutoff = datetime.now() - timedelta(seconds=config.STATUS_MAX_AGE_SECONDS)
            result = conn.execute(
                "SELECT COUNT(*) FROM monitoring_heartbeat WHERE completed_at > ?",
                (cutoff,),
            ).fetchone()
        if result and result[0] > 0:
            print("Health check passed: recent monitoring cycle")
            return 0
        print("No recent monitoring cycle")
        return 1
    except Exception as exc:
        print(f"Health check failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
