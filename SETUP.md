# Home Network Monitor Setup Guide

This guide will help you set up the Python environment for the Home Network Monitor project.

## Prerequisites

- Python 3.13+ (recommended)
- `pip` package manager
- Virtual environment support (`venv`)

## Setup Instructions

### 1. Create Virtual Environment

```bash
python3 -m venv venv
```

### 2. Activate Virtual Environment

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
python test_setup.py
```

## Quick Setup

For convenience, you can use the provided activation script:

```bash
./activate_env.sh
```

## Installed Packages

The following Python packages are installed (always fetches latest versions):

- **Streamlit** - Web application framework
- **DuckDB** - In-memory analytical database
- **Requests** - HTTP library
- **Pandas** - Data manipulation and analysis
- **Plotly** - Interactive plotting library
- **Python-dotenv** - Environment variable loading
- **Schedule** - Job scheduling library

### Why Latest Versions?

The requirements.txt file uses no version constraints, which means:
- ✅ **Latest Features**: Always get the newest features and improvements
- ✅ **Security Updates**: Automatically receive security patches
- ✅ **Bug Fixes**: Benefit from the latest bug fixes
- ✅ **Performance**: Get performance improvements in newer releases
- ⚠️ **Note**: If you need reproducible builds, consider pinning versions after testing

## Environment Management

### Activate Environment
```bash
source venv/bin/activate
```

### Deactivate Environment
```bash
deactivate
```

### Update Dependencies
```bash
pip install -r requirements.txt --upgrade
```

### View Installed Packages
```bash
pip list
```

## Troubleshooting

### Virtual Environment Not Found
If you get an error about the virtual environment not being found:
1. Make sure you're in the project root directory
2. Run `python3 -m venv venv` to create the virtual environment

### Package Installation Errors
If you encounter errors during package installation:
1. Make sure your virtual environment is activated
2. Update pip: `pip install --upgrade pip`
3. Try installing packages individually if needed

### DuckDB Compilation Issues
If DuckDB fails to install due to compilation errors:
1. Make sure you have build tools installed
2. Try installing a pre-compiled wheel: `pip install --only-binary=all duckdb`
3. Update to a newer version of DuckDB that has binary wheels

## Next Steps

After completing the setup:
1. See [SITE_CONFIGURATION.md](SITE_CONFIGURATION.md) for configuration options
2. Start the monitoring service: `python monitoring_service.py &`
3. Run the dashboard with `streamlit run dashboard.py`
4. Open your browser to http://localhost:8501
5. Use the **Configuration Management** interface to manage monitoring targets

## Support

If you encounter any issues during setup, please check:
1. Python version compatibility
2. Virtual environment activation
3. Internet connectivity for package downloads
4. Available disk space for package installation
