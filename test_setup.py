#!/usr/bin/env python3
"""
Test script to verify that all Python dependencies are properly installed.
"""

import sys

def test_imports():
    """Test importing all required packages."""
    try:
        import streamlit as st
        print(f"✓ Streamlit {st.__version__}")
    except ImportError as e:
        print(f"✗ Streamlit import failed: {e}")
        return False

    try:
        import duckdb
        print(f"✓ DuckDB {duckdb.__version__}")
    except ImportError as e:
        print(f"✗ DuckDB import failed: {e}")
        return False

    try:
        import requests
        print(f"✓ Requests {requests.__version__}")
    except ImportError as e:
        print(f"✗ Requests import failed: {e}")
        return False

    try:
        import pandas as pd
        print(f"✓ Pandas {pd.__version__}")
    except ImportError as e:
        print(f"✗ Pandas import failed: {e}")
        return False

    try:
        import plotly
        print(f"✓ Plotly {plotly.__version__}")
    except ImportError as e:
        print(f"✗ Plotly import failed: {e}")
        return False

    try:
        import dotenv
        print(f"✓ Python-dotenv imported successfully")
    except ImportError as e:
        print(f"✗ Python-dotenv import failed: {e}")
        return False

    try:
        import schedule
        print(f"✓ Schedule imported successfully")
    except ImportError as e:
        print(f"✗ Schedule import failed: {e}")
        return False

    return True

def test_basic_functionality():
    """Test basic functionality of key packages."""
    try:
        # Test DuckDB
        import duckdb
        conn = duckdb.connect(':memory:')
        result = conn.execute("SELECT 'Hello DuckDB' as message").fetchone()
        print(f"✓ DuckDB test: {result[0]}")
        conn.close()
    except Exception as e:
        print(f"✗ DuckDB functionality test failed: {e}")
        return False

    try:
        # Test Pandas
        import pandas as pd
        df = pd.DataFrame({'test': [1, 2, 3]})
        print(f"✓ Pandas test: Created DataFrame with {len(df)} rows")
    except Exception as e:
        print(f"✗ Pandas functionality test failed: {e}")
        return False

    return True

if __name__ == "__main__":
    print("Testing Python environment setup...")
    print(f"Python version: {sys.version}")
    print()
    
    print("1. Testing package imports:")
    imports_ok = test_imports()
    print()
    
    print("2. Testing basic functionality:")
    functionality_ok = test_basic_functionality()
    print()
    
    if imports_ok and functionality_ok:
        print("✓ All tests passed! Python environment is ready.")
        sys.exit(0)
    else:
        print("✗ Some tests failed. Please check the setup.")
        sys.exit(1)
