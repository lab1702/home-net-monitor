#!/bin/bash

# Home Network Monitor - Package Version Display
# Shows current installed package versions

echo "🏠 Home Network Monitor - Installed Package Versions"
echo "=================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment and show versions
source venv/bin/activate

echo "📅 Generated on: $(date)"
echo "🐍 Python version: $(python --version)"
echo ""
echo "📦 Main packages:"
pip list | grep -E "(streamlit|duckdb|requests|pandas|plotly|python-dotenv|schedule)" | column -t

echo ""
echo "🔧 All packages:"
pip list | column -t

echo ""
echo "💾 To create a locked requirements file:"
echo "  pip freeze > requirements-locked.txt"
