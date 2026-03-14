import streamlit as st
import pandas as pd
import io
from datetime import datetime
import zipfile
from src.persistent_mapping import PersistentMapping


def render_districtwise_page():
    """Render the Districtwise Data page for splitting transactions by district."""
    
    # Initialize persistent mapping
    mapping = PersistentMapping('districtwise')
    
    # Title and description
    st.title("📊 Data Splitter by Column")
    st.markdown("Upload an Excel file and split it by any column you choose (e.g., District, State, Bank Name, etc.)")

    # File upload
    uploaded_file = st.file_uploader(
        "Choose an Excel file (.xlsx)",
        type=['xlsx'],
        help="Upload an Excel file to split by any column",
        key="districtwise_uploader"
    )

    if uploaded_file is not None:
        try:
            # Read the Excel file
            with st.spinner("Reading Excel file..."):
                df = pd.read_excel(uploaded_file)
            
            st.success(f"✅ File uploaded successfully! Total records: {len(df):,}")
            
            # Show available columns
            st.markdown("---")
            st.subheader("📋 Select Column to Split By")
            
            # Show saved mappings indicator
            saved_count = mapping.get_saved_count()
            if saved_count > 0:
                st.success(f"✅ {saved_count} column mapping(s) remembered")
            
            available_columns = list(df.columns)
            
            # Column selection
            col_select_col1, col_select_col2 = st.columns([2, 1])
            
            with col_select_col1:
                # Try to find default column (Victim District, District, State, etc.)
                default_column = None
                priority_columns = ['Victim District', 'District', 'State', 'Bank Name', 'City']
                for col in priority_columns:
                    if col in available_columns:
                        default_column = col
                        break
                
                # Get saved column or use priority default
                saved_col = mapping.get('selected_column')
                if saved_col and saved_col in available_columns:
                    default_index = available_columns.index(saved_col)
                elif default_column:
                    default_index = available_columns.index(default_column)
                else:
                    default_index = 0
                
                selected_column = st.selectbox(
                    "Choose column to split data by:",
                    options=available_columns,
                    index=default_index,
                    key="split_column_select",
                    help="Select the column you want to use for splitting the data into separate sheets/files"
                )
                if selected_column:
                    mapping.set('selected_column', selected_column)
            
            with col_select_col2:
                st.markdown("<br>", unsafe_allow_html=True)
                st.info(f"📊 Column: **{selected_column}**")
            
            # Check if selected column exists
            if selected_column not in df.columns:
                st.error(f"❌ Error: '{selected_column}' column not found in the Excel file.")
                st.info(f"Available columns: {', '.join(df.columns)}")
            else:
                # Display file info
                st.success(f"✅ Splitting by column: **{selected_column}**")
                
                # Show preview of data
                with st.expander("📋 Preview Data (First 10 rows)"):
                    st.dataframe(df.head(10))
                
                # Get unique values in selected column
                unique_values = df[selected_column].dropna().unique()
                num_unique = len(unique_values)
                
                st.info(f"📍 Found **{num_unique}** unique values in '{selected_column}' column")
                
                # Show statistics per unique value
                with st.expander(f"📊 Statistics by {selected_column}"):
                    stats_df = df.groupby(selected_column).agg({
                        df.columns[0]: 'count'  # Count records
                    }).rename(columns={df.columns[0]: 'Number of Records'})
                    
                    # Add amount column if it exists
                    amount_cols = [col for col in df.columns if 'amount' in col.lower() or 'value' in col.lower()]
                    if amount_cols:
                        for col in amount_cols:
                            if pd.api.types.is_numeric_dtype(df[col]):
                                stats_df[f'Total {col}'] = df.groupby(selected_column)[col].sum()
                    
                    st.dataframe(stats_df)
                
                # Process button
                col1, col2 = st.columns(2)
                
                with col1:
                    process_single = st.button(f"🔄 Generate Single Excel File (All {selected_column}s in Sheets)", type="primary", use_container_width=True, key="districtwise_single")
                
                with col2:
                    process_separate = st.button("📦 Generate Separate Files (ZIP)", type="primary", use_container_width=True, key="districtwise_separate")
                
                # Process single Excel file with multiple sheets
                if process_single:
                    with st.spinner(f"Processing file and creating sheets by {selected_column}..."):
                        # Create Excel file in memory
                        output = io.BytesIO()
                        
                        # Create Excel writer
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            # Create a sheet for each unique value
                            for value in sorted(unique_values):
                                # Filter data for this value
                                value_df = df[df[selected_column] == value].copy()
                                
                                # Remove existing serial number columns (Sr No, S No., S.No, etc.)
                                sr_no_variations = ['Sr No', 'S No.', 'S.No', 'S No', 'Sr.No', 'Serial No', 'SNo', 'Sl No', 'Sl.No']
                                for col in sr_no_variations:
                                    if col in value_df.columns:
                                        value_df = value_df.drop(columns=[col])
                                
                                # Add Sr No column starting from 1 for each value
                                value_df.insert(0, 'Sr No', range(1, len(value_df) + 1))
                                
                                # Clean sheet name (Excel has 31 char limit and special char restrictions)
                                sheet_name = str(value)[:31]
                                # Remove invalid characters for Excel sheet names
                                invalid_chars = [':', '\\', '/', '?', '*', '[', ']']
                                for char in invalid_chars:
                                    sheet_name = sheet_name.replace(char, '_')
                                
                                # Write to sheet
                                value_df.to_excel(writer, sheet_name=sheet_name, index=False)
                                
                                # Auto-adjust column widths
                                worksheet = writer.sheets[sheet_name]
                                for idx, col in enumerate(value_df.columns):
                                    max_length = max(
                                        value_df[col].astype(str).apply(len).max(),
                                        len(str(col))
                                    )
                                    worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
                        
                        # Get the Excel file data
                        excel_data = output.getvalue()
                        
                        st.success(f"✅ Successfully created {num_unique} sheets by {selected_column}!")
                        
                        # Generate filename with timestamp
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"data_by_{selected_column.replace(' ', '_')}_{timestamp}.xlsx"
                        
                        # Download button
                        st.download_button(
                            label="⬇️ Download Single Excel File",
                            data=excel_data,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary",
                            key="districtwise_download_single"
                        )
                
                # Process separate Excel files in ZIP
                if process_separate:
                    with st.spinner(f"Creating separate Excel files for each {selected_column}..."):
                        # Create ZIP file in memory
                        zip_buffer = io.BytesIO()
                        
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            # Create a separate Excel file for each unique value
                            for value in sorted(unique_values):
                                # Filter data for this value
                                value_df = df[df[selected_column] == value].copy()
                                
                                # Remove existing serial number columns (Sr No, S No., S.No, etc.)
                                sr_no_variations = ['Sr No', 'S No.', 'S.No', 'S No', 'Sr.No', 'Serial No', 'SNo', 'Sl No', 'Sl.No']
                                for col in sr_no_variations:
                                    if col in value_df.columns:
                                        value_df = value_df.drop(columns=[col])
                                
                                # Add Sr No column starting from 1 for each value
                                value_df.insert(0, 'Sr No', range(1, len(value_df) + 1))
                                
                                # Create Excel file in memory for this value
                                excel_buffer = io.BytesIO()
                                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                                    value_df.to_excel(writer, sheet_name='Data', index=False)
                                    
                                    # Auto-adjust column widths
                                    worksheet = writer.sheets['Data']
                                    for idx, col in enumerate(value_df.columns):
                                        max_length = max(
                                            value_df[col].astype(str).apply(len).max(),
                                            len(str(col))
                                        )
                                        worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
                                
                                # Clean filename (remove invalid characters)
                                clean_value_name = str(value)
                                invalid_chars = [':', '\\', '/', '?', '*', '[', ']', '<', '>', '|', '"']
                                for char in invalid_chars:
                                    clean_value_name = clean_value_name.replace(char, '_')
                                
                                # Add Excel file to ZIP
                                filename = f"{clean_value_name}.xlsx"
                                zip_file.writestr(filename, excel_buffer.getvalue())
                        
                        # Get the ZIP file data
                        zip_data = zip_buffer.getvalue()
                        
                        st.success(f"✅ Successfully created {num_unique} separate Excel files!")
                        
                        # Generate filename with timestamp
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        zip_filename = f"data_by_{selected_column.replace(' ', '_')}_{timestamp}.zip"
                        
                        # Download button
                        st.download_button(
                            label="⬇️ Download ZIP File (Separate Files)",
                            data=zip_data,
                            file_name=zip_filename,
                            mime="application/zip",
                            type="primary",
                            key="districtwise_download_zip"
                        )
        
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.info("Please ensure the file is a valid Excel (.xlsx) file.")

    else:
        # Instructions when no file is uploaded
        st.info("👆 Please upload an Excel file to get started")
        
        with st.expander("ℹ️ Instructions"):
            st.markdown("""
            ### How to use this app:
            
            1. **Upload** your Excel file (.xlsx format)
            2. **Select Column** - Choose which column to split by (e.g., District, State, Bank Name)
            3. The app will automatically detect unique values in that column
            4. Review the **statistics** to see the breakdown
            5. Choose your preferred output format:
               - **Single Excel File**: All values in separate sheets within one file
               - **Separate Files (ZIP)**: Individual Excel file for each value in a ZIP archive
            6. **Download** the processed file(s)
            
            ### Requirements:
            - File must be in Excel format (.xlsx)
            - Select any column you want to split by
            - Each unique value will get its own sheet/file
            
            ### Features:
            - ✅ Split by ANY column (District, State, Bank, City, etc.)
            - ✅ Preserves all original columns and data
            - ✅ Auto-adjusts column widths for readability
            - ✅ Shows statistics per unique value
            - ✅ Handles special characters in names
            - ✅ Adds Sr No column starting from 1 for each split
            - ✅ Two output options: Single file or separate files in ZIP
            
            ### Examples:
            - Split by **District** → Get separate files for each district
            - Split by **State** → Get separate files for each state
            - Split by **Bank Name** → Get separate files for each bank
            - Split by **Status** → Get separate files for each status
            """)

    # Footer
    st.markdown("---")
    st.markdown("Built with Streamlit 🎈 | Powered by pandas and openpyxl")
