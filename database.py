"""Database operations for the network monitor."""

import duckdb
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import contextmanager
import config
from validators import validate_config
from logging_config import get_logger

logger = get_logger('database')


class DatabaseManager:
    """Manages database operations for network monitoring data."""
    
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            conn = duckdb.connect(self.db_path)
            yield conn
        finally:
            if conn:
                conn.close()
    
    def init_database(self):
        """Initialize the database with required tables."""
        with self.get_connection() as conn:
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
            
            # Create sequence for monitoring config IDs
            conn.execute("""
                CREATE SEQUENCE IF NOT EXISTS monitoring_config_id_seq
            """)
            
            # Create monitoring configuration table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS monitoring_config (
                    id INTEGER PRIMARY KEY DEFAULT nextval('monitoring_config_id_seq'),
                    name VARCHAR(100) NOT NULL UNIQUE,
                    url VARCHAR(500),
                    ping_host VARCHAR(100),
                    enabled BOOLEAN DEFAULT true,
                    enable_http BOOLEAN DEFAULT true,
                    enable_ping BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT now(),
                    updated_at TIMESTAMP DEFAULT now()
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
            
            # Initialize default configurations if none exist
            self.initialize_default_configurations()
    
    def insert_configuration(self, config: Dict):
        """Insert a new monitoring configuration into the database."""
        logger.info(f"Inserting configuration: {config.get('name')}")
        
        try:
            # Validate configuration using centralized validation
            validate_config(config)
            
            enable_http = config.get('enable_http', True)
            enable_ping = config.get('enable_ping', True)
            
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO monitoring_config (
                        name, url, ping_host, enabled, enable_http, enable_ping
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    config['name'].strip(),
                    config.get('url'),
                    config.get('ping_host'),
                    config.get('enabled', True),
                    enable_http,
                    enable_ping
                ))
            
            logger.info(f"Successfully inserted configuration: {config.get('name')}")
            
        except Exception as e:
            logger.error(f"Failed to insert configuration {config.get('name')}: {e}", exc_info=True)
            raise

    def update_configuration(self, config_id: int, config: Dict):
        """Update an existing monitoring configuration."""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE monitoring_config SET
                name = ?, url = ?, ping_host = ?, enabled = ?,
                enable_http = ?, enable_ping = ?, updated_at = NOW()
                WHERE id = ?
            """, (
                config['name'],
                config.get('url'),
                config.get('ping_host'),
                config.get('enabled', True),
                config.get('enable_http', True),
                config.get('enable_ping', True),
                config_id
            ))

    def delete_configuration(self, config_id: int):
        """Delete a monitoring configuration from the database."""
        with self.get_connection() as conn:
            conn.execute("""
                DELETE FROM monitoring_config WHERE id = ?
            """, (config_id,))

    def get_all_configurations(self) -> pd.DataFrame:
        """Retrieve all monitoring configurations from the database."""
        with duckdb.connect(self.db_path) as conn:
            return conn.execute("SELECT * FROM monitoring_config ORDER BY name").df()

    def get_enabled_configurations(self) -> List[Dict]:
        """Retrieve only enabled monitoring configurations for the monitoring service."""
        with self.get_connection() as conn:
            results = conn.execute("""
                SELECT * FROM monitoring_config 
                WHERE enabled = true 
                ORDER BY name
            """).fetchall()
            
            # Convert to list of dictionaries for compatibility with existing code
            configs = []
            for row in results:
                config = {
                    'name': row[1],  # name column
                    'url': row[2] if row[2] else None,  # url column
                    'ping_host': row[3] if row[3] else None,  # ping_host column
                    'enabled': row[4],  # enabled column
                    'enable_http': row[5],  # enable_http column
                    'enable_ping': row[6]   # enable_ping column
                }
                configs.append(config)
            
            return configs

    def initialize_default_configurations(self):
        """Initialize default monitoring configurations if none exist."""
        with self.get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM monitoring_config").fetchone()[0]
            
            if count == 0:
                # Import default configurations from config.py
                import config
                
                for site_config in config.MONITOR_SITES:
                    # Determine HTTP and ping settings based on provided fields
                    has_url = site_config.get('url') is not None and site_config.get('url').strip() != ''
                    has_ping = site_config.get('ping_host') is not None and site_config.get('ping_host').strip() != ''
                    
                    default_config = {
                        'name': site_config['name'],
                        'url': site_config.get('url'),
                        'ping_host': site_config.get('ping_host'),
                        'enabled': True,
                        'enable_http': has_url,
                        'enable_ping': has_ping
                    }
                    
                    self.insert_configuration(default_config)

    def insert_monitoring_result(self, result: Dict):
        """Insert a monitoring result into the database."""
        with self.get_connection() as conn:
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
        # Validate input to prevent SQL injection
        if not isinstance(hours, int) or hours < 0 or hours > 8760:  # Max 1 year
            raise ValueError("Hours must be a positive integer less than 8760")
        
        with self.get_connection() as conn:
            query = """
                SELECT * FROM monitoring_results 
                WHERE timestamp > NOW() - INTERVAL '{} hours'
                ORDER BY timestamp DESC
            """.format(hours)
            return conn.execute(query).df()
    
    def get_site_summary(self, hours: int = 24) -> pd.DataFrame:
        """Get summary statistics for each site."""
        # Validate input to prevent SQL injection
        if not isinstance(hours, int) or hours < 0 or hours > 8760:  # Max 1 year
            raise ValueError("Hours must be a positive integer less than 8760")
        
        with self.get_connection() as conn:
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
        with self.get_connection() as conn:
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
        # Validate input to prevent SQL injection
        if not isinstance(hours, int) or hours < 0 or hours > 8760:  # Max 1 year
            raise ValueError("Hours must be a positive integer less than 8760")
        
        with self.get_connection() as conn:
            query = """
                SELECT * FROM monitoring_results 
                WHERE site_name = ? AND timestamp > NOW() - INTERVAL '{} hours'
                ORDER BY timestamp ASC
            """.format(hours)
            return conn.execute(query, (site_name,)).df()
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Remove data older than specified days."""
        # Validate input to prevent SQL injection
        if not isinstance(days_to_keep, int) or days_to_keep < 1 or days_to_keep > 3650:  # Max 10 years
            raise ValueError("Days to keep must be a positive integer less than 3650")
        
        with self.get_connection() as conn:
            conn.execute("""
                DELETE FROM monitoring_results 
                WHERE timestamp < NOW() - INTERVAL '{} days'
            """.format(days_to_keep))
