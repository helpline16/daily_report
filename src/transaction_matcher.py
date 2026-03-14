"""
Transaction Matcher Module - Match records by Transaction ID.

Features:
- Upload File 1 (Complaint Data) and File 2 (Bank Data)
- Extract Transaction ID from "Transaction ID" column (e.g., "Transaction Id :AXNPN35101489308" -> "AXNPN35101489308")
- Match by Transaction ID
- Add Account Number and Transaction Date from File 2 to File 1
- Optional Step 5: Match Disputed Amount by Acknowledgement No + Account No + Amount
- Persistent column mapping storage (remembers selections forever)
"""

import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import re
import json
import os
from pathlib import Path


# Persistent storage file path
MAPPINGS_FILE = Path.home() / '.kiro' / 'transaction_matcher_mappings.json'


def load_saved_mappings():
    """Load saved column mappings from file."""
    try:
        if MAPPINGS_FILE.exists():
            with open(MAPPINGS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        st.warning(f"Could not load saved mappings: {e}")
    
    return {
        'f1_txn_col': None,
        'f2_txn_col': None,
        'f2_account_col': None,
        'f2_date_col': None,
        'disp_r_ack_col': None,
        'disp_r_acc_col': None,
        'disp_r_amt_col': None,
        'disp_f3_ack_col': None,
        'disp_f3_acc_col': None,
        'disp_f3_amt_col': None,
        'disp_f3_disp_col': None
    }


def save_mappings(mappings):
    """Save column mappings to file."""
    try:
        # Create directory if it doesn't exist
        MAPPINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(MAPPINGS_FILE, 'w') as f:
            json.dump(mappings, f, indent=2)
    except Exception as e:
        st.warning(f"Could not save mappings: {e}")


def extract_bank_name(action_value):
    """
    Extract bank name from Action column.
    Example: "Money Transfer To :Bank of India" -> "Bank of India"
    Just removes "Money Transfer To :" prefix, keeps bank name as-is.
    """
    if pd.isna(action_value):
        return None
    
    action_str = str(action_value).strip()
    
    # Only remove "Money Transfer To :" prefix (case-insensitive)
    prefix = "Money Transfer To :"
    if action_str.lower().startswith(prefix.lower()):
        result = action_str[len(prefix):].strip()
    else:
        result = action_str
    
    return result.strip() if result else None


def extract_transaction_id(txn_value):
    """
    Extract transaction ID from Transaction ID column.
    Example: "Transaction Id :YESAP53372408503" -> "YESAP53372408503"
    Just removes "Transaction Id :" prefix, keeps ID as-is.
    """
    if pd.isna(txn_value):
        return None
    
    txn_str = str(txn_value).strip()
    
    # Only remove "Transaction Id :" prefix (case-insensitive)
    prefix = "Transaction Id :"
    if txn_str.lower().startswith(prefix.lower()):
        result = txn_str[len(prefix):].strip()
    else:
        result = txn_str
    
    return result.strip() if result else None


def normalize_bank_name(bank_name):
    """
    Normalize bank name for matching.
    Just trims whitespace and converts to uppercase for case-insensitive matching.
    """
    if pd.isna(bank_name) or bank_name is None:
        return None
    
    # Convert to string, uppercase, strip
    normalized = str(bank_name).upper().strip()
    
    return normalized if normalized else None


def normalize_transaction_id(txn_id):
    """
    Normalize transaction ID for matching.
    Just trims whitespace and converts to uppercase for case-insensitive matching.
    """
    if pd.isna(txn_id) or txn_id is None:
        return None
    
    # Convert to string, uppercase, strip
    normalized = str(txn_id).upper().strip()
    
    return normalized if normalized else None


def generate_excel_bytes(df: pd.DataFrame) -> bytes:
    """Generate Excel file bytes from DataFrame."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Matched Data')
    return output.getvalue()


def normalize_amount(amount_value):
    """
    Normalize amount for matching.
    Removes currency symbols, commas, and converts to float.
    """
    if pd.isna(amount_value) or amount_value is None:
        return None
    
    amount_str = str(amount_value).strip()
    
    # Remove currency symbols and common characters
    amount_str = amount_str.replace('₹', '').replace('Rs', '').replace('Rs.', '')
    amount_str = amount_str.replace('INR', '').replace(',', '').replace(' ', '')
    
    try:
        return float(amount_str)
    except:
        return None


def normalize_ack_number(ack_value):
    """
    Normalize acknowledgement number for matching.
    Converts to string, uppercase, strips whitespace.
    """
    if pd.isna(ack_value) or ack_value is None:
        return None
    
    normalized = str(ack_value).upper().strip()
    
    # Remove .0 if present (from float conversion)
    if normalized.endswith('.0'):
        normalized = normalized[:-2]
    
    return normalized if normalized else None


def normalize_account_number(acc_value):
    """
    Normalize account number for matching.
    Converts to string, strips whitespace, removes spaces/dashes.
    Also removes "Nodal Account" text if present.
    """
    if pd.isna(acc_value) or acc_value is None:
        return None
    
    normalized = str(acc_value).strip()
    
    # Remove .0 if present (from float conversion)
    if normalized.endswith('.0'):
        normalized = normalized[:-2]
    
    # Remove "Nodal Account" text (case-insensitive)
    # Example: "918020110872063   Nodal Account   " -> "918020110872063"
    if 'nodal account' in normalized.lower():
        # Split and take only the numeric part before "Nodal Account"
        parts = normalized.split()
        # Get the first part which should be the account number
        if parts:
            normalized = parts[0]
    
    # Remove spaces and dashes
    normalized = normalized.replace(' ', '').replace('-', '')
    
    return normalized if normalized else None


def render_transaction_matcher_page():
    """Render the Transaction Matcher page."""
    
    st.title("🔄 Transaction ID Matcher")
    st.markdown("""
    Match records from two files based on **Transaction ID**.
    - **File 1**: Pending/Unattended data with Transaction ID
    - **File 2**: Money Transfer data with Transaction ID, Account Number, and Transaction Date
    
    The output will add **Account Number** and **Transaction Date** from File 2 to File 1.
    """)
    
    # Initialize session state
    if 'txn_matcher_file1_df' not in st.session_state:
        st.session_state.txn_matcher_file1_df = None
    if 'txn_matcher_file2_df' not in st.session_state:
        st.session_state.txn_matcher_file2_df = None
    if 'txn_matcher_result_df' not in st.session_state:
        st.session_state.txn_matcher_result_df = None
    if 'txn_matcher_file3_df' not in st.session_state:
        st.session_state.txn_matcher_file3_df = None
    if 'txn_matcher_final_df' not in st.session_state:
        st.session_state.txn_matcher_final_df = None
    
    # Initialize persistent column mapping storage
    if 'txn_matcher_saved_mappings' not in st.session_state:
        # Load saved mappings from file
        st.session_state.txn_matcher_saved_mappings = load_saved_mappings()
    
    st.markdown("---")
    
    # File Upload Section
    st.header("📁 Step 1: Upload Files")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("File 1: Pending/Unattended")
        st.caption("Contains: S No., Acknowledgement No., State, District, Police Station, Sub Category, Bank Name, Transaction ID, Amount, Complaint Date, etc.")
        
        file1 = st.file_uploader(
            "Upload Pending/Unattended file(s) (Ctrl+Click for multiple)",
            type=['xlsx', 'xls', 'csv'],
            key='txn_matcher_file1',
            accept_multiple_files=True,
            help="Upload up to 50 Pending/Unattended files. They will be combined automatically."
        )
        
        if file1:
            try:
                if len(file1) > 50:
                    st.error("❌ Maximum 50 files allowed. Please remove some files.")
                else:
                    all_data = []
                    
                    # Show progress for multiple files
                    if len(file1) > 1:
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                    
                    for idx, uploaded_file in enumerate(file1):
                        if len(file1) > 1:
                            status_text.text(f"Reading file {idx+1}/{len(file1)}: {uploaded_file.name}...")
                            progress_bar.progress((idx + 1) / len(file1))
                        
                        if uploaded_file.name.endswith('.csv'):
                            df_temp = pd.read_csv(uploaded_file, dtype=str)
                        else:
                            df_temp = pd.read_excel(uploaded_file, dtype=str)
                        
                        all_data.append(df_temp)
                    
                    # Combine all files
                    if len(all_data) > 1:
                        combined_df = pd.concat(all_data, ignore_index=True)
                        st.session_state.txn_matcher_file1_df = combined_df
                        
                        if len(file1) > 1:
                            progress_bar.empty()
                            status_text.empty()
                        
                        st.success(f"✅ Combined {len(file1)} files: {len(combined_df):,} total records")
                        
                        # Show file breakdown
                        with st.expander("📋 Files Combined", expanded=False):
                            breakdown = []
                            for idx, (f, df) in enumerate(zip(file1, all_data), 1):
                                breakdown.append({
                                    'File #': idx,
                                    'Filename': f.name,
                                    'Records': len(df)
                                })
                            st.dataframe(pd.DataFrame(breakdown), use_container_width=True)
                    else:
                        st.session_state.txn_matcher_file1_df = all_data[0]
                        st.success(f"✅ Loaded {len(all_data[0]):,} records")
                    
                    with st.expander("Preview Combined Pending/Unattended Data", expanded=False):
                        st.dataframe(st.session_state.txn_matcher_file1_df.head(10), use_container_width=True)
                        
            except Exception as e:
                st.error(f"❌ Error reading files: {str(e)}")
    
    with col2:
        st.subheader("File 2: Money Transfer")
        st.caption("Contains: Action (Bank Name), Transaction ID, Account Number, Transaction Date")
        
        file2 = st.file_uploader(
            "Upload Money Transfer file(s) (Ctrl+Click for multiple)",
            type=['xlsx', 'xls', 'csv'],
            key='txn_matcher_file2',
            accept_multiple_files=True,
            help="Upload up to 50 Money Transfer files. They will be combined automatically."
        )
        
        if file2:
            try:
                if len(file2) > 50:
                    st.error("❌ Maximum 50 files allowed. Please remove some files.")
                else:
                    all_data = []
                    
                    # Show progress for multiple files
                    if len(file2) > 1:
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                    
                    for idx, uploaded_file in enumerate(file2):
                        if len(file2) > 1:
                            status_text.text(f"Reading file {idx+1}/{len(file2)}: {uploaded_file.name}...")
                            progress_bar.progress((idx + 1) / len(file2))
                        
                        if uploaded_file.name.endswith('.csv'):
                            df_temp = pd.read_csv(uploaded_file, dtype=str)
                        else:
                            df_temp = pd.read_excel(uploaded_file, dtype=str)
                        
                        all_data.append(df_temp)
                    
                    # Combine all files
                    if len(all_data) > 1:
                        combined_df = pd.concat(all_data, ignore_index=True)
                        st.session_state.txn_matcher_file2_df = combined_df
                        
                        if len(file2) > 1:
                            progress_bar.empty()
                            status_text.empty()
                        
                        st.success(f"✅ Combined {len(file2)} files: {len(combined_df):,} total records")
                        
                        # Show file breakdown
                        with st.expander("📋 Files Combined", expanded=False):
                            breakdown = []
                            for idx, (f, df) in enumerate(zip(file2, all_data), 1):
                                breakdown.append({
                                    'File #': idx,
                                    'Filename': f.name,
                                    'Records': len(df)
                                })
                            st.dataframe(pd.DataFrame(breakdown), use_container_width=True)
                    else:
                        st.session_state.txn_matcher_file2_df = all_data[0]
                        st.success(f"✅ Loaded {len(all_data[0]):,} records")
                    
                    with st.expander("Preview Combined Money Transfer Data", expanded=False):
                        st.dataframe(st.session_state.txn_matcher_file2_df.head(10), use_container_width=True)
                        
            except Exception as e:
                st.error(f"❌ Error reading files: {str(e)}")
    
    # Column Selection Section
    if st.session_state.txn_matcher_file1_df is not None and st.session_state.txn_matcher_file2_df is not None:
        st.markdown("---")
        st.header("🔧 Step 2: Select Columns")
        
        # Show saved mappings indicator
        saved_count = sum(1 for v in st.session_state.txn_matcher_saved_mappings.values() if v is not None)
        if saved_count > 0:
            st.success(f"✅ {saved_count} column mapping(s) remembered from previous session")
        
        file1_columns = ["-- Select Column --"] + st.session_state.txn_matcher_file1_df.columns.tolist()
        file2_columns = ["-- Select Column --"] + st.session_state.txn_matcher_file2_df.columns.tolist()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("File 1 Columns")
            
            # Get saved mapping or default
            saved_f1_txn = st.session_state.txn_matcher_saved_mappings.get('f1_txn_col')
            default_f1_txn_idx = 0
            if saved_f1_txn and saved_f1_txn in st.session_state.txn_matcher_file1_df.columns:
                default_f1_txn_idx = file1_columns.index(saved_f1_txn)
            
            f1_txn_col = st.selectbox(
                "Transaction ID Column",
                options=file1_columns,
                index=default_f1_txn_idx,
                key='txn_f1_txn_col',
                help="Column containing Transaction ID"
            )
            
            # Save the selection
            if f1_txn_col != "-- Select Column --":
                st.session_state.txn_matcher_saved_mappings['f1_txn_col'] = f1_txn_col
                save_mappings(st.session_state.txn_matcher_saved_mappings)
        
        with col2:
            st.subheader("File 2 Columns")
            
            # Get saved mappings or defaults
            saved_f2_txn = st.session_state.txn_matcher_saved_mappings.get('f2_txn_col')
            saved_f2_account = st.session_state.txn_matcher_saved_mappings.get('f2_account_col')
            saved_f2_date = st.session_state.txn_matcher_saved_mappings.get('f2_date_col')
            
            default_f2_txn_idx = 0
            if saved_f2_txn and saved_f2_txn in st.session_state.txn_matcher_file2_df.columns:
                default_f2_txn_idx = file2_columns.index(saved_f2_txn)
            
            default_f2_account_idx = 0
            if saved_f2_account and saved_f2_account in st.session_state.txn_matcher_file2_df.columns:
                default_f2_account_idx = file2_columns.index(saved_f2_account)
            
            default_f2_date_idx = 0
            if saved_f2_date and saved_f2_date in st.session_state.txn_matcher_file2_df.columns:
                default_f2_date_idx = file2_columns.index(saved_f2_date)
            
            f2_txn_col = st.selectbox(
                "Transaction ID Column",
                options=file2_columns,
                index=default_f2_txn_idx,
                key='txn_f2_txn_col',
                help="Column containing Transaction ID (e.g., 'Transaction Id :YESAP53372408503')"
            )
            
            f2_account_col = st.selectbox(
                "Account Number Column",
                options=file2_columns,
                index=default_f2_account_idx,
                key='txn_f2_account_col',
                help="Column containing Account Number to add to File 1"
            )
            
            f2_date_col = st.selectbox(
                "Transaction Date Column",
                options=file2_columns,
                index=default_f2_date_idx,
                key='txn_f2_date_col',
                help="Column containing Transaction Date to add to File 1"
            )
            
            # Save the selections
            if f2_txn_col != "-- Select Column --":
                st.session_state.txn_matcher_saved_mappings['f2_txn_col'] = f2_txn_col
                save_mappings(st.session_state.txn_matcher_saved_mappings)
            if f2_account_col != "-- Select Column --":
                st.session_state.txn_matcher_saved_mappings['f2_account_col'] = f2_account_col
                save_mappings(st.session_state.txn_matcher_saved_mappings)
            if f2_date_col != "-- Select Column --":
                st.session_state.txn_matcher_saved_mappings['f2_date_col'] = f2_date_col
                save_mappings(st.session_state.txn_matcher_saved_mappings)
        
        # Validate selections
        all_selected = (
            f1_txn_col != "-- Select Column --" and
            f2_txn_col != "-- Select Column --" and
            f2_account_col != "-- Select Column --" and
            f2_date_col != "-- Select Column --"
        )
        
        if not all_selected:
            st.warning("⚠️ Please select all required columns")
        
        # Preview extracted data
        st.markdown("---")
        with st.expander("🔍 Preview Extracted Data (Verify Before Matching)", expanded=False):
            col_debug1, col_debug2 = st.columns(2)
            
            with col_debug1:
                st.write("**File 1 - Sample Transaction IDs:**")
                if f1_txn_col != "-- Select Column --":
                    sample_df1 = st.session_state.txn_matcher_file1_df[[f1_txn_col]].head(10).copy()
                    sample_df1['Normalized TxnID'] = sample_df1[f1_txn_col].apply(normalize_transaction_id)
                    st.dataframe(sample_df1, use_container_width=True)
            
            with col_debug2:
                st.write("**File 2 - Sample Extracted Data:**")
                if f2_txn_col != "-- Select Column --":
                    sample_df2 = st.session_state.txn_matcher_file2_df[[f2_txn_col]].head(10).copy()
                    sample_df2['Extracted TxnID'] = sample_df2[f2_txn_col].apply(extract_transaction_id)
                    sample_df2['Normalized TxnID'] = sample_df2['Extracted TxnID'].apply(normalize_transaction_id)
                    st.dataframe(sample_df2, use_container_width=True)
        
        # Process and Match Button
        st.markdown("---")
        st.header("🔄 Step 3: Match Records")
        
        if st.button("🚀 Match Records", type="primary", use_container_width=True, disabled=not all_selected):
            with st.spinner("Processing and matching data..."):
                try:
                    # Create working copies
                    df1 = st.session_state.txn_matcher_file1_df.copy()
                    df2 = st.session_state.txn_matcher_file2_df.copy()
                    
                    # Step 1: Normalize File 1 Transaction ID
                    df1['_norm_txn'] = df1[f1_txn_col].apply(normalize_transaction_id)
                    
                    # Step 2: Extract and normalize File 2 Transaction ID
                    df2['_extracted_txn'] = df2[f2_txn_col].apply(extract_transaction_id)
                    df2['_norm_txn'] = df2['_extracted_txn'].apply(normalize_transaction_id)
                    
                    # Step 3: Prepare File 2 for merge (keep only needed columns)
                    # Match ONLY by Transaction ID (not bank name)
                    df2_merge = df2[['_norm_txn', f2_account_col, f2_date_col]].copy()
                    df2_merge = df2_merge.rename(columns={
                        f2_account_col: 'ACCOUNT NO',
                        f2_date_col: 'TRANSACTION DATE'
                    })
                    
                    # Remove duplicates from File 2 (keep first)
                    df2_merge = df2_merge.drop_duplicates(subset=['_norm_txn'], keep='first')
                    
                    # Remove rows with empty transaction IDs
                    df2_merge = df2_merge[df2_merge['_norm_txn'].notna() & (df2_merge['_norm_txn'] != '')]
                    
                    # Step 4: Merge ONLY on Transaction ID
                    result_df = df1.merge(
                        df2_merge,
                        on=['_norm_txn'],
                        how='left'
                    )
                    
                    # Count matches
                    matched_count = result_df['ACCOUNT NO'].notna().sum()
                    total_count = len(result_df)
                    
                    # Step 5: Reorder columns as requested
                    # Original columns from File 1
                    original_cols = list(st.session_state.txn_matcher_file1_df.columns)
                    
                    # Find position of Transaction ID column
                    txn_col_index = original_cols.index(f1_txn_col) + 1
                    
                    # Build new column order
                    new_order = original_cols[:txn_col_index]  # Up to and including Transaction ID
                    new_order.append('ACCOUNT NO')
                    new_order.append('TRANSACTION DATE')
                    new_order.extend(original_cols[txn_col_index:])  # Rest of columns
                    
                    # Select and reorder columns (drop temp columns)
                    final_df = result_df[new_order].copy()
                    
                    # Fill empty values
                    final_df['ACCOUNT NO'] = final_df['ACCOUNT NO'].fillna('')
                    final_df['TRANSACTION DATE'] = final_df['TRANSACTION DATE'].fillna('')
                    
                    # Store result
                    st.session_state.txn_matcher_result_df = final_df
                    
                    # Display statistics
                    st.success(f"✅ Matching complete!")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Records", f"{total_count:,}")
                    with col2:
                        st.metric("Matched Records", f"{matched_count:,}")
                    with col3:
                        st.metric("Unmatched Records", f"{total_count - matched_count:,}")
                    with col4:
                        match_rate = (matched_count / total_count * 100) if total_count > 0 else 0
                        st.metric("Match Rate", f"{match_rate:.1f}%")
                    
                except Exception as e:
                    st.error(f"❌ Error during matching: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
        
        # Display results and download
        if st.session_state.txn_matcher_result_df is not None:
            st.markdown("---")
            st.header("📋 Step 4: Results")
            
            result_df = st.session_state.txn_matcher_result_df
            
            # Preview
            with st.expander("📋 Preview Results (First 100 rows)", expanded=True):
                st.dataframe(result_df.head(100), use_container_width=True)
            
            # Download buttons
            st.subheader("📥 Download Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                excel_bytes = generate_excel_bytes(result_df)
                st.download_button(
                    label=f"📊 Download Excel ({len(result_df):,} rows)",
                    data=excel_bytes,
                    file_name=f"matched_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary"
                )
            
            with col2:
                csv_bytes = result_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"📄 Download CSV ({len(result_df):,} rows)",
                    data=csv_bytes,
                    file_name=f"matched_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            # Clear button
            st.markdown("---")
            if st.button("🔄 Clear & Start Over", use_container_width=True):
                st.session_state.txn_matcher_file1_df = None
                st.session_state.txn_matcher_file2_df = None
                st.session_state.txn_matcher_result_df = None
                st.session_state.txn_matcher_file3_df = None
                st.session_state.txn_matcher_final_df = None
                st.rerun()
            
            # ============== STEP 5: DISPUTED AMOUNT MATCHING ==============
            st.markdown("---")
            st.header("💰 Step 5: Match Disputed Amount (Optional)")
            st.markdown("""
            Upload a **Layerwise file** containing **Disputed Amount** data.
            
            **Main file:**
            - Keep **Pending/Unattended** as main and add Disputed Amount to it
            
            Matching will be done on **3 parameters**:
            1. Acknowledgement Number
            2. Account Number  
            3. Amount
            
            All 3 must match to add the Disputed Amount.
            """)
            
            # Use original as base
            use_money_transfer_as_main = False
            
            st.info("📋 **Pending/Unattended (Step 4 result)** will be the main file. Disputed Amount will be added to it.")
            
            st.markdown("---")
            
            # File 3 upload
            file3 = st.file_uploader(
                "Upload Layerwise file(s) (Disputed Amount) - Ctrl+Click for multiple",
                type=['xlsx', 'xls', 'csv'],
                key='txn_matcher_file3',
                accept_multiple_files=True,
                help="Upload up to 50 Layerwise files containing Disputed Amount. They will be combined automatically."
            )
            
            if file3:
                try:
                    if len(file3) > 50:
                        st.error("❌ Maximum 50 files allowed. Please remove some files.")
                    else:
                        all_data = []
                        
                        # Show progress for multiple files
                        if len(file3) > 1:
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                        
                        for idx, uploaded_file in enumerate(file3):
                            if len(file3) > 1:
                                status_text.text(f"Reading file {idx+1}/{len(file3)}: {uploaded_file.name}...")
                                progress_bar.progress((idx + 1) / len(file3))
                            
                            # Read file bytes first
                            file_bytes = uploaded_file.getvalue()
                            
                            if uploaded_file.name.endswith('.csv'):
                                df3_temp = pd.read_csv(BytesIO(file_bytes), dtype=str)
                            else:
                                # Try reading with openpyxl, read all columns
                                xl = pd.ExcelFile(BytesIO(file_bytes), engine='openpyxl')
                                sheet_names = xl.sheet_names
                                
                                # For multiple files, use first sheet automatically
                                if len(file3) > 1:
                                    selected_sheet = sheet_names[0]
                                else:
                                    # Show sheet selector only for single file with multiple sheets
                                    if len(sheet_names) > 1:
                                        selected_sheet = st.selectbox(
                                            "Select Sheet",
                                            options=sheet_names,
                                            key='txn_file3_sheet',
                                            help="Select which sheet contains the disputed amount data"
                                        )
                                    else:
                                        selected_sheet = sheet_names[0]
                                
                                # Read with no restrictions
                                df3_temp = pd.read_excel(
                                    BytesIO(file_bytes), 
                                    sheet_name=selected_sheet, 
                                    dtype=str, 
                                    engine='openpyxl',
                                    header=0  # First row is header
                                )
                            
                            # Clean up column names
                            df3_temp.columns = [str(col).strip() if not str(col).startswith('Unnamed') else f"Column_{i}" for i, col in enumerate(df3_temp.columns)]
                            
                            all_data.append(df3_temp)
                        
                        # Combine all files
                        if len(all_data) > 1:
                            combined_df = pd.concat(all_data, ignore_index=True)
                            st.session_state.txn_matcher_file3_df = combined_df
                            
                            if len(file3) > 1:
                                progress_bar.empty()
                                status_text.empty()
                            
                            st.success(f"✅ Combined {len(file3)} Layerwise files: {len(combined_df):,} total records, {len(combined_df.columns)} columns")
                            
                            # Show file breakdown
                            with st.expander("📋 Layerwise Files Combined", expanded=False):
                                breakdown = []
                                for idx, (f, df) in enumerate(zip(file3, all_data), 1):
                                    breakdown.append({
                                        'File #': idx,
                                        'Filename': f.name,
                                        'Records': len(df),
                                        'Columns': len(df.columns)
                                    })
                                st.dataframe(pd.DataFrame(breakdown), use_container_width=True)
                        else:
                            st.session_state.txn_matcher_file3_df = all_data[0]
                            st.success(f"✅ Loaded {len(all_data[0]):,} records, {len(all_data[0].columns)} columns")
                        
                        # Show columns for debugging
                        st.info(f"📋 Columns found: {list(st.session_state.txn_matcher_file3_df.columns)}")
                        
                        with st.expander("Preview Combined Layerwise Data", expanded=True):
                            st.dataframe(st.session_state.txn_matcher_file3_df.head(10), use_container_width=True)
                            
                except Exception as e:
                    st.error(f"❌ Error reading files: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
            
            # Column selection for disputed amount matching
            if st.session_state.txn_matcher_file3_df is not None:
                st.subheader("🔧 Select Columns for Disputed Amount Matching")
                
                # Use the selected base file
                if use_money_transfer_as_main:
                    base_df = st.session_state.txn_matcher_file2_df
                    base_file_name = "Money Transfer (File 2)"
                else:
                    base_df = result_df
                    base_file_name = "Pending/Unattended Result (Step 4 output)"
                
                base_columns = ["-- Select Column --"] + base_df.columns.tolist()
                file3_columns = ["-- Select Column --"] + st.session_state.txn_matcher_file3_df.columns.tolist()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**From {base_file_name}:**")
                    
                    # Get saved mappings
                    saved_r_ack = st.session_state.txn_matcher_saved_mappings.get('disp_r_ack_col')
                    saved_r_acc = st.session_state.txn_matcher_saved_mappings.get('disp_r_acc_col')
                    saved_r_amt = st.session_state.txn_matcher_saved_mappings.get('disp_r_amt_col')
                    
                    default_r_ack_idx = 0
                    if saved_r_ack and saved_r_ack in base_df.columns:
                        default_r_ack_idx = base_columns.index(saved_r_ack)
                    
                    default_r_acc_idx = 0
                    if saved_r_acc and saved_r_acc in base_df.columns:
                        default_r_acc_idx = base_columns.index(saved_r_acc)
                    
                    default_r_amt_idx = 0
                    if saved_r_amt and saved_r_amt in base_df.columns:
                        default_r_amt_idx = base_columns.index(saved_r_amt)
                    
                    r_ack_col = st.selectbox(
                        "Acknowledgement No Column",
                        options=base_columns,
                        index=default_r_ack_idx,
                        key='disp_r_ack_col'
                    )
                    
                    r_acc_col = st.selectbox(
                        "Account No Column",
                        options=base_columns,
                        index=default_r_acc_idx,
                        key='disp_r_acc_col'
                    )
                    
                    r_amt_col = st.selectbox(
                        "Amount Column",
                        options=base_columns,
                        index=default_r_amt_idx,
                        key='disp_r_amt_col'
                    )
                    
                    # Save selections
                    if r_ack_col != "-- Select Column --":
                        st.session_state.txn_matcher_saved_mappings['disp_r_ack_col'] = r_ack_col
                        save_mappings(st.session_state.txn_matcher_saved_mappings)
                    if r_acc_col != "-- Select Column --":
                        st.session_state.txn_matcher_saved_mappings['disp_r_acc_col'] = r_acc_col
                        save_mappings(st.session_state.txn_matcher_saved_mappings)
                    if r_amt_col != "-- Select Column --":
                        st.session_state.txn_matcher_saved_mappings['disp_r_amt_col'] = r_amt_col
                        save_mappings(st.session_state.txn_matcher_saved_mappings)
                
                with col2:
                    st.write("**From Layerwise File (File 3):**")
                    
                    # Get saved mappings
                    saved_f3_ack = st.session_state.txn_matcher_saved_mappings.get('disp_f3_ack_col')
                    saved_f3_acc = st.session_state.txn_matcher_saved_mappings.get('disp_f3_acc_col')
                    saved_f3_amt = st.session_state.txn_matcher_saved_mappings.get('disp_f3_amt_col')
                    saved_f3_disp = st.session_state.txn_matcher_saved_mappings.get('disp_f3_disp_col')
                    
                    default_f3_ack_idx = 0
                    if saved_f3_ack and saved_f3_ack in st.session_state.txn_matcher_file3_df.columns:
                        default_f3_ack_idx = file3_columns.index(saved_f3_ack)
                    
                    default_f3_acc_idx = 0
                    if saved_f3_acc and saved_f3_acc in st.session_state.txn_matcher_file3_df.columns:
                        default_f3_acc_idx = file3_columns.index(saved_f3_acc)
                    
                    default_f3_amt_idx = 0
                    if saved_f3_amt and saved_f3_amt in st.session_state.txn_matcher_file3_df.columns:
                        default_f3_amt_idx = file3_columns.index(saved_f3_amt)
                    
                    default_f3_disp_idx = 0
                    if saved_f3_disp and saved_f3_disp in st.session_state.txn_matcher_file3_df.columns:
                        default_f3_disp_idx = file3_columns.index(saved_f3_disp)
                    
                    f3_ack_col = st.selectbox(
                        "Acknowledgement No Column",
                        options=file3_columns,
                        index=default_f3_ack_idx,
                        key='disp_f3_ack_col'
                    )
                    
                    f3_acc_col = st.selectbox(
                        "Account No Column",
                        options=file3_columns,
                        index=default_f3_acc_idx,
                        key='disp_f3_acc_col'
                    )
                    
                    f3_amt_col = st.selectbox(
                        "Amount Column",
                        options=file3_columns,
                        index=default_f3_amt_idx,
                        key='disp_f3_amt_col'
                    )
                    
                    f3_disp_col = st.selectbox(
                        "Disputed Amount Column",
                        options=file3_columns,
                        index=default_f3_disp_idx,
                        key='disp_f3_disp_col',
                        help="Column containing the Disputed Amount to add"
                    )
                    
                    # Save selections
                    if f3_ack_col != "-- Select Column --":
                        st.session_state.txn_matcher_saved_mappings['disp_f3_ack_col'] = f3_ack_col
                        save_mappings(st.session_state.txn_matcher_saved_mappings)
                    if f3_acc_col != "-- Select Column --":
                        st.session_state.txn_matcher_saved_mappings['disp_f3_acc_col'] = f3_acc_col
                        save_mappings(st.session_state.txn_matcher_saved_mappings)
                    if f3_amt_col != "-- Select Column --":
                        st.session_state.txn_matcher_saved_mappings['disp_f3_amt_col'] = f3_amt_col
                        save_mappings(st.session_state.txn_matcher_saved_mappings)
                    if f3_disp_col != "-- Select Column --":
                        st.session_state.txn_matcher_saved_mappings['disp_f3_disp_col'] = f3_disp_col
                        save_mappings(st.session_state.txn_matcher_saved_mappings)
                
                # Validate all selections
                disp_all_selected = (
                    r_ack_col != "-- Select Column --" and
                    r_acc_col != "-- Select Column --" and
                    r_amt_col != "-- Select Column --" and
                    f3_ack_col != "-- Select Column --" and
                    f3_acc_col != "-- Select Column --" and
                    f3_amt_col != "-- Select Column --" and
                    f3_disp_col != "-- Select Column --"
                )
                
                if not disp_all_selected:
                    st.warning("⚠️ Please select all columns for disputed amount matching")
                
                # Match Disputed Amount button
                if st.button("💰 Match Disputed Amount", type="primary", use_container_width=True, disabled=not disp_all_selected):
                    with st.spinner("Matching disputed amounts..."):
                        try:
                            # Use the selected base file
                            if use_money_transfer_as_main:
                                df_base = st.session_state.txn_matcher_file2_df.copy()
                                base_name = "Money Transfer (File 2)"
                            else:
                                df_base = result_df.copy()
                                base_name = "Pending/Unattended Result (Step 4)"
                            
                            df3 = st.session_state.txn_matcher_file3_df.copy()
                            
                            # Normalize columns for matching - convert to string to avoid type conflicts
                            df_base['_norm_ack'] = df_base[r_ack_col].apply(normalize_ack_number).astype(str)
                            df_base['_norm_acc'] = df_base[r_acc_col].apply(normalize_account_number).astype(str)
                            df_base['_norm_amt'] = df_base[r_amt_col].apply(normalize_amount).astype(str)
                            
                            df3['_norm_ack'] = df3[f3_ack_col].apply(normalize_ack_number).astype(str)
                            df3['_norm_acc'] = df3[f3_acc_col].apply(normalize_account_number).astype(str)
                            df3['_norm_amt'] = df3[f3_amt_col].apply(normalize_amount).astype(str)
                            
                            # Remove None/nan values (convert to empty string)
                            df_base['_norm_ack'] = df_base['_norm_ack'].replace('None', '').replace('nan', '')
                            df_base['_norm_acc'] = df_base['_norm_acc'].replace('None', '').replace('nan', '')
                            df_base['_norm_amt'] = df_base['_norm_amt'].replace('None', '').replace('nan', '')
                            
                            df3['_norm_ack'] = df3['_norm_ack'].replace('None', '').replace('nan', '')
                            df3['_norm_acc'] = df3['_norm_acc'].replace('None', '').replace('nan', '')
                            df3['_norm_amt'] = df3['_norm_amt'].replace('None', '').replace('nan', '')
                            
                            # Prepare File 3 for merge
                            df3_merge = df3[['_norm_ack', '_norm_acc', '_norm_amt', f3_disp_col]].copy()
                            df3_merge = df3_merge.rename(columns={f3_disp_col: 'DISPUTED AMOUNT'})
                            
                            # Remove duplicates (keep first)
                            df3_merge = df3_merge.drop_duplicates(subset=['_norm_ack', '_norm_acc', '_norm_amt'], keep='first')
                            
                            # Remove rows with empty matching keys
                            df3_merge = df3_merge[
                                (df3_merge['_norm_ack'] != '') & 
                                (df3_merge['_norm_acc'] != '') & 
                                (df3_merge['_norm_amt'] != '')
                            ]
                            
                            # Merge on all 3 columns
                            final_df = df_base.merge(
                                df3_merge,
                                on=['_norm_ack', '_norm_acc', '_norm_amt'],
                                how='left'
                            )
                            
                            # Count matches
                            disp_matched = final_df['DISPUTED AMOUNT'].notna().sum()
                            disp_total = len(final_df)
                            
                            # Reorder columns - insert DISPUTED AMOUNT after Amount column
                            original_cols = list(df_base.columns)
                            
                            # Find position of Amount column
                            amt_col_index = original_cols.index(r_amt_col) + 1
                            
                            # Build new column order
                            new_order = original_cols[:amt_col_index]
                            new_order.append('DISPUTED AMOUNT')
                            new_order.extend(original_cols[amt_col_index:])
                            
                            # Select and reorder columns (drop temp columns)
                            final_df = final_df[new_order].copy()
                            
                            # Fill empty values
                            final_df['DISPUTED AMOUNT'] = final_df['DISPUTED AMOUNT'].fillna('')
                            
                            # Store final result
                            st.session_state.txn_matcher_final_df = final_df
                            
                            # Display statistics
                            st.success(f"✅ Disputed Amount matching complete! Using **{base_name}** as main file.")
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Total Records", f"{disp_total:,}")
                            with col2:
                                st.metric("Matched Disputed", f"{disp_matched:,}")
                            with col3:
                                st.metric("Unmatched", f"{disp_total - disp_matched:,}")
                            with col4:
                                disp_rate = (disp_matched / disp_total * 100) if disp_total > 0 else 0
                                st.metric("Match Rate", f"{disp_rate:.1f}%")
                            
                        except Exception as e:
                            st.error(f"❌ Error during matching: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc())
                
                # Display final results with disputed amount
                if st.session_state.txn_matcher_final_df is not None:
                    st.markdown("---")
                    st.header("📋 Final Results (with Disputed Amount)")
                    
                    final_df = st.session_state.txn_matcher_final_df
                    
                    # Preview
                    with st.expander("📋 Preview Final Results (First 100 rows)", expanded=True):
                        st.dataframe(final_df.head(100), use_container_width=True)
                    
                    # Download buttons
                    st.subheader("📥 Download Final Results")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        excel_bytes = generate_excel_bytes(final_df)
                        st.download_button(
                            label=f"📊 Download Excel ({len(final_df):,} rows)",
                            data=excel_bytes,
                            file_name=f"final_with_disputed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            type="primary",
                            key="download_final_excel"
                        )
                    
                    with col2:
                        csv_bytes = final_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label=f"📄 Download CSV ({len(final_df):,} rows)",
                            data=csv_bytes,
                            file_name=f"final_with_disputed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True,
                            key="download_final_csv"
                        )
    
    # Footer
    st.markdown("---")
    st.caption("*Transaction ID Matcher - Match records and add Account Number, Transaction Date & Disputed Amount*")
