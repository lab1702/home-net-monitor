#!/usr/bin/env python3
"""Health check script for the monitoring service."""

import os
import sys
import duckdb
from datetime import datetime, timedelta

def main():
    """Check if the monitoring service is healthy."""
    try:
        # Check if database file exists
        db_path = os.getenv('DATABASE_PATH', '/data/network_monitor.db')
        if not os.path.exists(db_path):
            print("Database file does not exist")
            sys.exit(1)
        
        # Check if database is accessible and has recent data
        with duckdb.connect(db_path) as conn:
            # Check if table exists
            tables = conn.execute("SHOW TABLES").fetchall()
            table_names = [table[0] for table in tables]
            
            if 'monitoring_results' not in table_names:
                print("Monitoring results table does not exist")
                sys.exit(1)
            
            # Check for recent data (within last 5 minutes)
            five_minutes_ago = datetime.now() - timedelta(minutes=5)
            result = conn.execute("""
                SELECT COUNT(*) FROM monitoring_results 
                WHERE timestamp > ?
            """, (five_minutes_ago,)).fetchone()
            
            recent_count = result[0] if result else 0
            
            if recent_count > 0:
                print(f"Health check passed: {recent_count} recent records found")
                sys.exit(0)
            else:
                # For initial startup, just check if any data exists
                total_count = conn.execute("SELECT COUNT(*) FROM monitoring_results").fetchone()[0]
                if total_count > 0:
                    print(f"Health check passed: {total_count} total records found")
                    sys.exit(0)
                else:
                    print("No monitoring data found")
                    sys.exit(1)
                    
    except Exception as e:
        print(f"Health check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
