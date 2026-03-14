import streamlit as st
import pandas as pd
import io
from datetime import datetime
import json
import os


def render_column_selector_page():
    """Render the Column Selector page for custom column extraction and addition."""
    
    st.title("📋 Custom Column Selector")
    st.markdown("Upload a file, select columns you want, add custom columns, and download the customized Excel file.")
    
    # Initialize session state for saved configurations
    if 'column_configs' not in st.session_state:
        st.session_state.column_configs = load_saved_configs()
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose an Excel or CSV file",
        type=['xlsx', 'xls', 'csv'],
        help="Upload your data file",
        key="column_selector_uploader"
    )
    
    if uploaded_file is not None:
        try:
            # Read the file
            with st.spinner("Reading file..."):
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
            
            st.success(f"✅ File uploaded successfully! Total records: {len(df):,}")
            
            # Show preview
            with st.expander("📋 Preview Data (First 10 rows)", expanded=False):
                st.dataframe(df.head(10))
            
            st.markdown("---")
            
            # Configuration Management Section
            st.subheader("💾 Configuration Management")
            
            config_col1, config_col2, config_col3 = st.columns(3)
            
            with config_col1:
                # Load saved configuration
                if st.session_state.column_configs:
                    config_names = ["-- New Configuration --"] + list(st.session_state.column_configs.keys())
                    selected_config = st.selectbox(
                        "Load Saved Configuration",
                        options=config_names,
                        key="load_config_select"
                    )
                else:
                    selected_config = "-- New Configuration --"
                    st.info("No saved configurations yet")
            
            with config_col2:
                config_name = st.text_input(
                    "Configuration Name",
                    placeholder="e.g., Bank Report Format",
                    key="config_name_input",
                    help="Give a name to save this configuration for future use"
                )
            
            with config_col3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("💾 Save Configuration", use_container_width=True, key="save_config_btn"):
                    if config_name:
                        # Save current configuration
                        current_config = {
                            'selected_columns': st.session_state.get('selected_columns_list', []),
                            'custom_columns': st.session_state.get('custom_columns_list', [])
                        }
                        st.session_state.column_configs[config_name] = current_config
                        save_configs_to_file(st.session_state.column_configs)
                        st.success(f"✅ Configuration '{config_name}' saved!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Please enter a configuration name")
            
            # Load configuration if selected
            if selected_config != "-- New Configuration --" and selected_config in st.session_state.column_configs:
                loaded_config = st.session_state.column_configs[selected_config]
                st.session_state.selected_columns_list = loaded_config.get('selected_columns', [])
                st.session_state.custom_columns_list = loaded_config.get('custom_columns', [])
                st.info(f"📂 Loaded configuration: {selected_config}")
            
            st.markdown("---")
            
            # Column Selection Section
            st.subheader("✅ Select Columns from File")
            
            available_columns = list(df.columns)
            
            # Initialize selected columns in session state
            if 'selected_columns_list' not in st.session_state:
                st.session_state.selected_columns_list = []
            
            # Multi-select for columns
            selected_columns = st.multiselect(
                "Choose columns to include in output",
                options=available_columns,
                default=st.session_state.selected_columns_list if st.session_state.selected_columns_list else [],
                key="column_multiselect",
                help="Select one or more columns from your uploaded file"
            )
            
            # Update session state
            st.session_state.selected_columns_list = selected_columns
            
            if selected_columns:
                st.success(f"✅ Selected {len(selected_columns)} column(s)")
            
            st.markdown("---")
            
            # Custom Column Addition Section
            st.subheader("➕ Add Custom Columns")
            
            # Initialize custom columns in session state
            if 'custom_columns_list' not in st.session_state:
                st.session_state.custom_columns_list = []
            
            # Add new custom column
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                new_column_name = st.text_input(
                    "Custom Column Name",
                    placeholder="e.g., Remarks",
                    key="new_column_name_input"
                )
            
            with col2:
                new_column_value = st.text_input(
                    "Value for First Row (Optional)",
                    placeholder="e.g., Pending",
                    key="new_column_value_input",
                    help="This value will be added to the first row only"
                )
            
            with col3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("➕ Add Column", use_container_width=True, key="add_custom_column_btn"):
                    if new_column_name:
                        custom_col_info = {
                            'name': new_column_name,
                            'first_row_value': new_column_value if new_column_value else ""
                        }
                        st.session_state.custom_columns_list.append(custom_col_info)
                        st.success(f"✅ Added custom column: {new_column_name}")
                        st.rerun()
                    else:
                        st.warning("⚠️ Please enter a column name")
            
            # Display current custom columns
            if st.session_state.custom_columns_list:
                st.markdown("**Current Custom Columns:**")
                for idx, col_info in enumerate(st.session_state.custom_columns_list):
                    col_display1, col_display2 = st.columns([4, 1])
                    with col_display1:
                        first_val = col_info['first_row_value']
                        display_text = f"• **{col_info['name']}**"
                        if first_val:
                            display_text += f" (First row: '{first_val}')"
                        st.markdown(display_text)
                    with col_display2:
                        if st.button("🗑️ Remove", key=f"remove_custom_col_{idx}", use_container_width=True):
                            st.session_state.custom_columns_list.pop(idx)
                            st.rerun()
            else:
                st.info("No custom columns added yet")
            
            st.markdown("---")
            
            # Preview and Generate Section
            st.subheader("📊 Preview & Generate")
            
            if selected_columns or st.session_state.custom_columns_list:
                # Create preview dataframe
                preview_df = df[selected_columns].copy() if selected_columns else pd.DataFrame()
                
                # Add custom columns to preview
                for col_info in st.session_state.custom_columns_list:
                    col_name = col_info['name']
                    first_val = col_info['first_row_value']
                    
                    # Create column with empty values
                    preview_df[col_name] = ""
                    
                    # Set first row value if provided
                    if first_val and len(preview_df) > 0:
                        preview_df.loc[0, col_name] = first_val
                
                # Show preview
                st.markdown("**Preview (First 10 rows):**")
                st.dataframe(preview_df.head(10), use_container_width=True)
                
                st.info(f"📊 Output will have {len(preview_df.columns)} columns and {len(preview_df):,} rows")
                
                # Generate Excel button
                gen_col1, gen_col2, gen_col3 = st.columns([1, 2, 1])
                
                with gen_col2:
                    if st.button("🚀 Generate Excel File", type="primary", use_container_width=True, key="generate_excel_btn"):
                        with st.spinner("Generating Excel file..."):
                            # Create final dataframe
                            final_df = df[selected_columns].copy() if selected_columns else pd.DataFrame(index=df.index)
                            
                            # Add custom columns
                            for col_info in st.session_state.custom_columns_list:
                                col_name = col_info['name']
                                first_val = col_info['first_row_value']
                                
                                # Create column with empty values
                                final_df[col_name] = ""
                                
                                # Set first row value if provided
                                if first_val and len(final_df) > 0:
                                    final_df.loc[0, col_name] = first_val
                            
                            # Create Excel file in memory
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                final_df.to_excel(writer, sheet_name='Data', index=False)
                                
                                # Auto-adjust column widths
                                worksheet = writer.sheets['Data']
                                for idx, col in enumerate(final_df.columns):
                                    max_length = max(
                                        final_df[col].astype(str).apply(len).max(),
                                        len(str(col))
                                    )
                                    # Convert column index to Excel column letter
                                    col_letter = chr(65 + idx) if idx < 26 else chr(65 + idx // 26 - 1) + chr(65 + idx % 26)
                                    worksheet.column_dimensions[col_letter].width = min(max_length + 2, 50)
                            
                            excel_data = output.getvalue()
                            st.session_state.generated_excel = excel_data
                            st.success("✅ Excel file generated successfully!")
                
                # Download button
                if 'generated_excel' in st.session_state:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"custom_columns_{timestamp}.xlsx"
                    
                    st.download_button(
                        label="⬇️ Download Excel File",
                        data=st.session_state.generated_excel,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        use_container_width=True,
                        key="download_custom_excel"
                    )
            
            else:
                st.warning("⚠️ Please select at least one column or add a custom column")
            
            # Delete Configuration Section
            if st.session_state.column_configs:
                st.markdown("---")
                with st.expander("🗑️ Delete Saved Configurations", expanded=False):
                    config_to_delete = st.selectbox(
                        "Select configuration to delete",
                        options=list(st.session_state.column_configs.keys()),
                        key="delete_config_select"
                    )
                    
                    if st.button("🗑️ Delete Configuration", type="primary", key="delete_config_btn"):
                        if config_to_delete in st.session_state.column_configs:
                            del st.session_state.column_configs[config_to_delete]
                            save_configs_to_file(st.session_state.column_configs)
                            st.success(f"✅ Configuration '{config_to_delete}' deleted!")
                            st.rerun()
        
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.info("Please ensure the file is a valid Excel or CSV file.")
    
    else:
        # Instructions when no file is uploaded
        st.info("👆 Please upload a file to get started")
        
        with st.expander("ℹ️ How to Use", expanded=True):
            st.markdown("""
            ### Step-by-Step Guide:
            
            1. **Upload File**: Upload your Excel or CSV file
            2. **Select Columns**: Choose which columns from your file you want to keep
            3. **Add Custom Columns**: Add new columns with custom names
               - Enter column name
               - Optionally add a value for the first row
               - Click "Add Column"
            4. **Save Configuration**: Save your column selection for future use
               - Enter a configuration name
               - Click "Save Configuration"
            5. **Load Configuration**: Next time, just load your saved configuration
            6. **Generate**: Click "Generate Excel File" to create your custom file
            7. **Download**: Download the generated Excel file
            
            ### Features:
            - ✅ Select specific columns from uploaded file
            - ✅ Add custom blank columns with any name
            - ✅ Set first row value for custom columns
            - ✅ Save and load column configurations
            - ✅ Auto-adjust column widths in output
            - ✅ Support for Excel (.xlsx, .xls) and CSV files
            
            ### Configuration Memory:
            Your saved configurations are stored locally and will be available every time you use this page!
            """)
    
    # Footer
    st.markdown("---")
    st.markdown("Built with Streamlit 🎈 | Custom Column Selector Tool")


def load_saved_configs():
    """Load saved configurations from file."""
    config_file = "cyber multiple accoun with DA and ACK/.kiro/column_selector_configs.json"
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.warning(f"Could not load saved configurations: {str(e)}")
    
    return {}


def save_configs_to_file(configs):
    """Save configurations to file."""
    config_dir = "cyber multiple accoun with DA and ACK/.kiro"
    config_file = os.path.join(config_dir, "column_selector_configs.json")
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(config_dir, exist_ok=True)
        
        # Save configurations
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(configs, f, indent=2, ensure_ascii=False)
    
    except Exception as e:
        st.error(f"Could not save configurations: {str(e)}")
