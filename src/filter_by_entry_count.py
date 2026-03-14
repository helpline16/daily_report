import streamlit as st
import pandas as pd
import io
from datetime import datetime
import zipfile
from src.persistent_mapping import PersistentMapping


def render_filter_by_entry_count_page():
    """Render the Filter by Entry Count page - splits data by column but only includes values with minimum entry count."""
    
    # Initialize persistent mapping
    mapping = PersistentMapping('filter_by_entry_count')
    
    # Title and description
    st.title("🔢 Filter Data by Entry Count")
    st.markdown("Upload a file and filter by column values that have a minimum number of entries (e.g., only banks with 10+ transactions)")

    # File upload - support both Excel and CSV
    uploaded_file = st.file_uploader(
        "Choose an Excel or CSV file",
        type=['xlsx', 'xls', 'csv'],
        help="Upload an Excel or CSV file to filter by entry count",
        key="entry_count_uploader"
    )

    if uploaded_file is not None:
        try:
            # Read the file (Excel or CSV)
            with st.spinner("Reading file..."):
                if uploaded_file.name.lower().endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                    st.info("📄 CSV file detected")
                else:
                    df = pd.read_excel(uploaded_file)
                    st.info("📊 Excel file detected")
            
            st.success(f"✅ File uploaded successfully! Total records: {len(df):,}")
            
            # Show available columns
            st.markdown("---")
            st.subheader("📋 Select Column and Entry Count")
            
            # Show saved mappings indicator
            saved_count = mapping.get_saved_count()
            if saved_count > 0:
                st.success(f"✅ {saved_count} column mapping(s) remembered")
            
            available_columns = list(df.columns)
            
            # Column selection and entry count
            col_select_col1, col_select_col2 = st.columns([2, 1])
            
            with col_select_col1:
                # Try to find default column
                default_column = None
                priority_columns = ['Bank Name', 'Victim District', 'District', 'State', 'City', 'ACK']
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
                    "Choose column to filter by:",
                    options=available_columns,
                    index=default_index,
                    key="filter_column_select",
                    help="Select the column you want to use for filtering (e.g., Bank Name, District)"
                )
                if selected_column:
                    mapping.set('selected_column', selected_column)
            
            with col_select_col2:
                min_entries = st.number_input(
                    "Minimum entries:",
                    min_value=1,
                    max_value=1000,
                    value=10,
                    step=1,
                    key="min_entries_input",
                    help="Only include values with at least this many entries"
                )
            
            # Check if selected column exists
            if selected_column not in df.columns:
                st.error(f"❌ Error: '{selected_column}' column not found in the file.")
                st.info(f"Available columns: {', '.join(df.columns)}")
            else:
                # Display file info
                st.success(f"✅ Filtering by column: **{selected_column}** with minimum **{min_entries}** entries")
                
                # Show preview of data
                with st.expander("📋 Preview Data (First 10 rows)"):
                    st.dataframe(df.head(10))
                
                # Get unique values and their counts
                value_counts = df[selected_column].value_counts()
                
                # Filter values that meet minimum entry count
                filtered_values = value_counts[value_counts >= min_entries]
                num_filtered = len(filtered_values)
                num_total = len(value_counts)
                
                # Calculate statistics
                total_records_filtered = filtered_values.sum()
                total_records_excluded = value_counts[value_counts < min_entries].sum()
                
                # Show statistics
                st.markdown("---")
                st.subheader("📊 Filtering Statistics")
                
                stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
                with stat_col1:
                    st.metric("Total Unique Values", num_total)
                with stat_col2:
                    st.metric(f"Values with {min_entries}+ entries", num_filtered, 
                             delta=f"{num_filtered}/{num_total}")
                with stat_col3:
                    st.metric("Records Included", f"{total_records_filtered:,}",
                             delta=f"{(total_records_filtered/len(df)*100):.1f}%")
                with stat_col4:
                    st.metric("Records Excluded", f"{total_records_excluded:,}",
                             delta=f"{(total_records_excluded/len(df)*100):.1f}%")
                
                # Show detailed statistics
                with st.expander(f"📊 Detailed Statistics by {selected_column}"):
                    # Create stats dataframe
                    stats_data = []
                    for value, count in value_counts.items():
                        status = "✅ Included" if count >= min_entries else "❌ Excluded"
                        stats_data.append({
                            selected_column: value,
                            'Number of Records': count,
                            'Status': status
                        })
                    
                    stats_df = pd.DataFrame(stats_data)
                    stats_df = stats_df.sort_values('Number of Records', ascending=False)
                    
                    # Add amount column if it exists
                    amount_cols = [col for col in df.columns if 'amount' in col.lower() or 'value' in col.lower()]
                    if amount_cols:
                        for col in amount_cols:
                            if pd.api.types.is_numeric_dtype(df[col]):
                                amount_by_value = df.groupby(selected_column)[col].sum()
                                stats_df[f'Total {col}'] = stats_df[selected_column].map(amount_by_value)
                    
                    st.dataframe(stats_df, use_container_width=True, hide_index=True)
                
                if num_filtered == 0:
                    st.warning(f"⚠️ No values found with {min_entries}+ entries. Try lowering the minimum entry count.")
                else:
                    # Interactive deletion section
                    st.markdown("---")
                    st.subheader("🗑️ Remove Specific Values (Optional)")
                    st.markdown("Select values you want to **exclude** from the final output:")
                    
                    # Initialize session state for deleted values
                    if 'deleted_values' not in st.session_state:
                        st.session_state.deleted_values = set()
                    
                    # Get all unique values that meet the criteria
                    all_filtered_values = filtered_values.index.tolist()
                    
                    # Show statistics
                    remaining_values = [v for v in all_filtered_values if v not in st.session_state.deleted_values]
                    deleted_count = len(st.session_state.deleted_values)
                    
                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                    with col_stat1:
                        st.metric("Total Values", num_filtered)
                    with col_stat2:
                        st.metric("Excluded by You", deleted_count, delta=f"-{deleted_count}" if deleted_count > 0 else "0")
                    with col_stat3:
                        st.metric("Will be Included", len(remaining_values), delta=f"{len(remaining_values)}/{num_filtered}")
                    
                    # Create a dataframe for display with checkboxes
                    with st.expander(f"📋 View & Remove Values ({num_filtered} values with {min_entries}+ entries)", expanded=False):
                        # Create selection interface
                        st.markdown("**Select values to EXCLUDE from output:**")
                        
                        # Search box
                        search_term = st.text_input("🔍 Search values:", key="value_search", placeholder="Type to filter values...")
                        
                        # Filter values based on search
                        if search_term:
                            display_values = [v for v in all_filtered_values if search_term.lower() in str(v).lower()]
                        else:
                            display_values = all_filtered_values
                        
                        # Show count
                        st.caption(f"Showing {len(display_values)} of {num_filtered} values")
                        
                        # Create columns for better layout
                        col_select1, col_select2 = st.columns([3, 1])
                        
                        with col_select1:
                            # Multi-select for deletion
                            values_to_delete = st.multiselect(
                                "Select values to exclude:",
                                options=display_values,
                                default=[v for v in display_values if v in st.session_state.deleted_values],
                                key="values_to_delete_multiselect",
                                help="Select one or more values to exclude from the output"
                            )
                            
                            # Update session state
                            st.session_state.deleted_values = set(values_to_delete)
                        
                        with col_select2:
                            st.markdown("**Quick Actions:**")
                            
                            if st.button("🔄 Clear All Selections", use_container_width=True, key="clear_deletions"):
                                st.session_state.deleted_values = set()
                                st.rerun()
                            
                            if st.button("❌ Select All Visible", use_container_width=True, key="select_all_visible"):
                                st.session_state.deleted_values = set(display_values)
                                st.rerun()
                        
                        # Show detailed table with entry counts
                        if display_values:
                            st.markdown("---")
                            st.markdown("**Value Details:**")
                            
                            detail_data = []
                            for value in display_values:
                                count = filtered_values[value]
                                status = "❌ Excluded" if value in st.session_state.deleted_values else "✅ Included"
                                detail_data.append({
                                    'Status': status,
                                    selected_column: value,
                                    'Entry Count': count,
                                    'Percentage': f"{(count/len(df)*100):.2f}%"
                                })
                            
                            detail_df = pd.DataFrame(detail_data)
                            st.dataframe(detail_df, use_container_width=True, hide_index=True, height=400)
                    
                    # Calculate final statistics after deletions
                    final_values = [v for v in all_filtered_values if v not in st.session_state.deleted_values]
                    final_record_count = sum(filtered_values[v] for v in final_values) if final_values else 0
                    
                    if deleted_count > 0:
                        st.info(f"ℹ️ You have excluded {deleted_count} value(s). Final output will contain {len(final_values)} values with {final_record_count:,} records.")
                    
                    # Process buttons
                    st.markdown("---")
                    st.subheader("📥 Generate Output")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        process_single = st.button(
                            f"🔄 Generate Single Excel File ({len(final_values)} Sheets)", 
                            type="primary", 
                            use_container_width=True, 
                            key="entry_count_single",
                            disabled=(len(final_values) == 0)
                        )
                    
                    with col2:
                        process_separate = st.button(
                            f"📦 Generate Separate Files (ZIP - {len(final_values)} Files)", 
                            type="primary", 
                            use_container_width=True, 
                            key="entry_count_separate",
                            disabled=(len(final_values) == 0)
                        )
                    
                    with col3:
                        process_combined = st.button(
                            f"📄 Combined File (1 Sheet - {final_record_count:,} Records)", 
                            type="primary", 
                            use_container_width=True, 
                            key="entry_count_combined",
                            disabled=(len(final_values) == 0)
                        )
                    
                    # Process single Excel file with multiple sheets
                    if process_single:
                        with st.spinner(f"Processing file and creating sheets for {len(final_values)} values..."):
                            # Create Excel file in memory
                            output = io.BytesIO()
                            
                            # Create Excel writer
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                # Create a sheet for each final value (excluding deleted ones)
                                for value in final_values:
                                    # Filter data for this value
                                    value_df = df[df[selected_column] == value].copy()
                                    
                                    # Remove existing serial number columns
                                    sr_no_variations = ['Sr No', 'S No.', 'S.No', 'S No', 'Sr.No', 'Serial No', 'SNo', 'Sl No', 'Sl.No']
                                    for col in sr_no_variations:
                                        if col in value_df.columns:
                                            value_df = value_df.drop(columns=[col])
                                    
                                    # Add Sr No column starting from 1
                                    value_df.insert(0, 'Sr No', range(1, len(value_df) + 1))
                                    
                                    # Clean sheet name (Excel has 31 char limit)
                                    sheet_name = str(value)[:31]
                                    # Remove invalid characters
                                    invalid_chars = [':', '\\', '/', '?', '*', '[', ']']
                                    for char in invalid_chars:
                                        sheet_name = sheet_name.replace(char, '_')
                                    
                                    # Write to sheet
                                    value_df.to_excel(writer, sheet_name=sheet_name, index=False)
                                    
                                    # Auto-adjust column widths
                                    worksheet = writer.sheets[sheet_name]
                                    for idx, col in enumerate(value_df.columns):
                                        if idx < 26:  # Only first 26 columns (A-Z)
                                            max_length = max(
                                                value_df[col].astype(str).apply(len).max(),
                                                len(str(col))
                                            )
                                            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
                            
                            # Get the Excel file data
                            excel_data = output.getvalue()
                            
                            st.success(f"✅ Successfully created {len(final_values)} sheets!")
                            st.info(f"📊 Total records included: {final_record_count:,} out of {len(df):,}")
                            if deleted_count > 0:
                                st.warning(f"⚠️ Excluded {deleted_count} value(s) as per your selection")
                            
                            # Generate filename with timestamp
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"filtered_{selected_column.replace(' ', '_')}_min{min_entries}_{timestamp}.xlsx"
                            
                            # Download button
                            st.download_button(
                                label="⬇️ Download Single Excel File",
                                data=excel_data,
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                type="primary",
                                key="entry_count_download_single"
                            )
                    
                    # Process separate Excel files in ZIP
                    if process_separate:
                        with st.spinner(f"Creating separate Excel files for {len(final_values)} values..."):
                            # Create ZIP file in memory
                            zip_buffer = io.BytesIO()
                            
                            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                                # Create a separate Excel file for each final value (excluding deleted ones)
                                for value in final_values:
                                    # Filter data for this value
                                    value_df = df[df[selected_column] == value].copy()
                                    
                                    # Remove existing serial number columns
                                    sr_no_variations = ['Sr No', 'S No.', 'S.No', 'S No', 'Sr.No', 'Serial No', 'SNo', 'Sl No', 'Sl.No']
                                    for col in sr_no_variations:
                                        if col in value_df.columns:
                                            value_df = value_df.drop(columns=[col])
                                    
                                    # Add Sr No column starting from 1
                                    value_df.insert(0, 'Sr No', range(1, len(value_df) + 1))
                                    
                                    # Create Excel file in memory
                                    excel_buffer = io.BytesIO()
                                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                                        value_df.to_excel(writer, sheet_name='Data', index=False)
                                        
                                        # Auto-adjust column widths
                                        worksheet = writer.sheets['Data']
                                        for idx, col in enumerate(value_df.columns):
                                            if idx < 26:  # Only first 26 columns
                                                max_length = max(
                                                    value_df[col].astype(str).apply(len).max(),
                                                    len(str(col))
                                                )
                                                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
                                    
                                    # Clean filename
                                    clean_value_name = str(value)
                                    invalid_chars = [':', '\\', '/', '?', '*', '[', ']', '<', '>', '|', '"']
                                    for char in invalid_chars:
                                        clean_value_name = clean_value_name.replace(char, '_')
                                    
                                    # Add Excel file to ZIP
                                    filename = f"{clean_value_name}.xlsx"
                                    zip_file.writestr(filename, excel_buffer.getvalue())
                            
                            # Get the ZIP file data
                            zip_data = zip_buffer.getvalue()
                            
                            st.success(f"✅ Successfully created {len(final_values)} separate Excel files!")
                            st.info(f"📊 Total records included: {final_record_count:,} out of {len(df):,}")
                            if deleted_count > 0:
                                st.warning(f"⚠️ Excluded {deleted_count} value(s) as per your selection")
                            
                            # Generate filename with timestamp
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            zip_filename = f"filtered_{selected_column.replace(' ', '_')}_min{min_entries}_{timestamp}.zip"
                            
                            # Download button
                            st.download_button(
                                label="⬇️ Download ZIP File (Separate Files)",
                                data=zip_data,
                                file_name=zip_filename,
                                mime="application/zip",
                                type="primary",
                                key="entry_count_download_zip"
                            )
                    
                    # Process combined single sheet sorted by entry count
                    if process_combined:
                        with st.spinner(f"Creating single file with all filtered data sorted by entry count..."):
                            # Filter data to only include final values (excluding deleted ones)
                            filtered_df = df[df[selected_column].isin(final_values)].copy()
                            
                            # Create entry count column for sorting
                            entry_count_map = {v: filtered_values[v] for v in final_values}
                            filtered_df['_Entry_Count'] = filtered_df[selected_column].map(entry_count_map)
                            
                            # Sort by entry count (descending) then by selected column
                            filtered_df = filtered_df.sort_values(
                                by=['_Entry_Count', selected_column], 
                                ascending=[False, True]
                            )
                            
                            # Remove the temporary entry count column
                            filtered_df = filtered_df.drop(columns=['_Entry_Count'])
                            
                            # Remove existing serial number columns
                            sr_no_variations = ['Sr No', 'S No.', 'S.No', 'S No', 'Sr.No', 'Serial No', 'SNo', 'Sl No', 'Sl.No']
                            for col in sr_no_variations:
                                if col in filtered_df.columns:
                                    filtered_df = filtered_df.drop(columns=[col])
                            
                            # Add Sr No column starting from 1
                            filtered_df.insert(0, 'Sr No', range(1, len(filtered_df) + 1))
                            
                            # Create Excel file in memory
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                filtered_df.to_excel(writer, sheet_name='Filtered Data', index=False)
                                
                                # Auto-adjust column widths
                                worksheet = writer.sheets['Filtered Data']
                                for idx, col in enumerate(filtered_df.columns):
                                    if idx < 26:  # Only first 26 columns (A-Z)
                                        max_length = max(
                                            filtered_df[col].astype(str).apply(len).max(),
                                            len(str(col))
                                        )
                                        worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
                            
                            # Get the Excel file data
                            excel_data = output.getvalue()
                            
                            st.success(f"✅ Successfully created single file with all filtered data!")
                            st.info(f"📊 Total records: {len(filtered_df):,} (sorted by entry count for {selected_column})")
                            if deleted_count > 0:
                                st.warning(f"⚠️ Excluded {deleted_count} value(s) as per your selection")
                            
                            # Show top values
                            st.markdown("**Top values by entry count:**")
                            top_values_list = sorted([(v, filtered_values[v]) for v in final_values], key=lambda x: x[1], reverse=True)[:10]
                            for idx, (value, count) in enumerate(top_values_list, 1):
                                st.text(f"{idx}. {value}: {count:,} records")
                            
                            # Generate filename with timestamp
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"combined_filtered_{selected_column.replace(' ', '_')}_min{min_entries}_{timestamp}.xlsx"
                            
                            # Download button
                            st.download_button(
                                label="⬇️ Download Combined Excel File (1 Sheet)",
                                data=excel_data,
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                type="primary",
                                key="entry_count_download_combined"
                            )
        
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

    else:
        # Instructions when no file is uploaded
        st.info("👆 Please upload an Excel or CSV file to get started")
        
        with st.expander("ℹ️ Instructions"):
            st.markdown("""
            ### How to use this tool:
            
            1. **Upload** your Excel (.xlsx) or CSV (.csv) file
            2. **Select Column** - Choose which column to filter by (e.g., Bank Name, District)
            3. **Set Minimum Entries** - Enter the minimum number of entries required (e.g., 10, 15, 20)
            4. The app will show you:
               - How many values meet the criteria
               - How many records will be included/excluded
               - Detailed statistics for each value
            5. Choose your preferred output format:
               - **Single Excel File**: All filtered values in separate sheets
               - **Separate Files (ZIP)**: Individual Excel file for each filtered value
            6. **Download** the processed file(s)
            
            ### Use Cases:
            - **Banks with 10+ transactions**: Filter to only show banks with significant activity
            - **Districts with 15+ cases**: Focus on districts with higher case volumes
            - **ACKs with 5+ entries**: Find ACKs with multiple transactions
            - **States with 20+ records**: Analyze states with substantial data
            
            ### Features:
            - ✅ Supports both Excel (.xlsx) and CSV (.csv) files
            - ✅ Filter by ANY column with minimum entry count
            - ✅ Shows included vs excluded statistics
            - ✅ Preserves all original columns and data
            - ✅ Auto-adjusts column widths for readability
            - ✅ Adds Sr No column starting from 1 for each split
            - ✅ Two output options: Single file or separate files in ZIP
            - ✅ Handles special characters in names
            - ✅ Shows detailed statistics with amounts (if available)
            
            ### Examples:
            - **Bank Name with 10+ entries** → Only banks with 10 or more transactions
            - **District with 15+ entries** → Only districts with 15 or more cases
            - **ACK with 5+ entries** → Only ACKs with 5 or more related records
            - **State with 20+ entries** → Only states with 20 or more records
            
            ### Difference from "Split Data by Column":
            - **Split Data by Column**: Includes ALL values (no filtering)
            - **Filter by Entry Count**: Only includes values with minimum entry count
            
            ### For Gujarat State Cyber Crime Police:
            - Focus on high-volume cases
            - Identify banks with significant fraud activity
            - Prioritize districts with multiple cases
            - Filter out single-transaction entries
            """)

    # Footer
    st.markdown("---")
    st.markdown("🔢 Filter by Entry Count | Built with Streamlit")
