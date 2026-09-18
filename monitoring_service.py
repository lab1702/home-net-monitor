"""Background monitoring service that runs continuously."""

import logging
import time
from datetime import datetime
import signal
import sys

from monitor import NetworkMonitor
from database import DatabaseManager
import config

logger = logging.getLogger(__name__)


class MonitoringService:
    """Background service that monitors network connectivity."""
    
    def __init__(self):
        self.monitor = NetworkMonitor()
        self.db = DatabaseManager()
        self.running = True
        self.site_configs = []
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.running = False
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def run_monitoring_cycle(self):
        """Run a single monitoring cycle for all sites."""
        try:
            logger.info("Loading configurations...")
            self.site_configs = self.db.get_enabled_configurations()
            
            logger.info("Starting monitoring cycle...")
            stored_count = 0
            for site in self.site_configs:
                for result in self.monitor.monitor_all_sites([site]):
                    self.db.insert_monitoring_result(result)
                    stored_count += 1
                self.db.record_heartbeat()
            # A cycle with no enabled sites is still successful service progress.
            self.db.record_heartbeat()
            logger.info(f"Completed monitoring cycle, stored {stored_count} results")

        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}", exc_info=True)
    
    def cleanup_old_data(self):
        """Clean up old data from the database."""
        try:
            logger.info("Cleaning up old data...")
            self.db.cleanup_old_data(days_to_keep=30)
            logger.info("Data cleanup completed")
        except Exception as e:
            logger.error(f"Error during data cleanup: {e}", exc_info=True)
    
    def start(self):
        """Start the monitoring service."""
        logger.info("Starting network monitoring service...")
        
        # Load initial configurations to report count
        self.site_configs = self.db.get_enabled_configurations()
        self.db.record_heartbeat()
        logger.info(f"Monitoring {len(self.site_configs)} sites every {config.CHECK_INTERVAL_SECONDS} seconds")

        # ponytail: plain interval loop instead of the `schedule` dep. Cleanup
        # fires the first time we see hour>=2 on a new day (at startup if already
        # past 2am), which is close enough to a nightly job for a home monitor.
        last_check = 0.0
        last_cleanup_date = None
        while self.running:
            try:
                if time.monotonic() - last_check >= config.CHECK_INTERVAL_SECONDS:
                    last_check = time.monotonic()
                    self.run_monitoring_cycle()

                today = datetime.now().date()
                if datetime.now().hour >= 2 and last_cleanup_date != today:
                    last_cleanup_date = today
                    self.cleanup_old_data()

                time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
                time.sleep(5)  # Wait before retrying
        
        logger.info("Monitoring service stopped")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    MonitoringService().start()
