"""Configuration management functionality for the network monitor dashboard."""

import streamlit as st
import pandas as pd
from typing import Dict, Optional
from database import DatabaseManager
from validators import validate_config as validate_config_core


def render_config_management():
    """Render the configuration management interface."""
    st.header("🛠️ Configuration Management")
    st.markdown("Manage monitoring configurations for your network sites.")
    
    # Initialize database
    db = DatabaseManager()
    
    # Add information to sidebar
    with st.sidebar:
        st.markdown("---")
        st.markdown("**Configuration Status:**")
        
        # Get configuration summary
        enabled_configs = db.get_enabled_configurations()
        all_configs = db.get_all_configurations()
        
        if not all_configs.empty:
            total_sites = len(all_configs)
            enabled_sites = len(enabled_configs)
            disabled_sites = total_sites - enabled_sites
            
            st.metric("Total Sites", total_sites)
            st.metric("Enabled Sites", enabled_sites)
            st.metric("Disabled Sites", disabled_sites)
        else:
            st.info("No sites configured")
        
        st.markdown("---")
        st.markdown("**Quick Actions:**")
        if st.button("✏️ Add New Site", use_container_width=True):
            st.session_state.config_tab = "add"
        if st.button("📊 View Dashboard", use_container_width=True):
            st.session_state.page = "Dashboard"
            st.rerun()
    
    # Get all configurations
    config_df = db.get_all_configurations()
    
    # Create tabs for different operations
    tab1, tab2 = st.tabs(["📋 View/Edit Configurations", "➕ Add New Configuration"])
    
    with tab1:
        st.subheader("Current Configurations")
        
        if not config_df.empty:
            # Display current configurations
            display_df = config_df.copy()
            display_df['enabled'] = display_df['enabled'].map({True: '✅', False: '❌'})
            display_df['enable_http'] = display_df['enable_http'].map({True: '✅', False: '❌'})
            display_df['enable_ping'] = display_df['enable_ping'].map({True: '✅', False: '❌'})
            
            # Rename columns for better display
            display_df.columns = ['ID', 'Name', 'URL', 'Ping Host', 'Enabled', 'HTTP Test', 'Ping Test', 'Created', 'Updated']
            
            # Hide technical columns
            display_df = display_df[['ID', 'Name', 'URL', 'Ping Host', 'Enabled', 'HTTP Test', 'Ping Test']]
            
            # Display the table
            st.dataframe(display_df, use_container_width=True)
            
            # Configuration editing section
            st.subheader("Edit Configuration")
            
            # Select configuration to edit
            config_options = config_df.apply(lambda x: f"{x['name']} (ID: {x['id']})", axis=1).tolist()
            selected_config = st.selectbox("Select configuration to edit:", config_options)
            
            if selected_config:
                # Extract ID from the selected option
                config_id = int(selected_config.split('ID: ')[1].split(')')[0])
                config_row = config_df[config_df['id'] == config_id].iloc[0]
                
                # Edit form
                with st.form(f"edit_config_{config_id}"):
                    st.write(f"**Editing: {config_row['name']}**")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        name = st.text_input("Site Name", value=config_row['name'])
                        url = st.text_input("URL (optional)", value=config_row['url'] if pd.notna(config_row['url']) else "")
                        ping_host = st.text_input("Ping Host (optional)", value=config_row['ping_host'] if pd.notna(config_row['ping_host']) else "")
                    
                    with col2:
                        enabled = st.checkbox("Site Enabled", value=config_row['enabled'])
                        enable_http = st.checkbox("Enable HTTP Test", value=config_row['enable_http'])
                        enable_ping = st.checkbox("Enable Ping Test", value=config_row['enable_ping'])
                    
                    # Validation message
                    if not enable_http and not enable_ping:
                        st.error("At least one test type (HTTP or Ping) must be enabled.")
                    
                    if not url.strip() and enable_http:
                        st.error("URL is required when HTTP test is enabled.")
                    
                    if not ping_host.strip() and enable_ping:
                        st.error("Ping Host is required when Ping test is enabled.")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_button = st.form_submit_button("Update Configuration", type="primary")
                    with col2:
                        delete_button = st.form_submit_button("Delete Configuration", type="secondary")
                    
                    if update_button:
                        if validate_config(name, url, ping_host, enable_http, enable_ping):
                            try:
                                config_data = {
                                    'name': name,
                                    'url': url.strip() if url.strip() else None,
                                    'ping_host': ping_host.strip() if ping_host.strip() else None,
                                    'enabled': enabled,
                                    'enable_http': enable_http,
                                    'enable_ping': enable_ping
                                }
                                
                                db.update_configuration(config_id, config_data)
                                st.success(f"Configuration '{name}' updated successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error updating configuration: {e}")
                    
                    if delete_button:
                        try:
                            db.delete_configuration(config_id)
                            st.success(f"Configuration '{config_row['name']}' deleted successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting configuration: {e}")
        else:
            st.info("No configurations found. Add a new configuration to get started.")
    
    with tab2:
        st.subheader("Add New Configuration")
        
        # Add new configuration form
        with st.form("add_config"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Site Name *", help="Display name for the site")
                url = st.text_input("URL (optional)", help="HTTP/HTTPS URL to monitor")
                ping_host = st.text_input("Ping Host (optional)", help="Hostname or IP address to ping")
            
            with col2:
                enabled = st.checkbox("Site Enabled", value=True)
                enable_http = st.checkbox("Enable HTTP Test", value=True)
                enable_ping = st.checkbox("Enable Ping Test", value=True)
            
            # Validation messages
            if not enable_http and not enable_ping:
                st.error("At least one test type (HTTP or Ping) must be enabled.")
            
            if not url.strip() and enable_http:
                st.error("URL is required when HTTP test is enabled.")
            
            if not ping_host.strip() and enable_ping:
                st.error("Ping Host is required when Ping test is enabled.")
            
            submit_button = st.form_submit_button("Add Configuration", type="primary")
            
            if submit_button:
                if validate_config(name, url, ping_host, enable_http, enable_ping):
                    try:
                        config_data = {
                            'name': name,
                            'url': url.strip() if url.strip() else None,
                            'ping_host': ping_host.strip() if ping_host.strip() else None,
                            'enabled': enabled,
                            'enable_http': enable_http,
                            'enable_ping': enable_ping
                        }
                        
                        db.insert_configuration(config_data)
                        st.success(f"Configuration '{name}' added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding configuration: {e}")
    
    # Configuration guidelines
    st.markdown("---")
    st.subheader("📖 Configuration Guidelines")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **HTTP Monitoring:**
        - Use for websites and web services
        - Checks HTTP response codes and response times
        - Use HTTPS URLs when available
        - Example: `https://www.google.com`
        """)
    
    with col2:
        st.markdown("""
        **Ping Monitoring:**
        - Use for network connectivity checks
        - Works with hostnames or IP addresses
        - Good for DNS servers, routers, etc.
        - Example: `8.8.8.8` or `google.com`
        """)
    
    st.markdown("""
    **Common Configurations:**
    - **Full Monitoring**: Enable both HTTP and Ping for comprehensive monitoring
    - **HTTP Only**: For sites that block ping (many CDNs and cloud services)
    - **Ping Only**: For infrastructure devices without web interfaces
    
    **Requirements:**
    - Site name is always required
    - At least one test type must be enabled
    - URL is required if HTTP test is enabled
    - Ping host is required if Ping test is enabled
    """)


def validate_config(name: str, url: str, ping_host: str, enable_http: bool, enable_ping: bool) -> bool:
    """Wrapper for validate_config to handle errors in the Streamlit interface."""
    try:
        validate_config_core({
            'name': name,
            'url': url,
            'ping_host': ping_host,
            'enable_http': enable_http,
            'enable_ping': enable_ping
        })
        return True
    except ValueError as e:
        st.error(str(e))
        return False
