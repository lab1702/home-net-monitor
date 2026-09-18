"""Database operations for the network monitor."""

import logging
import os
from contextlib import contextmanager
from datetime import timedelta, timezone
import duckdb
import pandas as pd
from typing import List, Dict
import config
from validators import validate_config

logger = logging.getLogger(__name__)


@contextmanager
def database_connection(db_path):
    """Serialize application processes for the entire DuckDB connection lifetime."""
    db_path = os.path.realpath(db_path)
    with open(db_path + '.lock', 'a+b') as lock:
        if os.name == 'nt':
            import msvcrt
            if os.fstat(lock.fileno()).st_size == 0:
                lock.write(b'\0')
                lock.flush()
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            with duckdb.connect(db_path) as conn:
                yield conn
        finally:
            if os.name == 'nt':
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def monitoring_max_age_seconds(conn):
    """Allow two worst-case serial cycles before declaring observations stale."""
    http_count, ping_count = conn.execute("""
        SELECT COUNT(*) FILTER (WHERE enable_http),
               COUNT(*) FILTER (WHERE enable_ping)
        FROM monitoring_config WHERE enabled = true
    """).fetchone()
    http_budget = config.HTTP_TIMEOUT_SECONDS + 2  # Worker shutdown allowance.
    ping_budget = config.PING_COUNT * (config.PING_TIMEOUT_SECONDS + 1) + 5
    cycle_budget = http_count * http_budget + ping_count * ping_budget
    return max(config.STATUS_MAX_AGE_SECONDS, 2 * cycle_budget)


class DatabaseManager:
    """Manages database operations for network monitoring data."""
    
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the database with required tables."""
        with database_connection(self.db_path) as conn:
            conn.begin()
            config_exists = conn.execute("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_name = 'monitoring_config' AND table_schema = 'main'
            """).fetchone()[0] > 0
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
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS monitoring_heartbeat (
                    id INTEGER PRIMARY KEY, completed_at TIMESTAMP NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS monitoring_metadata (
                    key VARCHAR PRIMARY KEY, value VARCHAR NOT NULL
                )
            """)
            if conn.execute("SELECT value FROM monitoring_metadata WHERE key = 'time_basis'").fetchone() is None:
                # Legacy measurements used this host's local wall clock. Keep the
                # originals so ambiguous DST times or moved databases remain recoverable.
                conn.execute('ALTER TABLE monitoring_results ADD COLUMN IF NOT EXISTS legacy_timestamp TIMESTAMP')
                conn.execute('ALTER TABLE monitoring_heartbeat ADD COLUMN IF NOT EXISTS legacy_completed_at TIMESTAMP')
                conn.create_function(
                    '_legacy_local_to_utc',
                    lambda value: value.astimezone(timezone.utc).replace(tzinfo=None),
                    parameters=['TIMESTAMP'], return_type='TIMESTAMP')
                conn.execute('UPDATE monitoring_results SET legacy_timestamp = timestamp, timestamp = _legacy_local_to_utc(timestamp)')
                conn.execute('UPDATE monitoring_heartbeat SET legacy_completed_at = completed_at, completed_at = _legacy_local_to_utc(completed_at)')
                conn.remove_function('_legacy_local_to_utc')
                conn.execute("INSERT INTO monitoring_metadata VALUES ('time_basis', 'UTC')")
            # Empty existing stores are intentional; seed only at first creation.
            if not config_exists:
                self.initialize_default_configurations(conn)
            conn.commit()
    
    def insert_configuration(self, config: Dict):
        """Insert a new monitoring configuration into the database."""
        logger.info(f"Inserting configuration: {config.get('name')}")
        
        try:
            # Validate configuration using centralized validation
            validate_config(config)
            
            enable_http = config.get('enable_http', False)
            enable_ping = config.get('enable_ping', False)
            
            with database_connection(self.db_path) as conn:
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
        with database_connection(self.db_path) as conn:
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
                config.get('enable_http', False),
                config.get('enable_ping', False),
                config_id
            ))

    def delete_configuration(self, config_id: int):
        """Delete a monitoring configuration from the database."""
        with database_connection(self.db_path) as conn:
            conn.execute("""
                DELETE FROM monitoring_config WHERE id = ?
            """, (config_id,))

    def get_all_configurations(self) -> pd.DataFrame:
        """Retrieve all monitoring configurations from the database."""
        with database_connection(self.db_path) as conn:
            return conn.execute("SELECT * FROM monitoring_config ORDER BY name").df()

    def get_enabled_configurations(self) -> List[Dict]:
        """Retrieve only enabled monitoring configurations for the monitoring service."""
        with database_connection(self.db_path) as conn:
            # fetchall (not .df()) so NULL stays None rather than becoming nan,
            # which monitor_site treats as truthy and would .strip().
            cur = conn.execute("""
                SELECT name, url, ping_host, enabled, enable_http, enable_ping
                FROM monitoring_config WHERE enabled = true ORDER BY name
            """)
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def initialize_default_configurations(self, conn):
        """Seed a newly created store using the already locked connection."""
        for site in config.MONITOR_SITES:
            url = site.get('url') or None
            ping_host = site.get('ping_host') or None
            site_config = {
                'name': site['name'], 'url': url, 'ping_host': ping_host,
                'enable_http': bool(url and url.strip()),
                'enable_ping': bool(ping_host and ping_host.strip()),
            }
            validate_config(site_config)
            conn.execute("""
                INSERT INTO monitoring_config
                    (name, url, ping_host, enable_http, enable_ping)
                VALUES (?, ?, ?, ?, ?)
            """, (site['name'].strip(), url, ping_host,
                  site_config['enable_http'], site_config['enable_ping']))

    def record_heartbeat(self):
        """Record startup or persisted cycle progress, including empty cycles."""
        with database_connection(self.db_path) as conn:
            conn.execute("""
                INSERT INTO monitoring_heartbeat (id, completed_at) VALUES (1, ?)
                ON CONFLICT (id) DO UPDATE SET completed_at = excluded.completed_at
            """, (config.utc_now(),))

    def insert_monitoring_result(self, result: Dict):
        """Insert a monitoring result into the database."""
        with database_connection(self.db_path) as conn:
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
        with database_connection(self.db_path) as conn:
            return conn.execute("""
                SELECT * FROM monitoring_results
                WHERE timestamp > ? AND timestamp <= ?
                ORDER BY timestamp DESC
            """, (config.utc_now() - timedelta(hours=hours), config.utc_now())).df()
    
    def get_site_summary(self, hours: int = 24) -> pd.DataFrame:
        """Get summary statistics for each site."""
        with database_connection(self.db_path) as conn:
            return conn.execute("""
                SELECT
                    site_name,
                    COUNT(*) as total_checks,
                    SUM(CASE WHEN overall_success THEN 1 ELSE 0 END) as successful_checks,
                    AVG(CASE WHEN overall_success THEN 1.0 ELSE 0.0 END) * 100 as uptime_percent,
                    AVG(http_response_time_ms) as avg_http_response_time,
                    AVG(ping_avg_ms) as avg_ping_time,
                    AVG(ping_packet_loss_percent) as avg_packet_loss
                FROM monitoring_results
                WHERE timestamp > ? AND timestamp <= ?
                GROUP BY site_name
                ORDER BY uptime_percent DESC
            """, (config.utc_now() - timedelta(hours=hours), config.utc_now())).df()
    
    def get_current_status(self) -> pd.DataFrame:
        """Get the most recent status for each site."""
        with database_connection(self.db_path) as conn:
            query = """
                WITH ranked_results AS (
                    SELECT *, ROW_NUMBER() OVER (
                        PARTITION BY site_name ORDER BY id DESC
                    ) AS rn FROM monitoring_results
                )
                SELECT c.name AS site_name,
                       r.* EXCLUDE (site_name, overall_success),
                       CASE WHEN r.timestamp > ? AND r.timestamp <= ?
                            AND (r.http_success IS NOT NULL) = c.enable_http
                            AND (r.ping_success IS NOT NULL) = c.enable_ping
                            THEN r.overall_success
                            ELSE NULL END AS overall_success
                FROM monitoring_config c
                LEFT JOIN ranked_results r ON r.site_name = c.name AND r.rn = 1
                    AND r.site_url IS NOT DISTINCT FROM c.url
                    AND r.ping_host IS NOT DISTINCT FROM c.ping_host
                WHERE c.enabled = true
            """
            cutoff = config.utc_now() - timedelta(seconds=monitoring_max_age_seconds(conn))
            return conn.execute(query, (cutoff, config.utc_now())).df()

    def cleanup_old_data(self, days_to_keep: int = 30):
        """Remove data older than specified days."""
        with database_connection(self.db_path) as conn:
            conn.execute("""
                DELETE FROM monitoring_results
                WHERE timestamp < ?
            """, (config.utc_now() - timedelta(days=days_to_keep),))
