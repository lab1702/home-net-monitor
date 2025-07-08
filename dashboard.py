"""Streamlit dashboard for network monitoring data."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

from database import DatabaseManager
import config
from config_management import render_config_management

# Configure page
st.set_page_config(
    page_title=config.STREAMLIT_PAGE_TITLE,
    page_icon=config.STREAMLIT_PAGE_ICON,
    layout=config.STREAMLIT_LAYOUT,
    initial_sidebar_state="expanded"
)

# Initialize database
@st.cache_resource
def init_database():
    return DatabaseManager()

db = init_database()

# Dashboard title
st.title("📡 Home Network Monitor")
st.markdown("Monitor your internet connection performance and availability")

# Initialize page state
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

# Sidebar for controls
with st.sidebar:
    st.header("📋 Navigation")
    
    # Navigation buttons
    current_page = st.session_state.page
    
    # Dashboard button
    dashboard_type = "primary" if current_page == "Dashboard" else "secondary"
    if st.button("📊 Dashboard", use_container_width=True, type=dashboard_type):
        st.session_state.page = "Dashboard"
        st.rerun()
    
    # Configuration Management button
    config_type = "primary" if current_page == "Configuration Management" else "secondary"
    if st.button("⚙️ Configuration Management", use_container_width=True, type=config_type):
        st.session_state.page = "Configuration Management"
        st.rerun()
    
    st.markdown("---")
    st.header("⚙️ Settings")
    
    # Time range selector
    time_range = st.selectbox(
        "Time Range",
        ["Last 1 Hour", "Last 6 Hours", "Last 24 Hours", "Last 7 Days", "Last 30 Days"],
        index=2
    )
    
    # Map time range to hours
    time_range_hours = {
        "Last 1 Hour": 1,
        "Last 6 Hours": 6,
        "Last 24 Hours": 24,
        "Last 7 Days": 24 * 7,
        "Last 30 Days": 24 * 30
    }
    
    hours = time_range_hours[time_range]
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
    
    # Manual refresh button
    if st.button("🔄 Refresh Now"):
        st.rerun()

# Render appropriate page
if st.session_state.page == "Configuration Management":
    render_config_management()
    st.stop()  # Stop rendering the rest of the dashboard

# Auto-refresh functionality will be handled at the end

# Main dashboard content
try:
    # Current Status Section
    current_status = db.get_current_status()
    
    # Determine status color based on system health
    if not current_status.empty:
        total_sites = len(current_status)
        online_sites = current_status['overall_success'].sum()
        
        # Choose header color based on system status
        if online_sites == total_sites:
            status_icon = "🟢"  # All sites online
            status_text = "All Systems Operational"
        elif online_sites > 0:
            status_icon = "🟡"  # Some sites down
            status_text = "Partial Outage"
        else:
            status_icon = "🔴"  # All sites down
            status_text = "System Outage"
    else:
        status_icon = "⚪"
        status_text = "No Data Available"
    
    st.header(f"{status_icon} Current Status - {status_text}")
    
    if not current_status.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Sites", total_sites)
        
        with col2:
            st.metric("Online Sites", online_sites)
        
        with col3:
            offline_sites = total_sites - online_sites
            st.metric("Offline Sites", offline_sites)
        
        with col4:
            if total_sites > 0:
                uptime_percent = (online_sites / total_sites) * 100
                st.metric("Overall Uptime", f"{uptime_percent:.1f}%")
            else:
                st.metric("Overall Uptime", "N/A")
        
        # Current status table
        st.subheader("Site Status Details")
        status_df = current_status[[
            'site_name', 'overall_success', 'http_success', 'ping_success',
            'http_response_time_ms', 'ping_avg_ms', 'ping_packet_loss_percent', 'timestamp'
        ]].copy()
        
        # Format columns
        status_df['Status'] = status_df['overall_success'].apply(
            lambda x: '🟢 Online' if x else '🔴 Offline'
        )
        status_df['HTTP'] = status_df['http_success'].apply(
            lambda x: '✅' if x is True else ('❌' if x is False else '➖')
        )
        status_df['Ping'] = status_df['ping_success'].apply(
            lambda x: '✅' if x is True else ('❌' if x is False else '➖')
        )
        status_df['HTTP Response (ms)'] = status_df['http_response_time_ms'].apply(
            lambda x: f"{x:.1f}" if pd.notna(x) else "N/A"
        )
        status_df['Ping Time (ms)'] = status_df['ping_avg_ms'].apply(
            lambda x: f"{x:.1f}" if pd.notna(x) else "N/A"
        )
        status_df['Packet Loss (%)'] = status_df['ping_packet_loss_percent'].apply(
            lambda x: f"{x:.1f}" if pd.notna(x) else "N/A"
        )
        status_df['Last Check'] = pd.to_datetime(status_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        display_df = status_df[['site_name', 'Status', 'HTTP', 'Ping', 
                               'HTTP Response (ms)', 'Ping Time (ms)', 'Packet Loss (%)', 'Last Check']]
        display_df.columns = ['Site', 'Status', 'HTTP', 'Ping', 'HTTP Response (ms)', 
                             'Ping Time (ms)', 'Packet Loss (%)', 'Last Check']
        
        # Sort by site name for consistent display order
        display_df = display_df.sort_values('Site')
        
        st.dataframe(display_df, use_container_width=True)
    
    else:
        st.warning("No monitoring data available. Make sure the monitoring service is running.")
    
    # Historical Data Section
    st.header("📊 Historical Data")
    
    # Get summary statistics
    summary_stats = db.get_site_summary(hours)
    
    if not summary_stats.empty:
        # Site summary metrics
        st.subheader(f"Summary Statistics ({time_range})")
        
        # Sort summary statistics by site name for consistent display
        summary_stats = summary_stats.sort_values('site_name')
        
        # Create metrics for each site
        for _, row in summary_stats.iterrows():
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric(f"{row['site_name']} Uptime", f"{row['uptime_percent']:.1f}%")
            
            with col2:
                avg_http = row['avg_http_response_time']
                if pd.notna(avg_http):
                    st.metric("Avg HTTP (ms)", f"{avg_http:.1f}")
                else:
                    st.metric("Avg HTTP (ms)", "N/A")
            
            with col3:
                avg_ping = row['avg_ping_time']
                if pd.notna(avg_ping):
                    st.metric("Avg Ping (ms)", f"{avg_ping:.1f}")
                else:
                    st.metric("Avg Ping (ms)", "N/A")
            
            with col4:
                avg_loss = row['avg_packet_loss']
                if pd.notna(avg_loss):
                    st.metric("Avg Packet Loss (%)", f"{avg_loss:.1f}")
                else:
                    st.metric("Avg Packet Loss (%)", "N/A")
            
            with col5:
                st.metric("Total Checks", int(row['total_checks']))
        
        # Charts
        st.subheader("📈 Performance Charts")
        
        # Get historical data for charts
        historical_data = db.get_recent_results(hours)
        
        if not historical_data.empty:
            # Uptime chart
            fig_uptime = px.line(
                historical_data, 
                x='timestamp', 
                y='overall_success',
                color='site_name',
                title='Site Availability Over Time',
                labels={'overall_success': 'Online (1) / Offline (0)', 'timestamp': 'Time'},
                height=400
            )
            fig_uptime.update_traces(mode='lines+markers')
            st.plotly_chart(fig_uptime, use_container_width=True)
            
            # Response time chart
            response_time_data = historical_data[historical_data['http_response_time_ms'].notna()]
            if not response_time_data.empty:
                fig_response = px.line(
                    response_time_data,
                    x='timestamp',
                    y='http_response_time_ms',
                    color='site_name',
                    title='HTTP Response Time Over Time',
                    labels={'http_response_time_ms': 'Response Time (ms)', 'timestamp': 'Time'},
                    height=400
                )
                st.plotly_chart(fig_response, use_container_width=True)
            
            # Ping time chart
            ping_data = historical_data[historical_data['ping_avg_ms'].notna()]
            if not ping_data.empty:
                fig_ping = px.line(
                    ping_data,
                    x='timestamp',
                    y='ping_avg_ms',
                    color='site_name',
                    title='Ping Time Over Time',
                    labels={'ping_avg_ms': 'Ping Time (ms)', 'timestamp': 'Time'},
                    height=400
                )
                st.plotly_chart(fig_ping, use_container_width=True)
            
            # Packet loss chart
            packet_loss_data = historical_data[historical_data['ping_packet_loss_percent'].notna()]
            if not packet_loss_data.empty:
                fig_packet_loss = px.line(
                    packet_loss_data,
                    x='timestamp',
                    y='ping_packet_loss_percent',
                    color='site_name',
                    title='Packet Loss Over Time',
                    labels={'ping_packet_loss_percent': 'Packet Loss (%)', 'timestamp': 'Time'},
                    height=400
                )
                st.plotly_chart(fig_packet_loss, use_container_width=True)
        
        else:
            st.info(f"No historical data available for the selected time range ({time_range})")
    
    else:
        st.info("No summary statistics available. Data will appear once monitoring has been running.")

except Exception as e:
    st.error(f"Error loading dashboard data: {e}")
    st.info("Please ensure the monitoring service is running and the database is accessible.")

# Footer
st.markdown("---")
st.markdown("🏠 Home Network Monitor - Keeping your connection in check!")

# Auto-refresh status
if auto_refresh:
    st.info("⏱️ Auto-refresh is enabled. Page will refresh every 30 seconds.")
    time.sleep(30)
    st.rerun()
