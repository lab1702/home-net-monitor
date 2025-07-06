#!/usr/bin/env python3
"""
Verification script to check that documentation instructions are accurate.
"""

import os
import sys
import importlib.util

def test_file_exists(filepath, description):
    """Test if a file exists."""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} NOT FOUND")
        return False

def test_import(module_name, description):
    """Test if a Python module can be imported."""
    try:
        spec = importlib.util.spec_from_file_location(module_name, f"{module_name}.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        print(f"✅ {description}: {module_name}.py can be imported")
        return True
    except Exception as e:
        print(f"❌ {description}: {module_name}.py import failed - {e}")
        return False

def main():
    print("🔍 Verifying Home Network Monitor Documentation")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Test key files mentioned in documentation
    files_to_check = [
        ("requirements.txt", "Dependencies file"),
        ("dashboard.py", "Main Streamlit application"),
        ("monitoring_service.py", "Background monitoring service"),
        ("config.py", "Configuration file"),
        ("database.py", "Database management"),
        ("monitor.py", "Core monitoring logic"),
        ("test_setup.py", "Environment test script"),
        ("activate_env.sh", "Environment activation script"),
        ("show_versions.sh", "Version display script"),
        ("SETUP.md", "Setup documentation"),
        ("README.md", "Project documentation"),
        ("CHANGELOG.md", "Change log"),
        ("STATUS.md", "Project status"),
    ]
    
    print("\n📁 File Existence Checks:")
    for filepath, description in files_to_check:
        if not test_file_exists(filepath, description):
            all_tests_passed = False
    
    # Test Python module imports
    modules_to_test = [
        ("dashboard", "Streamlit dashboard"),
        ("monitoring_service", "Monitoring service"),
        ("config", "Configuration module"),
        ("database", "Database module"),
        ("monitor", "Monitor module"),
    ]
    
    print("\n🐍 Python Module Import Checks:")
    for module_name, description in modules_to_test:
        if not test_import(module_name, description):
            all_tests_passed = False
    
    # Check specific documentation references
    print("\n📖 Documentation Reference Checks:")
    
    # Check that SETUP.md doesn't reference app.py
    try:
        with open("SETUP.md", "r") as f:
            setup_content = f.read()
            if "app.py" in setup_content:
                print("❌ SETUP.md contains references to app.py (should be dashboard.py)")
                all_tests_passed = False
            else:
                print("✅ SETUP.md correctly references dashboard.py (not app.py)")
    except FileNotFoundError:
        print("❌ SETUP.md not found")
        all_tests_passed = False
    
    # Check that README.md has correct commands
    try:
        with open("README.md", "r") as f:
            readme_content = f.read()
            if "streamlit run dashboard.py" in readme_content:
                print("✅ README.md contains correct streamlit command")
            else:
                print("❌ README.md missing correct streamlit command")
                all_tests_passed = False
    except FileNotFoundError:
        print("❌ README.md not found")
        all_tests_passed = False
    
    # Summary
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("✅ All documentation verification tests PASSED!")
        print("📚 Documentation appears to be accurate and consistent.")
        return 0
    else:
        print("❌ Some documentation verification tests FAILED!")
        print("📚 Please review and fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
