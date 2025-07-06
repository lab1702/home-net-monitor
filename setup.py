#!/usr/bin/env python3
"""Setup and utility script for Home Network Monitor."""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def check_requirements():
    """Check if all requirements are available."""
    print("Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    else:
        print(f"✅ Python {sys.version.split()[0]}")
    
    # Check ping command
    try:
        subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                      capture_output=True, timeout=5)
        print("✅ Ping command available")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Ping command not available or not working")
        return False
    
    return True


def install_dependencies():
    """Install Python dependencies."""
    print("Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False


def setup_database():
    """Initialize the database."""
    print("Setting up database...")
    try:
        from database import DatabaseManager
        db = DatabaseManager()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False


def test_monitoring():
    """Run a test monitoring cycle."""
    print("Running test monitoring cycle...")
    try:
        from monitoring_service import MonitoringService
        service = MonitoringService()
        service.run_once()
        print("✅ Test monitoring completed successfully")
        return True
    except Exception as e:
        print(f"❌ Test monitoring failed: {e}")
        return False


def start_services():
    """Start both monitoring and dashboard services."""
    print("Starting services...")
    
    # Start monitoring service in background
    print("Starting monitoring service...")
    monitor_process = subprocess.Popen([
        sys.executable, 'monitoring_service.py'
    ])
    
    # Start dashboard
    print("Starting dashboard...")
    print("Dashboard will be available at: http://localhost:8501")
    try:
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 'dashboard.py'
        ])
    except KeyboardInterrupt:
        print("\nShutting down services...")
        monitor_process.terminate()
        monitor_process.wait()


def create_data_directory():
    """Create data directory for database."""
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    print(f"✅ Data directory created: {data_dir.absolute()}")


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description='Home Network Monitor Setup')
    parser.add_argument('command', choices=[
        'check', 'install', 'setup', 'test', 'start', 'all'
    ], help='Command to run')
    
    args = parser.parse_args()
    
    if args.command == 'check':
        success = check_requirements()
        sys.exit(0 if success else 1)
    
    elif args.command == 'install':
        success = install_dependencies()
        sys.exit(0 if success else 1)
    
    elif args.command == 'setup':
        create_data_directory()
        success = setup_database()
        sys.exit(0 if success else 1)
    
    elif args.command == 'test':
        success = test_monitoring()
        sys.exit(0 if success else 1)
    
    elif args.command == 'start':
        start_services()
    
    elif args.command == 'all':
        print("🚀 Setting up Home Network Monitor...")
        
        steps = [
            ("Checking requirements", check_requirements),
            ("Installing dependencies", install_dependencies),
            ("Creating data directory", lambda: create_data_directory() or True),
            ("Setting up database", setup_database),
            ("Testing monitoring", test_monitoring),
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            if not step_func():
                print(f"❌ Setup failed at: {step_name}")
                sys.exit(1)
        
        print("\n🎉 Setup completed successfully!")
        print("\nTo start the services:")
        print("  python setup.py start")
        print("\nOr manually:")
        print("  python monitoring_service.py &")
        print("  streamlit run dashboard.py")


if __name__ == "__main__":
    main()
