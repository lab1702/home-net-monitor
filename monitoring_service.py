"""Background monitoring service that runs continuously."""

import time
import schedule
from datetime import datetime
from threading import Thread
import signal
import sys

from monitor import NetworkMonitor
from database import DatabaseManager
import config
from logging_config import get_logger

# Configure logging
logger = get_logger('monitoring_service')


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
            results = self.monitor.monitor_all_sites(self.site_configs)
            
            # Store results in database
            for result in results:
                self.db.insert_monitoring_result(result)
            
            logger.info(f"Completed monitoring cycle, stored {len(results)} results")
            
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
        logger.info(f"Monitoring {len(self.site_configs)} sites every {config.CHECK_INTERVAL_SECONDS} seconds")
        
        # Schedule monitoring checks
        schedule.every(config.CHECK_INTERVAL_SECONDS).seconds.do(self.run_monitoring_cycle)
        
        # Schedule daily cleanup
        schedule.every().day.at("02:00").do(self.cleanup_old_data)
        
        # Run initial monitoring cycle
        self.run_monitoring_cycle()
        
        # Main monitoring loop
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
                time.sleep(5)  # Wait before retrying
        
        logger.info("Monitoring service stopped")
    
    def run_once(self):
        """Run monitoring once and exit (useful for testing)."""
        logger.info("Running single monitoring cycle...")
        self.run_monitoring_cycle()
        logger.info("Single monitoring cycle completed")


def main():
    """Main entry point for the monitoring service."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Network Monitoring Service')
    parser.add_argument('--once', action='store_true', 
                       help='Run monitoring once and exit')
    parser.add_argument('--cleanup', action='store_true',
                       help='Run data cleanup and exit')
    
    args = parser.parse_args()
    
    service = MonitoringService()
    
    if args.cleanup:
        service.cleanup_old_data()
    elif args.once:
        service.run_once()
    else:
        service.start()


if __name__ == "__main__":
    main()
