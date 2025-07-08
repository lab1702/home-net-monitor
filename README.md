# Home Network Monitor 📡

A simple yet powerful network monitoring tool that tracks your internet connection performance by monitoring ping latency, packet loss, and HTTP response times for popular websites.

## Features

- 🔍 **Real-time Monitoring**: Checks sites every minute
- 📊 **Interactive Dashboard**: Beautiful Streamlit-based web interface
- 📈 **Historical Data**: Track performance over time with charts
- 🗄️ **Efficient Storage**: Uses DuckDB for fast, lightweight data storage
- 🐳 **Docker Support**: Easy deployment with Docker and Docker Compose
- 🌐 **Cross-Platform**: Runs on Windows, macOS, and Linux
- ⚡ **Auto-refresh**: Dashboard updates automatically every 30 seconds

## Sites Monitored

By default, the following sites are monitored:
- Google (8.8.8.8) - Full monitoring (HTTP + Ping)
- GitHub - Full monitoring (HTTP + Ping)
- Cloudflare (1.1.1.1) - Full monitoring (HTTP + Ping)
- Amazon - Full monitoring (HTTP + Ping)
- Microsoft - HTTP only (ping blocked)
- Netflix - HTTP only (ping blocked)
- Google DNS Secondary (8.8.4.4) - Ping only

**Note:** Sites are now managed through the database via the Configuration Management interface in the dashboard.

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone or download the project
git clone <repository> home-net-monitor
cd home-net-monitor

# Start the services
docker-compose up -d

# View the dashboard
open http://localhost:8501
```

### Option 2: Local Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Start the monitoring service (in background)
python monitoring_service.py &

# Start the dashboard
streamlit run dashboard.py
```

### Option 3: Manual Testing

```bash
# Run a single monitoring cycle
python monitoring_service.py --once

# View the dashboard
streamlit run dashboard.py
```

## Dashboard Features

### Current Status
- Overall uptime percentage
- Real-time status of each monitored site
- Latest response times and packet loss

### Historical Data
- Customizable time ranges (1 hour to 30 days)
- Site availability charts
- HTTP response time trends
- Ping latency trends
- Packet loss visualization

### Configuration Management
- Add, edit, and delete monitoring sites
- Enable/disable individual sites
- Configure HTTP and/or ping testing per site
- Real-time validation of configurations
- User-friendly interface for managing monitoring targets

### Settings
- Auto-refresh toggle (30-second intervals)
- Manual refresh button
- Time range selector

## Configuration

**Database-Driven Configuration**: Sites are managed through the database using the Configuration Management interface. This facilitates real-time configuration without restarting the service.

**Default Sites**: The system initializes with default configurations from `config.py`, but these can be modified through the web interface.

For detailed configuration options including monitoring types (HTTP-only, ping-only, full monitoring) and site examples, see [SITE_CONFIGURATION.md](SITE_CONFIGURATION.md).

For complete setup instructions, see [SETUP.md](SETUP.md).

For dashboard usage and symbols, see [DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md).

## Architecture

- **Backend**: Python with DuckDB database and robust error handling
- **Frontend**: Streamlit web application with real-time configuration management
- **Monitoring**: Separate service that runs ping and HTTP checks with comprehensive logging
- **Data**: Stored in a lightweight DuckDB database file with proper connection management
- **Validation**: Centralized input validation for security and data integrity
- **Logging**: Structured logging with configurable levels and formats

## Architecture Diagram

To better understand the architecture, refer to this simplified diagram: (ASCII art or reference to an external diagram file)

[Architecture Diagram]

## File Structure

```
home-net-monitor/
├── config.py              # Configuration settings
├── database.py             # Database operations with context manager
├── monitor.py              # Network monitoring logic
├── monitoring_service.py   # Background monitoring service
├── dashboard.py            # Streamlit dashboard
├── config_management.py    # Configuration management UI
├── validators.py           # Centralized input validation utilities
├── logging_config.py       # Centralized logging configuration
├── tests.py               # Unit tests
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker container definition
├── docker-compose.yml     # Multi-container setup
├── CHANGELOG.md           # Change log
└── README.md              # This file
```

## Commands

### Monitoring Service

```bash
# Run continuous monitoring
python monitoring_service.py

# Run single check and exit
python monitoring_service.py --once

# Clean up old data
python monitoring_service.py --cleanup
```

### Dashboard

```bash
# Start dashboard (default port 8501)
streamlit run dashboard.py

# Start on custom port
streamlit run dashboard.py --server.port 8080
```

### Docker

```bash
# Build image
docker build -t home-net-monitor .

# Run monitoring service
docker run -v $(pwd)/data:/data home-net-monitor python monitoring_service.py

# Run dashboard
docker run -p 8501:8501 -v $(pwd)/data:/data home-net-monitor
```

## Data Storage

The application stores data in a DuckDB database with the following schema:

- **monitoring_results**: Main table storing all monitoring data
  - Site information (name, URL, ping host)
  - HTTP metrics (status code, response time)
  - Ping metrics (latency, packet loss)
  - Timestamps and success flags

Data is automatically cleaned up after 30 days to prevent unlimited growth.

## Environment Variables

Here are some important environment variables that can be configured:
- `DATABASE_PATH`: Path to the DuckDB database file (default: `network_monitor.db`)
- `CHECK_INTERVAL_SECONDS`: Interval for running monitoring checks (default: `60` seconds)

## Security Considerations

- **Input Validation**: All user inputs are validated through centralized validation functions
- **SQL Injection Protection**: Database queries use proper parameterization and input validation
- **Connection Management**: Database connections are managed through context managers for safety
- **Logging Security**: Sensitive information is not logged in plain text
- **Dependency Updates**: Regularly review and update dependency versions for security patches

## Change Log

All changes, including features, bug fixes, and enhancements, should be documented here for better version control.

## Troubleshooting

### No Data in Dashboard
1. Ensure the monitoring service is running
2. Check that the database file is accessible
3. Verify network connectivity

### Docker Issues
1. Ensure Docker and Docker Compose are installed
2. Check port 8501 is not already in use
3. Verify the `./data` directory is created

### Permission Issues
1. Ensure ping command is available (requires root on some systems)
2. Check file permissions for database directory
3. Verify network access to monitored sites

## Development

To extend the application:

1. **Add new sites**: Modify `MONITOR_SITES` in `config.py`
2. **Custom metrics**: Extend the monitoring logic in `monitor.py`
3. **Dashboard features**: Add new charts or views in `dashboard.py`
4. **Database queries**: Add new methods to `database.py`

## Requirements

- Python 3.13+ (or use Docker)
- Network access to monitored sites
- Ping command available
- 50MB+ free disk space for database

## License

This project is provided as-is for educational and personal use.
