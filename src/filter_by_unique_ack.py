import streamlit as st
import pandas as pd
import io
from datetime import datetime
import zipfile
from src.persistent_mapping import PersistentMapping


def render_filter_by_unique_ack_page():
    """Render the Filter by Unique ACK Count page - filters banks by unique ACK count."""
    
    # Initialize persistent mapping
    mapping = PersistentMapping('filter_by_unique_ack')
    
    # Title and description
    st.title("🏦 Filter Banks by Unique ACK Count")
    st.markdown("Upload a file and filter banks that have a minimum number of **unique ACK numbers** (e.g., only banks with 10+ unique ACKs)")

    # File upload - support both Excel and CSV
    uploaded_file = st.file_uploader(
        "Choose an Excel or CSV file",
        type=['xlsx', 'xls', 'csv'],
        help="Upload an Excel or CSV file to filter by unique ACK count",
        key="unique_ack_uploader"
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
            st.subheader("📋 Select Columns and Minimum Unique ACKs")
            
            # Show saved mappings indicator
            saved_count = mapping.get_saved_count()
            if saved_count > 0:
                st.success(f"✅ {saved_count} column mapping(s) remembered")
            
            available_columns = list(df.columns)
            
            # Column selection
            col_select_col1, col_select_col2, col_select_col3 = st.columns([2, 2, 1])
            
            with col_select_col1:
                # Get saved bank column or use default
                saved_bank_col = mapping.get('bank_column')
                default_bank_idx = 0
                
                # Priority columns for bank
                priority_bank_cols = ['Bank Name', 'Bank', 'Bank_Name', 'BankName', 'Action']
                for col in priority_bank_cols:
                    if col in available_columns:
                        default_bank_idx = available_columns.index(col)
                        break
                
                if saved_bank_col and saved_bank_col in available_columns:
                    default_bank_idx = available_columns.index(saved_bank_col)
                
                bank_column = st.selectbox(
                    "Bank Name Column:",
                    options=available_columns,
                    index=default_bank_idx,
                    key="bank_column_select",
                    help="Select the column containing bank names"
                )
                if bank_column:
                    mapping.set('bank_column', bank_column)
            
            with col_select_col2:
                # Get saved ACK column or use default
                saved_ack_col = mapping.get('ack_column')
                default_ack_idx = 0
                
                # Priority columns for ACK
                priority_ack_cols = ['Acknowledgement No', 'ACK No', 'ACK', 'Acknowledgement', 'ACK Number']
                for col in priority_ack_cols:
                    if col in available_columns:
                        default_ack_idx = available_columns.index(col)
                        break
                
                if saved_ack_col and saved_ack_col in available_columns:
                    default_ack_idx = available_columns.index(saved_ack_col)
                
                ack_column = st.selectbox(
                    "ACK Number Column:",
                    options=available_columns,
                    index=default_ack_idx,
                    key="ack_column_select",
                    help="Select the column containing ACK numbers"
                )
                if ack_column:
                    mapping.set('ack_column', ack_column)
            
            with col_select_col3:
                min_unique_acks = st.number_input(
                    "Min Unique ACKs:",
                    min_value=1,
                    max_value=1000,
                    value=10,
                    step=1,
                    key="min_unique_acks_input",
                    help="Minimum number of unique ACK numbers required"
                )
            
            # Check if selected columns exist
            if bank_column not in df.columns or ack_column not in df.columns:
                st.error(f"❌ Error: Selected columns not found in the file.")
                st.info(f"Available columns: {', '.join(df.columns)}")
            else:
                # Display file info
                st.success(f"✅ Filtering banks by **{min_unique_acks}+ unique ACKs** from column: **{ack_column}**")
                
                # Show preview of data
                with st.expander("📋 Preview Data (First 10 rows)"):
                    st.dataframe(df.head(10))
                
                # Calculate unique ACK counts per bank
                bank_stats = df.groupby(bank_column).agg({
                    ack_column: ['nunique', 'count']
                }).reset_index()
                
                bank_stats.columns = ['Bank', 'Unique_ACKs', 'Total_Records']
                
                # Sort alphabetically by bank name (A to Z)
                bank_stats = bank_stats.sort_values('Bank', ascending=True)
                
                # Filter banks that meet minimum unique ACK count
                qualified_banks = bank_stats[bank_stats['Unique_ACKs'] >= min_unique_acks]
                num_qualified = len(qualified_banks)
                num_total_banks = len(bank_stats)
                
                # Calculate statistics
                total_records_qualified = qualified_banks['Total_Records'].sum()
                total_records_excluded = bank_stats[bank_stats['Unique_ACKs'] < min_unique_acks]['Total_Records'].sum()
                
                # Show statistics
                st.markdown("---")
                st.subheader("📊 Filtering Statistics")
                
                stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
                with stat_col1:
                    st.metric("Total Banks", num_total_banks)
                with stat_col2:
                    st.metric(f"Banks with {min_unique_acks}+ Unique ACKs", num_qualified, 
                             delta=f"{num_qualified}/{num_total_banks}")
                with stat_col3:
                    st.metric("Records Included", f"{total_records_qualified:,}",
                             delta=f"{(total_records_qualified/len(df)*100):.1f}%")
                with stat_col4:
                    st.metric("Records Excluded", f"{total_records_excluded:,}",
                             delta=f"{(total_records_excluded/len(df)*100):.1f}%")
                
                # Show detailed statistics
                with st.expander(f"📊 Detailed Statistics by Bank (Sorted A-Z)"):
                    # Create stats dataframe
                    stats_data = []
                    for _, row in bank_stats.iterrows():
                        bank = row['Bank']
                        unique_acks = row['Unique_ACKs']
                        total_records = row['Total_Records']
                        
                        status = "✅ Qualified" if unique_acks >= min_unique_acks else "❌ Not Qualified"
                        stats_data.append({
                            'Bank Name': bank,
                            'Unique ACKs': unique_acks,
                            'Total Records': total_records,
                            'Status': status
                        })
                    
                    stats_df = pd.DataFrame(stats_data)
                    st.dataframe(stats_df, use_container_width=True, hide_index=True)
                
                if num_qualified == 0:
                    st.warning(f"⚠️ No banks found with {min_unique_acks}+ unique ACKs. Try lowering the minimum.")
                else:
                    # Interactive deletion section
                    st.markdown("---")
                    st.subheader("🗑️ Remove Specific Banks (Optional)")
                    st.markdown("Select banks you want to **exclude** from the final output:")
                    
                    # Initialize session state for deleted banks
                    if 'deleted_banks' not in st.session_state:
                        st.session_state.deleted_banks = set()
                    
                    # Get all qualified banks (sorted A-Z)
                    all_qualified_banks = qualified_banks['Bank'].tolist()
                    
                    # Show statistics
                    remaining_banks = [b for b in all_qualified_banks if b not in st.session_state.deleted_banks]
                    deleted_count = len(st.session_state.deleted_banks)
                    
                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                    with col_stat1:
                        st.metric("Qualified Banks", num_qualified)
                    with col_stat2:
                        st.metric("Excluded by You", deleted_count, delta=f"-{deleted_count}" if deleted_count > 0 else "0")
                    with col_stat3:
                        st.metric("Will be Included", len(remaining_banks), delta=f"{len(remaining_banks)}/{num_qualified}")
                    
                    # Create selection interface
                    with st.expander(f"📋 View & Remove Banks ({num_qualified} qualified banks, sorted A-Z)", expanded=False):
                        st.markdown("**Select banks to EXCLUDE from output:**")
                        
                        # Search box
                        search_term = st.text_input("🔍 Search banks:", key="bank_search", placeholder="Type to filter banks...")
                        
                        # Filter banks based on search
                        if search_term:
                            display_banks = [b for b in all_qualified_banks if search_term.lower() in str(b).lower()]
                        else:
                            display_banks = all_qualified_banks
                        
                        # Show count
                        st.caption(f"Showing {len(display_banks)} of {num_qualified} qualified banks (A-Z order)")
                        
                        # Create columns for better layout
                        col_select1, col_select2 = st.columns([3, 1])
                        
                        with col_select1:
                            # Multi-select for deletion
                            banks_to_delete = st.multiselect(
                                "Select banks to exclude:",
                                options=display_banks,
                                default=[b for b in display_banks if b in st.session_state.deleted_banks],
                                key="banks_to_delete_multiselect",
                                help="Select one or more banks to exclude from the output"
                            )
                            
                            # Update session state
                            st.session_state.deleted_banks = set(banks_to_delete)
                        
                        with col_select2:
                            st.markdown("**Quick Actions:**")
                            
                            if st.button("🔄 Clear All Selections", use_container_width=True, key="clear_bank_deletions"):
                                st.session_state.deleted_banks = set()
                                st.rerun()
                            
                            if st.button("❌ Select All Visible", use_container_width=True, key="select_all_banks_visible"):
                                st.session_state.deleted_banks = set(display_banks)
                                st.rerun()
                        
                        # Show detailed table
                        if display_banks:
                            st.markdown("---")
                            st.markdown("**Bank Details (A-Z):**")
                            
                            detail_data = []
                            for bank in display_banks:
                                bank_row = bank_stats[bank_stats['Bank'] == bank].iloc[0]
                                status = "❌ Excluded" if bank in st.session_state.deleted_banks else "✅ Included"
                                detail_data.append({
                                    'Status': status,
                                    'Bank Name': bank,
                                    'Unique ACKs': bank_row['Unique_ACKs'],
                                    'Total Records': bank_row['Total_Records']
                                })
                            
                            detail_df = pd.DataFrame(detail_data)
                            st.dataframe(detail_df, use_container_width=True, hide_index=True, height=400)
                    
                    # Calculate final statistics after deletions
                    final_banks = [b for b in all_qualified_banks if b not in st.session_state.deleted_banks]
                    final_record_count = bank_stats[bank_stats['Bank'].isin(final_banks)]['Total_Records'].sum() if final_banks else 0
                    
                    if deleted_count > 0:
                        st.info(f"ℹ️ You have excluded {deleted_count} bank(s). Final output will contain {len(final_banks)} banks with {final_record_count:,} records.")
                    
                    # Process buttons
                    st.markdown("---")
                    st.subheader("📥 Generate Output")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        process_single = st.button(
                            f"🔄 Generate Single Excel File ({len(final_banks)} Sheets)", 
                            type="primary", 
                            use_container_width=True, 
                            key="unique_ack_single",
                            disabled=(len(final_banks) == 0)
                        )
                    
                    with col2:
                        process_separate = st.button(
                            f"📦 Generate Separate Files (ZIP - {len(final_banks)} Files)", 
                            type="primary", 
                            use_container_width=True, 
                            key="unique_ack_separate",
                            disabled=(len(final_banks) == 0)
                        )
                    
                    with col3:
                        process_combined = st.button(
                            f"📄 Combined File (1 Sheet - {final_record_count:,} Records)", 
                            type="primary", 
                            use_container_width=True, 
                            key="unique_ack_combined",
                            disabled=(len(final_banks) == 0)
                        )
                    
                    # Process single Excel file with multiple sheets
                    if process_single:
                        with st.spinner(f"Processing file and creating sheets for {len(final_banks)} banks..."):
                            # Create Excel file in memory
                            output = io.BytesIO()
                            
                            # Create Excel writer
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                # Create a sheet for each final bank (excluding deleted ones)
                                for bank in final_banks:
                                    # Get ALL rows for this bank (including duplicate ACKs)
                                    bank_df = df[df[bank_column] == bank].copy()
                                    
                                    # Remove existing serial number columns
                                    sr_no_variations = ['Sr No', 'S No.', 'S.No', 'S No', 'Sr.No', 'Serial No', 'SNo', 'Sl No', 'Sl.No']
                                    for col in sr_no_variations:
                                        if col in bank_df.columns:
                                            bank_df = bank_df.drop(columns=[col])
                                    
                                    # Add Sr No column starting from 1
                                    bank_df.insert(0, 'Sr No', range(1, len(bank_df) + 1))
                                    
                                    # Clean sheet name (Excel has 31 char limit)
                                    sheet_name = str(bank)[:31]
                                    # Remove invalid characters
                                    invalid_chars = [':', '\\', '/', '?', '*', '[', ']']
                                    for char in invalid_chars:
                                        sheet_name = sheet_name.replace(char, '_')
                                    
                                    # Write to sheet
                                    bank_df.to_excel(writer, sheet_name=sheet_name, index=False)
                                    
                                    # Auto-adjust column widths
                                    worksheet = writer.sheets[sheet_name]
                                    for idx, col in enumerate(bank_df.columns):
                                        if idx < 26:  # Only first 26 columns (A-Z)
                                            max_length = max(
                                                bank_df[col].astype(str).apply(len).max(),
                                                len(str(col))
                                            )
                                            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
                            
                            # Get the Excel file data
                            excel_data = output.getvalue()
                            
                            st.success(f"✅ Successfully created {len(final_banks)} sheets!")
                            st.info(f"📊 Total records included: {final_record_count:,} out of {len(df):,}")
                            if deleted_count > 0:
                                st.warning(f"⚠️ Excluded {deleted_count} bank(s) as per your selection")
                            
                            # Generate filename with timestamp
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"banks_by_unique_ack_min{min_unique_acks}_{timestamp}.xlsx"
                            
                            # Download button
                            st.download_button(
                                label="⬇️ Download Single Excel File",
                                data=excel_data,
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                type="primary",
                                key="unique_ack_download_single"
                            )
                    
                    # Process separate Excel files in ZIP
                    if process_separate:
                        with st.spinner(f"Creating separate Excel files for {len(final_banks)} banks..."):
                            # Create ZIP file in memory
                            zip_buffer = io.BytesIO()
                            
                            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                                # Create a separate Excel file for each final bank
                                for bank in final_banks:
                                    # Get ALL rows for this bank (including duplicate ACKs)
                                    bank_df = df[df[bank_column] == bank].copy()
                                    
                                    # Remove existing serial number columns
                                    sr_no_variations = ['Sr No', 'S No.', 'S.No', 'S No', 'Sr.No', 'Serial No', 'SNo', 'Sl No', 'Sl.No']
                                    for col in sr_no_variations:
                                        if col in bank_df.columns:
                                            bank_df = bank_df.drop(columns=[col])
                                    
                                    # Add Sr No column starting from 1
                                    bank_df.insert(0, 'Sr No', range(1, len(bank_df) + 1))
                                    
                                    # Create Excel file in memory
                                    excel_buffer = io.BytesIO()
                                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                                        bank_df.to_excel(writer, sheet_name='Data', index=False)
                                        
                                        # Auto-adjust column widths
                                        worksheet = writer.sheets['Data']
                                        for idx, col in enumerate(bank_df.columns):
                                            if idx < 26:  # Only first 26 columns
                                                max_length = max(
                                                    bank_df[col].astype(str).apply(len).max(),
                                                    len(str(col))
                                                )
                                                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
                                    
                                    # Clean filename
                                    clean_bank_name = str(bank)
                                    invalid_chars = [':', '\\', '/', '?', '*', '[', ']', '<', '>', '|', '"']
                                    for char in invalid_chars:
                                        clean_bank_name = clean_bank_name.replace(char, '_')
                                    
                                    # Add Excel file to ZIP
                                    filename = f"{clean_bank_name}.xlsx"
                                    zip_file.writestr(filename, excel_buffer.getvalue())
                            
                            # Get the ZIP file data
                            zip_data = zip_buffer.getvalue()
                            
                            st.success(f"✅ Successfully created {len(final_banks)} separate Excel files!")
                            st.info(f"📊 Total records included: {final_record_count:,} out of {len(df):,}")
                            if deleted_count > 0:
                                st.warning(f"⚠️ Excluded {deleted_count} bank(s) as per your selection")
                            
                            # Generate filename with timestamp
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            zip_filename = f"banks_by_unique_ack_min{min_unique_acks}_{timestamp}.zip"
                            
                            # Download button
                            st.download_button(
                                label="⬇️ Download ZIP File (Separate Files)",
                                data=zip_data,
                                file_name=zip_filename,
                                mime="application/zip",
                                type="primary",
                                key="unique_ack_download_zip"
                            )
                    
                    # Process combined single sheet sorted by bank name (A-Z)
                    if process_combined:
                        with st.spinner(f"Creating single file with all data sorted by bank name..."):
                            # Filter data to only include final banks (excluding deleted ones)
                            filtered_df = df[df[bank_column].isin(final_banks)].copy()
                            
                            # Sort by bank name (A-Z)
                            filtered_df = filtered_df.sort_values(by=bank_column, ascending=True)
                            
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
                                filtered_df.to_excel(writer, sheet_name='All Banks Data', index=False)
                                
                                # Auto-adjust column widths
                                worksheet = writer.sheets['All Banks Data']
                                for idx, col in enumerate(filtered_df.columns):
                                    if idx < 26:  # Only first 26 columns (A-Z)
                                        max_length = max(
                                            filtered_df[col].astype(str).apply(len).max(),
                                            len(str(col))
                                        )
                                        worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
                            
                            # Get the Excel file data
                            excel_data = output.getvalue()
                            
                            st.success(f"✅ Successfully created single file with all data!")
                            st.info(f"📊 Total records: {len(filtered_df):,} from {len(final_banks)} banks (sorted A-Z)")
                            if deleted_count > 0:
                                st.warning(f"⚠️ Excluded {deleted_count} bank(s) as per your selection")
                            
                            # Show top banks
                            st.markdown("**Top 10 banks by unique ACK count:**")
                            top_banks = bank_stats[bank_stats['Bank'].isin(final_banks)].nlargest(10, 'Unique_ACKs')
                            for idx, row in enumerate(top_banks.itertuples(), 1):
                                st.text(f"{idx}. {row.Bank}: {row.Unique_ACKs} unique ACKs ({row.Total_Records:,} total records)")
                            
                            # Generate filename with timestamp
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"combined_banks_unique_ack_min{min_unique_acks}_{timestamp}.xlsx"
                            
                            # Download button
                            st.download_button(
                                label="⬇️ Download Combined Excel File (1 Sheet)",
                                data=excel_data,
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                type="primary",
                                key="unique_ack_download_combined"
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
            2. **Select Bank Column** - Choose the column containing bank names
            3. **Select ACK Column** - Choose the column containing ACK numbers
            4. **Set Minimum Unique ACKs** - Enter the minimum number of unique ACK numbers required
            5. The app will show you:
               - Which banks qualify (have enough unique ACKs)
               - Total records for each bank (including duplicate ACKs)
               - Detailed statistics sorted A-Z
            6. **Optional**: Manually exclude specific banks even if they qualify
            7. Choose your preferred output format:
               - **Single Excel File**: All qualified banks in separate sheets
               - **Separate Files (ZIP)**: Individual Excel file for each bank
               - **Combined File**: All data in one sheet, sorted by bank name (A-Z)
            8. **Download** the processed file(s)
            
            ### Key Logic:
            - **Filtering**: Banks qualify if they have >= minimum UNIQUE ACK numbers
            - **Output**: ALL records for qualified banks (including duplicate ACKs)
            - **Example**: Bank with 15 unique ACKs but 50 total rows → Include all 50 rows
            
            ### Use Cases:
            - **Banks with 10+ unique ACKs**: Focus on banks with multiple unique transactions
            - **Banks with 15+ unique ACKs**: Identify banks with significant fraud patterns
            - **Banks with 5+ unique ACKs**: Find banks with repeated fraud activity
            
            ### Features:
            - ✅ Filters by UNIQUE ACK count, outputs ALL records
            - ✅ Supports both Excel (.xlsx) and CSV (.csv) files
            - ✅ Shows qualified vs not qualified banks
            - ✅ Preserves all original columns and data
            - ✅ Auto-adjusts column widths for readability
            - ✅ Adds Sr No column starting from 1 for each split
            - ✅ Three output options: Single file, separate files, or combined
            - ✅ Handles special characters in bank names
            - ✅ Sorted A-Z for easy navigation
            - ✅ Manual exclusion of specific banks
            - ✅ Persistent column mapping (remembers your selections)
            
            ### Example Scenario:
            **Minimum Unique ACKs: 10**
            - Bank A: 15 unique ACKs, 50 total rows → ✅ QUALIFIES (include all 50 rows)
            - Bank B: 8 unique ACKs, 20 total rows → ❌ EXCLUDED (less than 10 unique ACKs)
            - Bank C: 12 unique ACKs, 12 total rows → ✅ QUALIFIES (include all 12 rows)
            
            ### For Gujarat State Cyber Crime Police:
            - Identify banks with multiple unique fraud cases
            - Focus on banks with repeated fraud patterns
            - Get complete data including duplicate ACKs for investigation
            - Easy A-Z sorting for quick reference
            """)

    # Footer
    st.markdown("---")
    st.markdown("🏦 Filter Banks by Unique ACK Count | Built with Streamlit")
