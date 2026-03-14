import streamlit as st
import pandas as pd
import io
from datetime import datetime
import zipfile
import os


def render_amount_matcher_page():
    """Render the Amount Matcher page - matches disputed amounts from ZIP file with main data."""
    
    st.title("💰 Match Remaining Amount with Disputed Amount")
    st.markdown("Upload a ZIP file containing bank-wise transaction Excel files and an Excel file with disputed amounts.")
    
    st.info("📌 This tool will merge all Excel files from ZIP (main transaction data), match them with disputed amounts file using Acknowledgement No. and Account No., and add disputed amounts to the output.")
    
    # File uploads
    st.markdown("### 📁 Upload Files")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 1️⃣ ZIP File (Main Transaction Data)")
        zip_file = st.file_uploader(
            "Upload ZIP file containing bank-wise Excel files",
            type=['zip'],
            help="ZIP file contains your main transaction data (bank-wise Excel files)",
            key="amount_matcher_zip"
        )
    
    with col2:
        st.markdown("#### 2️⃣ Excel File (Disputed Amounts)")
        disputed_file = st.file_uploader(
            "Upload Excel file with disputed amounts",
            type=['xlsx', 'xls'],
            help="Excel file containing Acknowledgement No., Account No., and Disputed Amount",
            key="amount_matcher_disputed"
        )
    
    if zip_file is not None and disputed_file is not None:
        try:
            # Step 1: Extract and merge all Excel files from ZIP (MAIN DATA)
            st.markdown("---")
            st.markdown("### 📦 Step 1: Extract and Merge ZIP Files (Main Transaction Data)")
            
            zip_data_frames = []
            
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                file_list = [f for f in zip_ref.namelist() if f.endswith(('.xlsx', '.xls')) and not f.startswith('__MACOSX')]
                
                st.info(f"📄 Found {len(file_list)} Excel files in ZIP")
                
                progress_bar = st.progress(0)
                for idx, file_name in enumerate(file_list):
                    with zip_ref.open(file_name) as excel_file:
                        df_temp = pd.read_excel(io.BytesIO(excel_file.read()))
                        zip_data_frames.append(df_temp)
                        st.text(f"✅ Loaded: {os.path.basename(file_name)} ({len(df_temp)} rows)")
                    progress_bar.progress((idx + 1) / len(file_list))
                
                progress_bar.empty()
                
                # Merge all dataframes from ZIP (THIS IS MAIN DATA)
                if zip_data_frames:
                    main_df = pd.concat(zip_data_frames, ignore_index=True)
                    st.success(f"✅ Merged {len(file_list)} files → Total {len(main_df):,} rows (Main Transaction Data)")
                    
                    # Show preview
                    with st.expander("👁️ Preview Main Transaction Data (First 10 rows)"):
                        st.dataframe(main_df.head(10))
                else:
                    st.error("❌ No valid Excel files found in ZIP")
                    return
            
            # Step 2: Load disputed amounts Excel file
            st.markdown("### 📊 Step 2: Load Disputed Amounts File")
            
            disputed_df = pd.read_excel(disputed_file)
            st.success(f"✅ Loaded disputed amounts file: {len(disputed_df):,} rows")
            
            with st.expander("👁️ Preview Disputed Amounts Data (First 10 rows)"):
                st.dataframe(disputed_df.head(10))
            
            # Step 3: Column Selection
            st.markdown("---")
            st.markdown("### 🎯 Step 3: Select Matching Columns")
            
            st.info("Select the columns to match between Main Data (ZIP) and Disputed Amounts file")
            
            col_sel1, col_sel2 = st.columns(2)
            
            with col_sel1:
                st.markdown("**From Main Data (ZIP - Merged):**")
                
                main_ack_col = st.selectbox(
                    "Acknowledgement No. column:",
                    options=["-- Select --"] + list(main_df.columns),
                    key="main_ack_col"
                )
                
                main_acc_col = st.selectbox(
                    "Account No. column:",
                    options=["-- Select --"] + list(main_df.columns),
                    key="main_acc_col"
                )
            
            with col_sel2:
                st.markdown("**From Disputed Amounts File:**")
                
                disputed_ack_col = st.selectbox(
                    "Acknowledgement No. column:",
                    options=["-- Select --"] + list(disputed_df.columns),
                    key="disputed_ack_col"
                )
                
                disputed_acc_col = st.selectbox(
                    "Account No. column:",
                    options=["-- Select --"] + list(disputed_df.columns),
                    key="disputed_acc_col"
                )
                
                disputed_amount_col = st.selectbox(
                    "Disputed Amount column:",
                    options=["-- Select --"] + list(disputed_df.columns),
                    key="disputed_amount_col"
                )
            
            # Optional: Additional columns from disputed amounts file
            st.markdown("---")
            st.markdown("### ➕ Optional: Additional Columns from Disputed Amounts File")
            
            additional_cols = st.multiselect(
                "Select any additional columns you want from Disputed Amounts file (optional):",
                options=[col for col in disputed_df.columns if col not in [disputed_ack_col, disputed_acc_col, disputed_amount_col]],
                key="additional_cols"
            )
            
            # Required columns from main file for output
            st.markdown("---")
            st.markdown("### 📋 Step 4: Select Output Columns from Main File")
            
            st.info("Select the columns you want in the final output (in order)")
            
            # Predefined output structure
            output_col1, output_col2, output_col3 = st.columns(3)
            
            with output_col1:
                complaint_date_col = st.selectbox(
                    "Complaint Date:",
                    options=["-- Skip --"] + list(main_df.columns),
                    key="complaint_date_col"
                )
                
                incident_date_col = st.selectbox(
                    "Incident Date:",
                    options=["-- Skip --"] + list(main_df.columns),
                    key="incident_date_col"
                )
                
                reported_amount_col = st.selectbox(
                    "Reported Amount:",
                    options=["-- Skip --"] + list(main_df.columns),
                    key="reported_amount_col"
                )
            
            with output_col2:
                pending_with_col = st.selectbox(
                    "Pending With Bank/FIs:",
                    options=["-- Skip --"] + list(main_df.columns),
                    key="pending_with_col"
                )
                
                transaction_id_col = st.selectbox(
                    "Transaction Id / UTR Number:",
                    options=["-- Skip --"] + list(main_df.columns),
                    key="transaction_id_col"
                )
                
                transaction_date_col = st.selectbox(
                    "Transaction Date:",
                    options=["-- Skip --"] + list(main_df.columns),
                    key="transaction_date_col"
                )
            
            with output_col3:
                transaction_amount_col = st.selectbox(
                    "Transaction Amount (Required):",
                    options=["-- Skip --"] + list(main_df.columns),
                    key="transaction_amount_col",
                    help="Required: Used as fallback when disputed amount not found"
                )
            
            # Validation
            if disputed_ack_col == "-- Select --" or disputed_acc_col == "-- Select --" or disputed_amount_col == "-- Select --":
                st.warning("⚠️ Please select Acknowledgement No., Account No., and Disputed Amount columns from Disputed Amounts file")
                return
            
            if main_ack_col == "-- Select --" or main_acc_col == "-- Select --":
                st.warning("⚠️ Please select Acknowledgement No. and Account No. columns from Main Data")
                return
            
            if transaction_amount_col == "-- Skip --":
                st.warning("⚠️ Please select Transaction Amount column (required for fallback when disputed amount not found)")
                return
            
            # Step 5: Match and Process
            st.markdown("---")
            
            if st.button("🔄 Match and Generate Output", type="primary", use_container_width=True, key="match_amounts"):
                status_placeholder = st.empty()
                
                status_placeholder.info("⏳ Processing... Please wait")
                
                # Create a copy of main dataframe (from ZIP)
                result_df = main_df.copy()
                
                # Normalize column names for matching (strip spaces, convert to string)
                result_df[main_ack_col] = result_df[main_ack_col].astype(str).str.strip()
                result_df[main_acc_col] = result_df[main_acc_col].astype(str).str.strip()
                
                disputed_df[disputed_ack_col] = disputed_df[disputed_ack_col].astype(str).str.strip()
                disputed_df[disputed_acc_col] = disputed_df[disputed_acc_col].astype(str).str.strip()
                
                # Create matching keys
                result_df['_match_key'] = result_df[main_ack_col] + "_" + result_df[main_acc_col]
                disputed_df['_match_key'] = disputed_df[disputed_ack_col] + "_" + disputed_df[disputed_acc_col]
                
                # Create a dictionary for fast lookup from disputed amounts file
                disputed_lookup = {}
                for _, row in disputed_df.iterrows():
                    key = row['_match_key']
                    if key not in disputed_lookup:
                        disputed_lookup[key] = {
                            'disputed_amount': row[disputed_amount_col]
                        }
                        # Add additional columns if selected
                        for add_col in additional_cols:
                            disputed_lookup[key][add_col] = row[add_col]
                
                # Match and add disputed amount
                matched_count = 0
                unmatched_count = 0
                disputed_amounts = []
                additional_data = {col: [] for col in additional_cols}
                
                for _, row in result_df.iterrows():
                    key = row['_match_key']
                    if key in disputed_lookup:
                        # Match found - use disputed amount from file
                        disputed_amounts.append(disputed_lookup[key]['disputed_amount'])
                        matched_count += 1
                        
                        # Add additional columns
                        for add_col in additional_cols:
                            additional_data[add_col].append(disputed_lookup[key].get(add_col, ''))
                    else:
                        # No match found - use transaction amount as fallback
                        fallback_amount = row[transaction_amount_col]
                        disputed_amounts.append(fallback_amount)
                        unmatched_count += 1
                        
                        for add_col in additional_cols:
                            additional_data[add_col].append('')
                
                result_df['Disputed Amount'] = disputed_amounts
                
                # Add additional columns to result
                for add_col in additional_cols:
                    result_df[f'{add_col} (from Disputed File)'] = additional_data[add_col]
                
                # Build final output dataframe with selected columns
                output_columns = []
                output_mapping = {}
                
                # Add Sr No
                output_columns.append('S No.')
                
                # Add Acknowledgement No
                output_columns.append('Acknowledgement No.')
                output_mapping['Acknowledgement No.'] = main_ack_col
                
                # Add optional columns
                if complaint_date_col != "-- Skip --":
                    output_columns.append('Complaint Date')
                    output_mapping['Complaint Date'] = complaint_date_col
                
                if incident_date_col != "-- Skip --":
                    output_columns.append('Incident Date')
                    output_mapping['Incident Date'] = incident_date_col
                
                if reported_amount_col != "-- Skip --":
                    output_columns.append('Reported Amount')
                    output_mapping['Reported Amount'] = reported_amount_col
                
                if pending_with_col != "-- Skip --":
                    output_columns.append('Pending With Bank/FIs')
                    output_mapping['Pending With Bank/FIs'] = pending_with_col
                
                # Add Account No
                output_columns.append('Account No')
                output_mapping['Account No'] = main_acc_col
                
                if transaction_id_col != "-- Skip --":
                    output_columns.append('Transaction Id / UTR Number')
                    output_mapping['Transaction Id / UTR Number'] = transaction_id_col
                
                if transaction_date_col != "-- Skip --":
                    output_columns.append('Transaction Date')
                    output_mapping['Transaction Date'] = transaction_date_col
                
                if transaction_amount_col != "-- Skip --":
                    output_columns.append('Transaction Amount')
                    output_mapping['Transaction Amount'] = transaction_amount_col
                
                # Add Disputed Amount
                output_columns.append('Disputed Amount')
                
                # Add additional columns from disputed file
                for add_col in additional_cols:
                    output_columns.append(f'{add_col} (from Disputed File)')
                
                # Create final output dataframe
                final_df = pd.DataFrame()
                
                # Add S No
                final_df['S No.'] = range(1, len(result_df) + 1)
                
                # Map columns
                for out_col, src_col in output_mapping.items():
                    final_df[out_col] = result_df[src_col]
                
                # Add Disputed Amount
                final_df['Disputed Amount'] = result_df['Disputed Amount']
                
                # Add additional columns
                for add_col in additional_cols:
                    final_df[f'{add_col} (from Disputed File)'] = result_df[f'{add_col} (from Disputed File)']
                
                st.session_state.amount_matcher_result = final_df
                st.session_state.amount_matcher_stats = {
                    'total_rows': len(result_df),
                    'matched_rows': matched_count,
                    'unmatched_rows': unmatched_count
                }
                
                status_placeholder.empty()
                st.success(f"✅ Matching complete! {matched_count} matched, {unmatched_count} used transaction amount as fallback")
            
            # Display results
            if 'amount_matcher_result' in st.session_state and st.session_state.amount_matcher_result is not None:
                final_df = st.session_state.amount_matcher_result
                stats = st.session_state.amount_matcher_stats
                
                st.markdown("---")
                st.markdown("### 📊 Results")
                
                # Statistics
                stat_col1, stat_col2, stat_col3 = st.columns(3)
                with stat_col1:
                    st.metric("Total Rows", f"{stats['total_rows']:,}")
                with stat_col2:
                    st.metric("Matched (Disputed Amount)", f"{stats['matched_rows']:,}", delta=f"{(stats['matched_rows']/stats['total_rows']*100):.1f}%")
                with stat_col3:
                    st.metric("Fallback (Transaction Amount)", f"{stats['unmatched_rows']:,}", delta=f"{(stats['unmatched_rows']/stats['total_rows']*100):.1f}%")
                
                st.info(f"ℹ️ **Note:** {stats['matched_rows']:,} rows found disputed amount from file. {stats['unmatched_rows']:,} rows used transaction amount as disputed amount (no match found).")
                
                # Preview
                st.markdown("### 👁️ Preview Output")
                st.dataframe(final_df.head(20), use_container_width=True)
                
                # Download
                st.markdown("---")
                st.markdown("### 📥 Download Matched Data")
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                dl_col1, dl_col2 = st.columns(2)
                
                with dl_col1:
                    # Excel download
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        final_df.to_excel(writer, sheet_name='Matched Data', index=False)
                        
                        # Auto-adjust column widths
                        worksheet = writer.sheets['Matched Data']
                        for idx, col in enumerate(final_df.columns):
                            max_length = max(
                                final_df[col].astype(str).apply(len).max(),
                                len(str(col))
                            )
                            col_letter = chr(65 + idx) if idx < 26 else f"A{chr(65 + idx - 26)}"
                            worksheet.column_dimensions[col_letter].width = min(max_length + 2, 50)
                    
                    excel_data = excel_buffer.getvalue()
                    
                    st.download_button(
                        label=f"⬇️ Download Excel ({len(final_df):,} rows)",
                        data=excel_data,
                        file_name=f"matched_disputed_amounts_{timestamp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="download_matched_excel"
                    )
                
                with dl_col2:
                    # CSV download
                    csv_data = final_df.to_csv(index=False).encode('utf-8')
                    
                    st.download_button(
                        label=f"⬇️ Download CSV ({len(final_df):,} rows)",
                        data=csv_data,
                        file_name=f"matched_disputed_amounts_{timestamp}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key="download_matched_csv"
                    )
        
        except Exception as e:
            st.error(f"❌ Error processing files: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    
    else:
        # Instructions
        st.info("👆 Please upload both files to get started")
        
        with st.expander("ℹ️ Instructions"):
            st.markdown("""
            ### How to use this tool:
            
            1. **Upload ZIP File**: Contains multiple Excel files (bank-wise transaction data) - THIS IS YOUR MAIN DATA
            2. **Upload Excel File**: Contains disputed amounts with Acknowledgement No. and Account No.
            3. **Select Matching Columns**:
               - Acknowledgement No. (from both files)
               - Account No. (from both files)
               - Disputed Amount (from Excel file)
            4. **Select Output Columns**: Choose which columns you want in the final output
            5. **Optional**: Select additional columns from disputed amounts file if needed
            6. **Click Match**: Tool will match records and add disputed amounts
            7. **Download**: Get the matched data in Excel or CSV format
            
            ### Matching Logic:
            - Main data comes from ZIP file (merged bank-wise Excel files)
            - Disputed amounts come from single Excel file
            - Records are matched using **both** Acknowledgement No. AND Account No.
            - Both must match for disputed amount to be added
            - **If no match found**: Transaction amount is used as disputed amount (fallback)
            - **No blank disputed amounts**: All rows will have a disputed amount value
            
            ### Output Format:
            - S No. (auto-generated)
            - Acknowledgement No. (from main data)
            - Complaint Date (optional, from main data)
            - Incident Date (optional, from main data)
            - Reported Amount (optional, from main data)
            - Pending With Bank/FIs (optional, from main data)
            - Account No (from main data)
            - Transaction Id / UTR Number (optional, from main data)
            - Transaction Date (optional, from main data)
            - Transaction Amount (optional, from main data)
            - Disputed Amount (matched from Excel file)
            - Additional columns (if selected from Excel file)
            
            ### Features:
            - ✅ Handles ZIP files with multiple Excel files (main transaction data)
            - ✅ Merges all Excel files automatically
            - ✅ Matches using two keys (Ack No. + Account No.)
            - ✅ Flexible column selection
            - ✅ Optional additional columns from disputed amounts file
            - ✅ Shows match statistics
            - ✅ Download in Excel or CSV format
            """)
    
    # Footer
    st.markdown("---")
    st.markdown("💰 Amount Matcher | Built with Streamlit")
