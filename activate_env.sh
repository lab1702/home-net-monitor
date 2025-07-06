#!/bin/bash

# Home Network Monitor - Environment Activation Script
# This script activates the Python virtual environment for the project

echo "🔧 Activating Home Network Monitor Python environment..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run the following commands to set up the environment:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Activate the virtual environment
source venv/bin/activate

echo "✅ Virtual environment activated!"
echo "📦 Installed packages:"
pip list | grep -E "(streamlit|duckdb|requests|pandas|plotly|python-dotenv|schedule)"

echo ""
echo "🚀 Ready to run the Home Network Monitor!"
echo "To deactivate the environment, run: deactivate"
