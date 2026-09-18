# Change Log

All notable changes to the Home Network Monitor project will be documented in this file.

## [Unreleased]

### Added
- **Database-Driven Configuration**: Sites are now managed through the database using the Configuration Management interface in the dashboard
- **Real-time Configuration Changes**: Configuration changes take effect immediately without requiring service restarts
- **Configuration Management Interface**: Added a web-based interface for managing monitoring targets
- **Enhanced Navigation**: Improved sidebar navigation with visual indicators for active pages
- **Input Validation**: Added comprehensive input validation for configuration entries
- **Site Status Metrics**: Added configuration status metrics in the sidebar
- **SQL Injection Protection**: Fixed SQL injection vulnerabilities in database queries
- **Centralized Validation**: Created `validators.py` module for consistent validation logic
- **Logging Configuration**: Added `logging_config.py` for standardized logging setup
- **Database Context Manager**: Implemented proper connection management with context managers
- **Enhanced Error Handling**: Added comprehensive error handling with detailed logging
- **DuckDB Compatibility**: Fixed SQL syntax issues specific to DuckDB interval queries

### Changed
- **Amazon Default Ping Target**: Changed Amazon's default ping host from `amazon.com` to `www.amazon.com`
- **Navigation UI**: Moved navigation buttons to the sidebar for better organization
- **Configuration Storage**: Migrated from static config.py to database-driven configuration
- **Monitoring Service**: Updated to load configurations from database in real-time
- **Button Highlighting**: Fixed navigation button highlighting to update immediately
- **Database Operations**: All database operations now use context managers for safe connection handling
- **Logging Implementation**: Standardized logging across all modules using centralized configuration
- **Query Parameterization**: Replaced string formatting with proper DuckDB-compatible queries

### Fixed
- Bind documented local Streamlit launches to localhost to keep unauthenticated configuration controls off the LAN by default.
- Configure INFO-level service logging so startup, successful checks, and cleanup progress are visible in local and Docker logs.
- Align omitted HTTP/ping flags in database writes with validation so single-probe API configurations can report current status.
- Use UTC for measurements, health heartbeats, and query cutoffs; preserve and migrate legacy local timestamps, and order current observations by insertion sequence across clock rollbacks.
- Use structured .NET ping results on Windows instead of localized command-output labels.
- Scale stale-data and health deadlines to configured probe workload, persist each site's results immediately, and record startup and per-site progress for long cycles.
- Invalidate current status when enabled test types change and preserve skipped checks in error records.
- Exclude runtime data, credentials, and Git history from Docker build contexts.
- Reject unreachable Windows ping responses without echo timings, distinguish partial from total outages, and connect the add-site shortcut to its tab.
- Serialize shared DuckDB access across application processes and preserve intentionally empty configuration stores.
- Bound HTTP checks with a worker deadline and avoid downloading response bodies, including redirects.
- Correct decimal packet loss and Linux, macOS, and Windows ping arguments and output handling.
- Show only enabled current targets, mark stale or pending observations unknown, and require recent monitoring heartbeats for health checks.
- Keep configuration IDs separate from editable names, honor the interval environment setting, and support false disabled ping defaults.
- Bind Docker's published management port to localhost and make test failures return a nonzero status.
- **SQL Injection Vulnerabilities**: Replaced string formatting with parameterized queries
- **Navigation Button Feedback**: Fixed button highlighting to respond immediately to clicks
- **Configuration Validation**: Added proper validation for monitoring configuration entries
- **DuckDB SQL Syntax**: Fixed interval query syntax to be compatible with DuckDB
- **Database Connection Management**: Implemented proper connection closing to prevent resource leaks
- **Error Propagation**: Enhanced error handling and logging throughout the application

### Security
- **Input Validation**: Added comprehensive input validation for all configuration fields
- **SQL Injection Prevention**: Implemented parameterized queries throughout the database layer
- **Data Sanitization**: Added proper data sanitization for user inputs
- **Connection Safety**: Database connections are now properly managed and closed
- **Logging Security**: Sensitive information is not exposed in log messages

## [v1.0.0] - Initial Release

### Added
- **Network Monitoring**: Basic HTTP and ping monitoring functionality
- **Streamlit Dashboard**: Web-based dashboard for viewing monitoring results
- **DuckDB Storage**: Lightweight database for storing monitoring data
- **Docker Support**: Docker and Docker Compose configuration
- **Multiple Monitoring Types**: Support for HTTP-only, ping-only, and full monitoring
- **Real-time Dashboard**: Live status updates and historical data visualization
- **Automated Cleanup**: Automatic cleanup of old monitoring data

### Features
- Monitor HTTP response times and status codes
- Monitor ping latency and packet loss
- Configurable monitoring intervals
- Historical data visualization
- Status indicators and alerts
- Cross-platform compatibility
- Containerized deployment

---

## Version Format

This project uses [Semantic Versioning](https://semver.org/) for version numbers:
- **MAJOR**: Incompatible API changes
- **MINOR**: Backwards-compatible functionality additions
- **PATCH**: Backwards-compatible bug fixes

## Categories

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Features that have been removed
- **Fixed**: Bug fixes
- **Security**: Security improvements
