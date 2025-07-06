"""Database operations for the network monitor."""

import duckdb
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
import config


class DatabaseManager:
    """Manages database operations for network monitoring data."""
    
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        with duckdb.connect(self.db_path) as conn:
            # Create sequence for auto-incrementing IDs
            conn.execute("""
                CREATE SEQUENCE IF NOT EXISTS monitoring_results_id_seq
            """)
            
            # Create monitoring results table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS monitoring_results (
                    id INTEGER PRIMARY KEY DEFAULT nextval('monitoring_results_id_seq'),
                    timestamp TIMESTAMP,
                    site_name VARCHAR(100),
                    site_url VARCHAR(500),
                    ping_host VARCHAR(100),
                    http_status_code INTEGER,
                    http_response_time_ms FLOAT,
                    http_success BOOLEAN,
                    ping_avg_ms FLOAT,
                    ping_min_ms FLOAT,
                    ping_max_ms FLOAT,
                    ping_packet_loss_percent FLOAT,
                    ping_success BOOLEAN,
                    overall_success BOOLEAN
                )
            """)
            
            # Create index for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_monitoring_timestamp 
                ON monitoring_results(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_monitoring_site 
                ON monitoring_results(site_name)
            """)
    
    def insert_monitoring_result(self, result: Dict):
        """Insert a monitoring result into the database."""
        with duckdb.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO monitoring_results (
                    timestamp, site_name, site_url, ping_host,
                    http_status_code, http_response_time_ms, http_success,
                    ping_avg_ms, ping_min_ms, ping_max_ms, 
                    ping_packet_loss_percent, ping_success, overall_success
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result['timestamp'],
                result['site_name'],
                result['site_url'],
                result['ping_host'],
                result['http_status_code'],
                result['http_response_time_ms'],
                result['http_success'],
                result['ping_avg_ms'],
                result['ping_min_ms'],
                result['ping_max_ms'],
                result['ping_packet_loss_percent'],
                result['ping_success'],
                result['overall_success']
            ))
    
    def get_recent_results(self, hours: int = 24) -> pd.DataFrame:
        """Get monitoring results from the last N hours."""
        with duckdb.connect(self.db_path) as conn:
            query = """
                SELECT * FROM monitoring_results 
                WHERE timestamp > NOW() - INTERVAL '{} hours'
                ORDER BY timestamp DESC
            """.format(hours)
            return conn.execute(query).df()
    
    def get_site_summary(self, hours: int = 24) -> pd.DataFrame:
        """Get summary statistics for each site."""
        with duckdb.connect(self.db_path) as conn:
            query = """
                SELECT 
                    site_name,
                    COUNT(*) as total_checks,
                    SUM(CASE WHEN overall_success THEN 1 ELSE 0 END) as successful_checks,
                    AVG(CASE WHEN overall_success THEN 1.0 ELSE 0.0 END) * 100 as uptime_percent,
                    AVG(http_response_time_ms) as avg_http_response_time,
                    AVG(ping_avg_ms) as avg_ping_time,
                    AVG(ping_packet_loss_percent) as avg_packet_loss
                FROM monitoring_results 
                WHERE timestamp > NOW() - INTERVAL '{} hours'
                GROUP BY site_name
                ORDER BY uptime_percent DESC
            """.format(hours)
            return conn.execute(query).df()
    
    def get_current_status(self) -> pd.DataFrame:
        """Get the most recent status for each site."""
        with duckdb.connect(self.db_path) as conn:
            query = """
                WITH ranked_results AS (
                    SELECT *,
                           ROW_NUMBER() OVER (PARTITION BY site_name ORDER BY timestamp DESC) as rn
                    FROM monitoring_results
                )
                SELECT * FROM ranked_results WHERE rn = 1
            """
            return conn.execute(query).df()
    
    def get_historical_data(self, site_name: str, hours: int = 24) -> pd.DataFrame:
        """Get historical data for a specific site."""
        with duckdb.connect(self.db_path) as conn:
            query = """
                SELECT * FROM monitoring_results 
                WHERE site_name = ? AND timestamp > NOW() - INTERVAL '{} hours'
                ORDER BY timestamp ASC
            """.format(hours)
            return conn.execute(query, (site_name,)).df()
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Remove data older than specified days."""
        with duckdb.connect(self.db_path) as conn:
            conn.execute("""
                DELETE FROM monitoring_results 
                WHERE timestamp < NOW() - INTERVAL '{} days'
            """.format(days_to_keep))
