#!/usr/bin/env python3
"""Demo script showing different dashboard status header states."""

def get_status_header(online_sites, total_sites):
    """Determine status header based on site counts."""
    if total_sites == 0:
        return "⚪ Current Status - No Data Available"
    elif online_sites == total_sites:
        return "🟢 Current Status - All Systems Operational"
    elif online_sites > 0:
        return "🟡 Current Status - Partial Outage"
    else:
        return "🔴 Current Status - System Outage"

def main():
    """Demo different status scenarios."""
    print("=== Dashboard Status Header Demo ===")
    print()
    
    # Test scenarios
    scenarios = [
        (7, 7, "All sites online"),
        (5, 7, "2 sites down"),
        (1, 7, "6 sites down"),
        (0, 7, "All sites down"),
        (0, 0, "No sites configured"),
    ]
    
    for online, total, description in scenarios:
        header = get_status_header(online, total)
        print(f"{description:20} → {header}")
    
    print()
    print("Current system status:")
    
    # Real system status
    try:
        from database import DatabaseManager
        db = DatabaseManager()
        current_status = db.get_current_status()
        
        if not current_status.empty:
            total_sites = len(current_status)
            online_sites = current_status['overall_success'].sum()
            
            header = get_status_header(online_sites, total_sites)
            print(f"Real status ({online_sites}/{total_sites}) → {header}")
        else:
            print("No data available → ⚪ Current Status - No Data Available")
            
    except Exception as e:
        print(f"Error accessing database: {e}")

if __name__ == "__main__":
    main()
