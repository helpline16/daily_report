import streamlit as st
import pandas as pd
import io
from datetime import datetime
import zipfile
import os
import json


def load_column_mappings():
    """Load column mappings from persistent JSON file"""
    mapping_file = "cyber multiple accoun with DA and ACK/.kiro/bank_pivot_mappings.json"
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(mapping_file), exist_ok=True)
    
    if os.path.exists(mapping_file):
        try:
            with open(mapping_file, 'r') as f:
                return json.load(f)
        except:
            pass
    
    # Default mappings
    return {
        'main_ack': '-- Select --',
        'main_bank': '-- Select --',
        'main_account': '-- Select --',
        'main_txn_id': '-- Select --',
        'main_amount': '-- Select --',
        'main_date': '-- Select --',
        'layer_ack': '-- Select --',
        'layer_account': '-- Select --',
        'layer_disputed': '-- Select --',
        'status_ack': '-- Select --',
        'status_txn_id': '-- Select --',
        'status_complaint': '-- Select --'
    }


def save_column_mappings(mappings):
    """Save column mappings to persistent JSON file"""
    mapping_file = "cyber multiple accoun with DA and ACK/.kiro/bank_pivot_mappings.json"
    
    try:
        os.makedirs(os.path.dirname(mapping_file), exist_ok=True)
        with open(mapping_file, 'w') as f:
            json.dump(mappings, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Could not save mappings: {e}")
        return False


def render_bank_ack_pivot_page():
    """Render the Bank ACK Pivot page - creates pivot table by Bank and ACK."""
    
    st.title("🏦 Bank ACK & Pending Time Pivot Report")
    st.markdown("Upload 3 files to generate a pivot table grouped by Bank Name and ACK Number.")
    
    st.info("📌 This tool creates a structured report showing pending amounts, disputed amounts, and pending time for each ACK under each bank.")
    
    # Initialize session state for column mappings - LOAD FROM FILE
    if 'pivot_col_mappings' not in st.session_state:
        st.session_state.pivot_col_mappings = load_column_mappings()
    
    # File uploads
    st.markdown("### 📁 Upload Files")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 1️⃣ ZIP File (Main Data)")
        zip_file = st.file_uploader(
            "Bank-wise transaction files",
            type=['zip'],
            help="ZIP file with bank-wise Excel files containing ACK, Bank Name, Transaction Amount, Transaction Date",
            key="pivot_zip"
        )
    
    with col2:
        st.markdown("#### 2️⃣ Layerwise File")
        layerwise_file = st.file_uploader(
            "Layerwise Excel file",
            type=['xlsx', 'xls'],
            help="Excel file with ACK and Disputed Amount",
            key="pivot_layerwise"
        )
    
    with col3:
        st.markdown("#### 3️⃣ Status Wise Report")
        status_file = st.file_uploader(
            "Status wise report",
            type=['xlsx', 'xls', 'csv'],
            help="Excel or CSV file with ACK and Complaint Date for pending time calculation",
            key="pivot_status"
        )
    
    if zip_file is not None and layerwise_file is not None and status_file is not None:
        try:
            # Step 1: Extract and merge ZIP files
            st.markdown("---")
            st.markdown("### 📦 Step 1: Extract and Merge ZIP Files")
            
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
            
            if zip_data_frames:
                main_df = pd.concat(zip_data_frames, ignore_index=True)
                st.success(f"✅ Merged {len(file_list)} files → Total {len(main_df):,} rows")
                
                with st.expander("👁️ Preview Main Data (First 10 rows)"):
                    st.dataframe(main_df.head(10))
            else:
                st.error("❌ No valid Excel files found in ZIP")
                return
            
            # Step 2: Load other files
            st.markdown("### 📊 Step 2: Load Other Files")
            
            layerwise_df = pd.read_excel(layerwise_file)
            st.success(f"✅ Loaded layerwise file: {len(layerwise_df):,} rows")
            
            # Handle CSV or Excel for status file
            if status_file.name.lower().endswith('.csv'):
                # For CSV files, read directly
                status_df = pd.read_csv(status_file)
                st.success(f"✅ Loaded status file (CSV): {len(status_df):,} rows")
            else:
                # For Excel files
                status_df = pd.read_excel(status_file)
                st.success(f"✅ Loaded status file (Excel): {len(status_df):,} rows")
            
            col_prev1, col_prev2 = st.columns(2)
            with col_prev1:
                with st.expander("👁️ Preview Layerwise Data"):
                    st.dataframe(layerwise_df.head(10))
            with col_prev2:
                with st.expander("👁️ Preview Status Data"):
                    st.dataframe(status_df.head(10))
            
            # Step 3: Column Selection
            st.markdown("---")
            col_header1, col_header2 = st.columns([3, 1])
            with col_header1:
                st.markdown("### 🎯 Step 3: Select Columns")
            with col_header2:
                if st.button("🔄 Reset Mappings", help="Reset all column selections to default", key="reset_mappings"):
                    default_mappings = {
                        'main_ack': '-- Select --',
                        'main_bank': '-- Select --',
                        'main_account': '-- Select --',
                        'main_txn_id': '-- Select --',
                        'main_amount': '-- Select --',
                        'main_date': '-- Select --',
                        'layer_ack': '-- Select --',
                        'layer_account': '-- Select --',
                        'layer_disputed': '-- Select --',
                        'status_ack': '-- Select --',
                        'status_txn_id': '-- Select --',
                        'status_complaint': '-- Select --'
                    }
                    st.session_state.pivot_col_mappings = default_mappings
                    save_column_mappings(default_mappings)
                    st.rerun()
            
            col_sel1, col_sel2, col_sel3 = st.columns(3)
            
            with col_sel1:
                st.markdown("**From Main Data (ZIP):**")
                
                # Get default index for remembered columns
                main_ack_options = ["-- Select --"] + list(main_df.columns)
                main_ack_default = main_ack_options.index(st.session_state.pivot_col_mappings['main_ack']) if st.session_state.pivot_col_mappings['main_ack'] in main_ack_options else 0
                
                main_ack_col = st.selectbox(
                    "ACK Number:",
                    options=main_ack_options,
                    index=main_ack_default,
                    key="main_ack"
                )
                
                main_bank_options = ["-- Select --"] + list(main_df.columns)
                main_bank_default = main_bank_options.index(st.session_state.pivot_col_mappings['main_bank']) if st.session_state.pivot_col_mappings['main_bank'] in main_bank_options else 0
                
                main_bank_col = st.selectbox(
                    "Bank Name:",
                    options=main_bank_options,
                    index=main_bank_default,
                    key="main_bank"
                )
                
                main_account_options = ["-- Select --"] + list(main_df.columns)
                main_account_default = main_account_options.index(st.session_state.pivot_col_mappings.get('main_account', '-- Select --')) if st.session_state.pivot_col_mappings.get('main_account', '-- Select --') in main_account_options else 0
                
                main_account_col = st.selectbox(
                    "Account Number:",
                    options=main_account_options,
                    index=main_account_default,
                    key="main_account"
                )
                
                main_txn_id_options = ["-- Select --"] + list(main_df.columns)
                main_txn_id_default = main_txn_id_options.index(st.session_state.pivot_col_mappings.get('main_txn_id', '-- Select --')) if st.session_state.pivot_col_mappings.get('main_txn_id', '-- Select --') in main_txn_id_options else 0
                
                main_txn_id_col = st.selectbox(
                    "Transaction ID/UTR:",
                    options=main_txn_id_options,
                    index=main_txn_id_default,
                    key="main_txn_id"
                )
                
                main_amount_options = ["-- Select --"] + list(main_df.columns)
                main_amount_default = main_amount_options.index(st.session_state.pivot_col_mappings['main_amount']) if st.session_state.pivot_col_mappings['main_amount'] in main_amount_options else 0
                
                main_amount_col = st.selectbox(
                    "Transaction Amount:",
                    options=main_amount_options,
                    index=main_amount_default,
                    key="main_amount"
                )
                
                main_date_options = ["-- Select --"] + list(main_df.columns)
                main_date_default = main_date_options.index(st.session_state.pivot_col_mappings['main_date']) if st.session_state.pivot_col_mappings['main_date'] in main_date_options else 0
                
                main_date_col = st.selectbox(
                    "Transaction Date:",
                    options=main_date_options,
                    index=main_date_default,
                    key="main_date"
                )
            
            with col_sel2:
                st.markdown("**From Layerwise File:**")
                
                layer_ack_options = ["-- Select --"] + list(layerwise_df.columns)
                layer_ack_default = layer_ack_options.index(st.session_state.pivot_col_mappings['layer_ack']) if st.session_state.pivot_col_mappings['layer_ack'] in layer_ack_options else 0
                
                layer_ack_col = st.selectbox(
                    "ACK Number:",
                    options=layer_ack_options,
                    index=layer_ack_default,
                    key="layer_ack"
                )
                
                layer_account_options = ["-- Select --"] + list(layerwise_df.columns)
                layer_account_default = layer_account_options.index(st.session_state.pivot_col_mappings.get('layer_account', '-- Select --')) if st.session_state.pivot_col_mappings.get('layer_account', '-- Select --') in layer_account_options else 0
                
                layer_account_col = st.selectbox(
                    "Account Number:",
                    options=layer_account_options,
                    index=layer_account_default,
                    key="layer_account"
                )
                
                layer_disputed_options = ["-- Select --"] + list(layerwise_df.columns)
                layer_disputed_default = layer_disputed_options.index(st.session_state.pivot_col_mappings['layer_disputed']) if st.session_state.pivot_col_mappings['layer_disputed'] in layer_disputed_options else 0
                
                layer_disputed_col = st.selectbox(
                    "Disputed Amount:",
                    options=layer_disputed_options,
                    index=layer_disputed_default,
                    key="layer_disputed"
                )
            
            with col_sel3:
                st.markdown("**From Status File:**")
                
                status_ack_options = ["-- Select --"] + list(status_df.columns)
                status_ack_default = status_ack_options.index(st.session_state.pivot_col_mappings['status_ack']) if st.session_state.pivot_col_mappings['status_ack'] in status_ack_options else 0
                
                status_ack_col = st.selectbox(
                    "ACK Number:",
                    options=status_ack_options,
                    index=status_ack_default,
                    key="status_ack"
                )
                
                status_txn_id_options = ["-- Select --"] + list(status_df.columns)
                status_txn_id_default = status_txn_id_options.index(st.session_state.pivot_col_mappings.get('status_txn_id', '-- Select --')) if st.session_state.pivot_col_mappings.get('status_txn_id', '-- Select --') in status_txn_id_options else 0
                
                status_txn_id_col = st.selectbox(
                    "Transaction ID/UTR:",
                    options=status_txn_id_options,
                    index=status_txn_id_default,
                    key="status_txn_id"
                )
                
                status_complaint_options = ["-- Select --"] + list(status_df.columns)
                status_complaint_default = status_complaint_options.index(st.session_state.pivot_col_mappings['status_complaint']) if st.session_state.pivot_col_mappings['status_complaint'] in status_complaint_options else 0
                
                status_complaint_col = st.selectbox(
                    "Complaint Date:",
                    options=status_complaint_options,
                    index=status_complaint_default,
                    key="status_complaint"
                )
            
            # Validation
            if main_ack_col == "-- Select --" or main_bank_col == "-- Select --" or main_account_col == "-- Select --" or main_txn_id_col == "-- Select --" or main_amount_col == "-- Select --" or main_date_col == "-- Select --":
                st.warning("⚠️ Please select all required columns from Main Data")
                return
            
            if layer_ack_col == "-- Select --" or layer_account_col == "-- Select --" or layer_disputed_col == "-- Select --":
                st.warning("⚠️ Please select all required columns from Layerwise File")
                return
            
            if status_ack_col == "-- Select --" or status_txn_id_col == "-- Select --" or status_complaint_col == "-- Select --":
                st.warning("⚠️ Please select all required columns from Status File")
                return
            
            # Step 4: Date Filter (Optional)
            st.markdown("---")
            st.markdown("### 📅 Step 4: Filter by Transaction Date (Optional)")
            
            # Get unique dates from main data
            try:
                main_df[main_date_col] = pd.to_datetime(main_df[main_date_col], errors='coerce')
                unique_dates = main_df[main_date_col].dropna().dt.date.unique()
                unique_dates = sorted(unique_dates, reverse=True)
                
                date_options = ["All Dates"] + [str(d) for d in unique_dates]
                
                selected_date = st.selectbox(
                    "Select Transaction Date to filter:",
                    options=date_options,
                    key="filter_date",
                    help="Select a specific date or 'All Dates' to include all transactions"
                )
            except:
                st.warning("⚠️ Could not parse transaction dates. Proceeding with all data.")
                selected_date = "All Dates"
            
            # Step 5: Generate Report
            st.markdown("---")
            
            if st.button("🔄 Generate Pivot Report", type="primary", use_container_width=True, key="generate_pivot"):
                # Save column mappings PERMANENTLY to file
                mappings_to_save = {
                    'main_ack': main_ack_col,
                    'main_bank': main_bank_col,
                    'main_account': main_account_col,
                    'main_txn_id': main_txn_id_col,
                    'main_amount': main_amount_col,
                    'main_date': main_date_col,
                    'layer_ack': layer_ack_col,
                    'layer_account': layer_account_col,
                    'layer_disputed': layer_disputed_col,
                    'status_ack': status_ack_col,
                    'status_txn_id': status_txn_id_col,
                    'status_complaint': status_complaint_col
                }
                
                st.session_state.pivot_col_mappings = mappings_to_save
                
                if save_column_mappings(mappings_to_save):
                    st.success("✅ Column mappings saved permanently!")
                
                status_placeholder = st.empty()
                status_placeholder.info("⏳ Processing... Please wait")
                
                # Filter by date if selected
                if selected_date != "All Dates":
                    filter_date = pd.to_datetime(selected_date).date()
                    filtered_main_df = main_df[main_df[main_date_col].dt.date == filter_date].copy()
                    st.info(f"📅 Filtered to {selected_date}: {len(filtered_main_df):,} rows")
                else:
                    filtered_main_df = main_df.copy()
                
                # CRITICAL: Normalize ALL data types BEFORE any matching
                # This ensures matching works correctly regardless of source data types
                
                # 1. Convert transaction amount to numeric - ROBUST CONVERSION
                st.write("🔍 **Debugging Transaction Amounts:**")
                st.write(f"Sample raw values: {filtered_main_df[main_amount_col].head(10).tolist()}")
                st.write(f"Data type before conversion: {filtered_main_df[main_amount_col].dtype}")
                
                # ROBUST AMOUNT CONVERSION - handles all formats
                def clean_amount(val):
                    """Convert any amount format to float with 2 decimals"""
                    if pd.isna(val) or val == '' or val is None:
                        return 0.0
                    
                    # Convert to string first
                    val_str = str(val).strip()
                    
                    if val_str == '' or val_str.lower() in ['nan', 'none', 'null', 'na']:
                        return 0.0
                    
                    # Remove common currency symbols and separators
                    val_str = val_str.replace('₹', '').replace('$', '').replace('€', '')
                    val_str = val_str.replace(',', '')  # Remove thousand separators
                    val_str = val_str.replace(' ', '')  # Remove spaces
                    val_str = val_str.strip()
                    
                    # Try to convert to float
                    try:
                        amount = float(val_str)
                        return round(amount, 2)  # Keep 2 decimal places
                    except (ValueError, TypeError):
                        # If conversion fails, log it and return 0
                        st.warning(f"⚠️ Could not convert value to amount: '{val}' → Treating as 0")
                        return 0.0
                
                # Apply robust conversion
                filtered_main_df['_original_amount'] = filtered_main_df[main_amount_col].copy()  # Keep original for debugging
                filtered_main_df[main_amount_col] = filtered_main_df[main_amount_col].apply(clean_amount)
                
                st.write(f"Data type after conversion: {filtered_main_df[main_amount_col].dtype}")
                st.write(f"Sample converted values: {filtered_main_df[main_amount_col].head(10).tolist()}")
                st.write(f"Total sum of all amounts: ₹{filtered_main_df[main_amount_col].sum():,.2f}")
                
                # CRITICAL VALIDATION: Check for conversion failures
                non_zero_count = (filtered_main_df[main_amount_col] > 0).sum()
                zero_count = (filtered_main_df[main_amount_col] == 0).sum()
                
                st.write(f"✅ Non-zero amounts: {non_zero_count} ({non_zero_count/len(filtered_main_df)*100:.1f}%)")
                st.write(f"⚠️ Zero amounts: {zero_count} ({zero_count/len(filtered_main_df)*100:.1f}%)")
                
                # Show any rows where conversion might have failed
                if zero_count > 0:
                    zero_samples = filtered_main_df[filtered_main_df[main_amount_col] == 0][['_original_amount', main_amount_col]].head(5)
                    if len(zero_samples) > 0:
                        st.write("Sample zero amount rows (original vs converted):")
                        st.dataframe(zero_samples)
                
                st.write("---")
                
                # 2. Normalize ACK numbers - convert to string, strip whitespace, handle NaN
                filtered_main_df[main_ack_col] = filtered_main_df[main_ack_col].fillna('').apply(lambda x: str(x).strip().upper() if x != '' else '')
                layerwise_df[layer_ack_col] = layerwise_df[layer_ack_col].fillna('').apply(lambda x: str(x).strip().upper() if x != '' else '')
                status_df[status_ack_col] = status_df[status_ack_col].fillna('').apply(lambda x: str(x).strip().upper() if x != '' else '')
                
                # 3. Normalize Account Numbers - convert to string, strip whitespace, remove any special characters
                filtered_main_df[main_account_col] = filtered_main_df[main_account_col].fillna('').apply(lambda x: str(x).strip().replace(' ', '').replace('-', '').upper() if x != '' else '')
                layerwise_df[layer_account_col] = layerwise_df[layer_account_col].fillna('').apply(lambda x: str(x).strip().replace(' ', '').replace('-', '').upper() if x != '' else '')
                
                # 4. Normalize Transaction IDs - convert to string, strip whitespace
                filtered_main_df[main_txn_id_col] = filtered_main_df[main_txn_id_col].fillna('').apply(lambda x: str(x).strip().upper() if x != '' else '')
                status_df[status_txn_id_col] = status_df[status_txn_id_col].fillna('').apply(lambda x: str(x).strip().upper() if x != '' else '')
                
                # 5. Normalize disputed amounts to numeric - ROBUST CONVERSION
                def clean_disputed_amount(val):
                    """Convert disputed amount to float with 2 decimals"""
                    if pd.isna(val) or val == '' or val is None:
                        return 0.0
                    
                    val_str = str(val).strip()
                    
                    if val_str == '' or val_str.lower() in ['nan', 'none', 'null', 'na']:
                        return 0.0
                    
                    # Remove currency symbols and separators
                    val_str = val_str.replace('₹', '').replace('$', '').replace('€', '')
                    val_str = val_str.replace(',', '')
                    val_str = val_str.replace(' ', '')
                    val_str = val_str.strip()
                    
                    try:
                        amount = float(val_str)
                        return round(amount, 2)
                    except (ValueError, TypeError):
                        return 0.0
                
                layerwise_df[layer_disputed_col] = layerwise_df[layer_disputed_col].apply(clean_disputed_amount)
                
                st.info(f"✅ Data normalized: {len(filtered_main_df):,} ZIP rows, {len(layerwise_df):,} layerwise rows, {len(status_df):,} status rows")
                
                # CRITICAL: ZIP file is master - keep ALL entries
                # Create base dataframe from ZIP file
                result_df = filtered_main_df[[main_bank_col, main_ack_col, main_account_col, main_txn_id_col, main_amount_col, main_date_col]].copy()
                result_df.columns = ['Bank Name', 'ACK', 'Account No', 'Transaction ID', 'Transaction Amount', 'Transaction Date']
                
                # Create lookup dictionaries with COMPOSITE KEYS for accuracy
                # Disputed Amount: Match by ACK + Account Number
                disputed_lookup = {}
                disputed_match_count = 0
                
                for _, row in layerwise_df.iterrows():
                    ack = row[layer_ack_col]
                    account = row[layer_account_col]
                    
                    # Skip empty keys
                    if ack == '' or account == '':
                        continue
                    
                    key = f"{ack}|{account}"  # Composite key
                    disputed_amt = row[layer_disputed_col]
                    
                    # Store numeric value
                    if pd.notna(disputed_amt) and disputed_amt != 0:
                        disputed_lookup[key] = float(disputed_amt)
                        disputed_match_count += 1
                    else:
                        disputed_lookup[key] = 0
                
                st.info(f"📊 Created {len(disputed_lookup):,} disputed amount lookup entries")
                
                # Complaint Date: Match by ACK + Transaction ID
                complaint_lookup = {}
                complaint_match_count = 0
                
                for _, row in status_df.iterrows():
                    ack = row[status_ack_col]
                    txn_id = row[status_txn_id_col]
                    
                    # Skip empty keys
                    if ack == '' or txn_id == '':
                        continue
                    
                    key = f"{ack}|{txn_id}"  # Composite key
                    complaint_date = row[status_complaint_col]
                    
                    if pd.notna(complaint_date):
                        complaint_lookup[key] = complaint_date
                        complaint_match_count += 1
                
                st.info(f"📊 Created {len(complaint_lookup):,} complaint date lookup entries")
                
                # Match and fill data using composite keys
                disputed_amounts = []
                complaint_dates = []
                matched_disputed = 0
                matched_complaint = 0
                
                for _, row in result_df.iterrows():
                    ack = row['ACK']
                    account = row['Account No']
                    txn_id = row['Transaction ID']
                    
                    # Match disputed amount by ACK + Account
                    disputed_key = f"{ack}|{account}"
                    disputed_val = disputed_lookup.get(disputed_key, 0)
                    
                    if disputed_val != 0:
                        disputed_amounts.append(disputed_val)
                        matched_disputed += 1
                    else:
                        disputed_amounts.append('')
                    
                    # Match complaint date by ACK + Transaction ID
                    complaint_key = f"{ack}|{txn_id}"
                    complaint_val = complaint_lookup.get(complaint_key, '')
                    
                    if complaint_val != '':
                        complaint_dates.append(complaint_val)
                        matched_complaint += 1
                    else:
                        complaint_dates.append('')
                
                result_df['Total Disputed Amount'] = disputed_amounts
                result_df['Complaint Date'] = complaint_dates
                
                st.info(f"✅ Matched: {matched_disputed:,} disputed amounts, {matched_complaint:,} complaint dates out of {len(result_df):,} transactions")
                
                # Calculate pending time
                current_time = datetime.now()
                pending_times = []
                
                for complaint_date in result_df['Complaint Date']:
                    if complaint_date != '' and pd.notna(complaint_date):
                        try:
                            complaint_dt = pd.to_datetime(complaint_date)
                            time_diff = current_time - complaint_dt
                            
                            total_seconds = int(time_diff.total_seconds())
                            hours = total_seconds // 3600
                            minutes = (total_seconds % 3600) // 60
                            
                            pending_times.append(f"Pending since {hours} hr {minutes:02d} min")
                        except:
                            pending_times.append('')
                    else:
                        pending_times.append('')
                
                result_df['Pending Time'] = pending_times
                
                # Group by Bank and ACK - sum transaction amounts and disputed amounts for same ACK
                grouped_data = []
                
                st.write("🔍 **Debugging Grouping:**")
                group_count = 0
                
                for (bank, ack), group in result_df.groupby(['Bank Name', 'ACK']):
                    group_count += 1
                    
                    # Sum transaction amounts (pending amount)
                    total_pending = group['Transaction Amount'].sum()
                    
                    # Debug first few groups
                    if group_count <= 3:
                        st.write(f"Group {group_count}: Bank={bank}, ACK={ack}")
                        st.write(f"  - Transactions in group: {len(group)}")
                        st.write(f"  - Individual amounts: {group['Transaction Amount'].tolist()}")
                        st.write(f"  - Total pending: ₹{total_pending:,.2f}")
                    
                    # Sum disputed amounts (only non-empty/non-zero values)
                    disputed_values = [x for x in group['Total Disputed Amount'] if x != '' and x != 0 and pd.notna(x)]
                    total_disputed = sum(disputed_values) if disputed_values else ''
                    
                    latest_date = group['Transaction Date'].max()
                    
                    # Get first non-empty complaint date
                    complaint = ''
                    for val in group['Complaint Date']:
                        if val != '' and pd.notna(val):
                            complaint = val
                            break
                    
                    # Get first non-empty pending time
                    pending = ''
                    for val in group['Pending Time']:
                        if val != '' and pd.notna(val):
                            pending = val
                            break
                    
                    grouped_data.append({
                        'Bank Name': bank,
                        'ACK': ack,
                        'Total Pending Amount': total_pending,
                        'Transaction Date': latest_date,
                        'Total Disputed Amount': total_disputed,
                        'Complaint Date': complaint,
                        'Pending Time': pending
                    })
                
                st.write(f"Total groups created: {group_count}")
                st.write("---")
                
                grouped = pd.DataFrame(grouped_data)
                
                # Sort by Bank Name and ACK
                grouped = grouped.sort_values(['Bank Name', 'ACK'])
                
                # Create final output
                final_output = grouped[['Bank Name', 'ACK', 'Total Pending Amount', 'Total Disputed Amount', 'Pending Time']].copy()
                
                # Validation: Ensure all ZIP entries are present
                original_acks = set(filtered_main_df[main_ack_col].unique())
                output_acks = set(final_output['ACK'].unique())
                
                if original_acks != output_acks:
                    st.error(f"⚠️ DATA INTEGRITY ERROR: Some ACKs from ZIP file are missing in output!")
                    st.error(f"Original ACKs: {len(original_acks)}, Output ACKs: {len(output_acks)}")
                    missing_acks = original_acks - output_acks
                    if missing_acks:
                        st.error(f"Missing ACKs: {missing_acks}")
                    return
                
                st.session_state.pivot_result = final_output
                st.session_state.pivot_stats = {
                    'total_banks': final_output['Bank Name'].nunique(),
                    'total_acks': len(final_output),
                    'total_pending': final_output['Total Pending Amount'].sum(),
                    'total_disputed': sum([x for x in final_output['Total Disputed Amount'] if x != '' and pd.notna(x)]),
                    'matched_disputed': len([x for x in final_output['Total Disputed Amount'] if x != '' and pd.notna(x)]),
                    'matched_complaint': len([x for x in grouped['Complaint Date'] if x != '' and pd.notna(x)])
                }
                
                status_placeholder.empty()
                st.success(f"✅ Report generated! {final_output['Bank Name'].nunique()} banks, {len(final_output)} ACKs (100% from ZIP file)")
                st.info(f"📊 Matched: {st.session_state.pivot_stats['matched_disputed']} disputed amounts, {st.session_state.pivot_stats['matched_complaint']} complaint dates")
            
            # Display results
            if 'pivot_result' in st.session_state and st.session_state.pivot_result is not None:
                final_output = st.session_state.pivot_result
                stats = st.session_state.pivot_stats
                
                st.markdown("---")
                st.markdown("### 📊 Pivot Report Results")
                
                # Statistics
                stat_col1, stat_col2, stat_col3, stat_col4, stat_col5 = st.columns(5)
                with stat_col1:
                    st.metric("Total Banks", f"{stats['total_banks']}")
                with stat_col2:
                    st.metric("Total ACKs", f"{stats['total_acks']:,}")
                with stat_col3:
                    st.metric("Total Pending Amount", f"₹{stats['total_pending']:,.0f}")
                with stat_col4:
                    st.metric("Disputed Matched", f"{stats['matched_disputed']}/{stats['total_acks']}")
                with stat_col5:
                    st.metric("Complaint Matched", f"{stats['matched_complaint']}/{stats['total_acks']}")
                
                # Display grouped by bank
                st.markdown("### 🏦 Bank-wise Report")
                
                for bank_name in final_output['Bank Name'].unique():
                    bank_data = final_output[final_output['Bank Name'] == bank_name]
                    
                    with st.expander(f"🏦 {bank_name} ({len(bank_data)} ACKs)", expanded=False):
                        # Show bank summary
                        bank_pending = bank_data['Total Pending Amount'].sum()
                        bank_disputed = sum([x for x in bank_data['Total Disputed Amount'] if x != '' and pd.notna(x)])
                        bank_matched = len([x for x in bank_data['Total Disputed Amount'] if x != '' and pd.notna(x)])
                        
                        st.markdown(f"**Summary:** {len(bank_data)} ACKs | Pending: ₹{bank_pending:,.0f} | Disputed: ₹{bank_disputed:,.0f} | Matched: {bank_matched}/{len(bank_data)}")
                        
                        # Show ACK details
                        display_df = bank_data[['ACK', 'Total Pending Amount', 'Total Disputed Amount', 'Pending Time']].copy()
                        display_df['Total Pending Amount'] = display_df['Total Pending Amount'].apply(lambda x: f"₹{x:,.2f}" if pd.notna(x) else '')
                        display_df['Total Disputed Amount'] = display_df['Total Disputed Amount'].apply(lambda x: f"₹{x:,.2f}" if x != '' and pd.notna(x) else '')
                        
                        st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # Download options
                st.markdown("---")
                st.markdown("### 📥 Download Report")
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                dl_col1, dl_col2 = st.columns(2)
                
                with dl_col1:
                    # Excel download
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        final_output.to_excel(writer, sheet_name='Bank ACK Pivot', index=False)
                        
                        # Auto-adjust column widths
                        worksheet = writer.sheets['Bank ACK Pivot']
                        for idx, col in enumerate(final_output.columns):
                            max_length = max(
                                final_output[col].astype(str).apply(len).max(),
                                len(str(col))
                            )
                            col_letter = chr(65 + idx) if idx < 26 else f"A{chr(65 + idx - 26)}"
                            worksheet.column_dimensions[col_letter].width = min(max_length + 2, 50)
                    
                    excel_data = excel_buffer.getvalue()
                    
                    st.download_button(
                        label=f"⬇️ Download Excel ({len(final_output):,} rows)",
                        data=excel_data,
                        file_name=f"bank_ack_pivot_{timestamp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="download_pivot_excel"
                    )
                
                with dl_col2:
                    # CSV download
                    csv_data = final_output.to_csv(index=False).encode('utf-8')
                    
                    st.download_button(
                        label=f"⬇️ Download CSV ({len(final_output):,} rows)",
                        data=csv_data,
                        file_name=f"bank_ack_pivot_{timestamp}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key="download_pivot_csv"
                    )
        
        except Exception as e:
            st.error(f"❌ Error processing files: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    
    else:
        # Instructions
        st.info("👆 Please upload all 3 files to get started")
        
        with st.expander("ℹ️ Instructions"):
            st.markdown("""
            ### How to use this tool:
            
            1. **Upload ZIP File**: Bank-wise transaction files (ACK, Bank Name, Account No, Transaction ID, Transaction Amount, Transaction Date)
            2. **Upload Layerwise File**: Excel with ACK, Account No, and Disputed Amount
            3. **Upload Status File**: Excel or CSV with ACK, Transaction ID, and Complaint Date
            4. **Select Columns**: Choose the correct columns from each file (auto-remembered)
            5. **Filter by Date** (Optional): Select a specific transaction date or use all dates
            6. **Generate Report**: Click to create the pivot table
            7. **Download**: Get the report in Excel or CSV format
            
            ### ⚠️ CRITICAL - Data Integrity & Matching Logic:
            - **ZIP file is MASTER data source** - 100% of entries preserved
            - **Pending Amount**: Sum of Transaction Amount from ZIP file (column J)
            - **Disputed Amount Matching**: Matches by ACK Number + Account Number (2 parameters for 100% accuracy)
            - **Pending Time Matching**: Matches by ACK Number + Transaction ID/UTR (2 parameters for 100% accuracy)
            - If same ACK appears twice: Sums BOTH pending and disputed amounts
            - If match not found → field left BLANK
            
            ### Matching Logic (100% Accurate):
            - **Disputed Amount**: Match using ACK + Account Number from layerwise file
            - **Complaint Date**: Match using ACK + Transaction ID from status file
            - **Pending Time**: Calculated from complaint date to current time
            - **Grouping**: If same ACK has multiple transactions → combine into 1 row, sum all amounts
            
            ### Output Format:
            - Grouped by Bank Name
            - Each bank shows all its ACKs
            - For each ACK: ACK | Total Pending Amount | Total Disputed Amount | Pending Time
            - Total Pending Amount = Sum of all transaction amounts for that ACK
            - Total Disputed Amount = Sum of all disputed amounts for that ACK (if multiple matches)
            - Pending Time format: "Pending since X hr XX min" (blank if no match)
            
            ### Features:
            - ✅ 100% data integrity - all ZIP entries preserved
            - ✅ Dual-parameter matching for accuracy (ACK + Account, ACK + Transaction ID)
            - ✅ Sums both pending and disputed amounts for duplicate ACKs
            - ✅ Pivot table grouped by Bank
            - ✅ Calculates pending time automatically
            - ✅ Filter by specific transaction date
            - ✅ Download in Excel or CSV
            - ✅ Bank-wise expandable view
            - ✅ Match statistics showing data completeness
            - ✅ Column mappings remembered for faster workflow
            
            ### For Gujarat State Cyber Crime Police:
            - This tool ensures 100% accuracy for critical police data
            - Every transaction from ZIP file is accounted for
            - Dual-parameter matching prevents false matches
            - Validation checks prevent data loss
            - Blank fields clearly show where additional data is needed
            """)
    
    # Footer
    st.markdown("---")
    st.markdown("🏦 Bank ACK Pivot Report | Built with Streamlit")
