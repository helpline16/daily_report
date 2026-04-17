"""
Merge Excel Files Module - Upload multiple files and get aggregated summary.

Features:
- Upload 1 to 15 Excel files
- Auto-detect columns (Account No, ACK No, Amount, etc.)
- Merge all files and aggregate by account
- Download summary as Excel/CSV
- Optimized for large files
"""
import streamlit as st
import pandas as pd
import io
from typing import List, Dict, Optional, Tuple


def auto_detect_columns(df: pd.DataFrame) -> Dict[str, str]:
    """Auto-detect column mappings based on column names."""
    # Store original column names for reference
    original_columns = list(df.columns)
    
    # Normalize column names for matching
    normalized_cols = {str(col).strip().lower() if col is not None else "": col for col in df.columns}
    
    columns_map = {}
    
    for col_lower, original_col in normalized_cols.items():
        if not col_lower:
            continue
        
        # Acknowledgement Number
        if not columns_map.get('ack_no'):
            if ('acknowledgement' in col_lower or 'ack' in col_lower) and ('no' in col_lower or 'number' in col_lower):
                columns_map['ack_no'] = original_col
            elif col_lower in ['acknowledgement no.', 'ack no.', 'ack_no', 'acknowledgement_no', 'ack no', 'acknowledgement no']:
                columns_map['ack_no'] = original_col
        
        # Account Number - more flexible matching
        if not columns_map.get('account_no'):
            if 'account' in col_lower and ('no' in col_lower or 'number' in col_lower or 'num' in col_lower):
                columns_map['account_no'] = original_col
            elif col_lower in ['account no.', 'account_no', 'acc no.', 'acc_no', 'account no', 'acc no', 'account number', 'acc number', 'accountno', 'accno']:
                columns_map['account_no'] = original_col
        
        # Transaction Amount
        if not columns_map.get('transaction_amount'):
            if 'transaction' in col_lower and 'amount' in col_lower:
                columns_map['transaction_amount'] = original_col
            elif col_lower in ['transaction amount', 'txn amount', 'amount', 'trans amount', 'transaction amt', 'txn amt']:
                columns_map['transaction_amount'] = original_col
            elif col_lower == 'amount' and 'transaction_amount' not in columns_map:
                columns_map['transaction_amount'] = original_col
        
        # Disputed Amount
        if not columns_map.get('disputed_amount'):
            if 'disputed' in col_lower and 'amount' in col_lower:
                columns_map['disputed_amount'] = original_col
            elif col_lower in ['disputed amount', 'dispute amount', 'disputed amt', 'dispute amt']:
                columns_map['disputed_amount'] = original_col
        
        # Bank Name
        if not columns_map.get('bank_name'):
            if 'bank' in col_lower and 'name' not in columns_map.get('account_no', '').lower():
                if 'fi' in col_lower or 'name' in col_lower or col_lower == 'bank':
                    columns_map['bank_name'] = original_col
            elif 'bank/fi' in col_lower or 'bank name' in col_lower or col_lower in ['bank', 'bank/fis', 'bank / fi']:
                columns_map['bank_name'] = original_col
        
        # IFSC Code
        if not columns_map.get('ifsc_code'):
            if 'ifsc' in col_lower:
                columns_map['ifsc_code'] = original_col
        
        # District
        if not columns_map.get('district'):
            if 'district' in col_lower and 'state' not in col_lower:
                columns_map['district'] = original_col
        
        # State
        if not columns_map.get('state'):
            if 'state' in col_lower and 'district' not in col_lower:
                columns_map['state'] = original_col
        
        # Address
        if not columns_map.get('address'):
            if 'address' in col_lower:
                columns_map['address'] = original_col
    
    return columns_map


def read_excel_optimized(uploaded_file) -> pd.DataFrame:
    """Read Excel file with optimization for large files."""
    filename = uploaded_file.name.lower()
    
    if filename.endswith('.csv'):
        return pd.read_csv(uploaded_file, low_memory=False, dtype=str)
    else:
        return pd.read_excel(uploaded_file, dtype=str)


def process_single_file(uploaded_file, file_index: int) -> Tuple[Optional[pd.DataFrame], str]:
    """Process a single uploaded file and return standardized data."""
    try:
        df = read_excel_optimized(uploaded_file)
        
        if len(df) == 0:
            return None, "❌ Error: File is empty"
        
        # Store original columns for error reporting
        original_columns = list(df.columns)
        
        # Auto-detect columns
        columns_map = auto_detect_columns(df)
        
        # Check required columns
        required = {'account_no', 'transaction_amount'}
        missing = required - set(columns_map.keys())
        
        if missing:
            # Provide helpful error message with available columns
            available_cols = ', '.join([f"'{col}'" for col in original_columns[:10]])
            if len(original_columns) > 10:
                available_cols += f", ... ({len(original_columns)} total)"
            
            missing_readable = []
            if 'account_no' in missing:
                missing_readable.append('Account Number')
            if 'transaction_amount' in missing:
                missing_readable.append('Transaction Amount')
            
            return None, f"❌ Error: Could not find required columns: {', '.join(missing_readable)}. Available columns: {available_cols}"
        
        # Build standardized dataframe
        data = pd.DataFrame()
        
        # Required columns
        data['Account No.'] = df[columns_map['account_no']].astype(str).str.strip()
        data['Transaction Amount'] = pd.to_numeric(
            df[columns_map['transaction_amount']].astype(str).str.replace(',', '').str.strip(),
            errors='coerce'
        ).fillna(0)
        
        # Optional columns
        if 'ack_no' in columns_map:
            data['Acknowledgement No.'] = df[columns_map['ack_no']].astype(str).str.strip()
        else:
            data['Acknowledgement No.'] = ''
        
        if 'disputed_amount' in columns_map:
            data['Disputed Amount'] = pd.to_numeric(
                df[columns_map['disputed_amount']].astype(str).str.replace(',', '').str.strip(),
                errors='coerce'
            ).fillna(0)
        else:
            data['Disputed Amount'] = 0
        
        if 'bank_name' in columns_map:
            data['Bank Name'] = df[columns_map['bank_name']].astype(str).str.strip()
        else:
            data['Bank Name'] = 'Unknown'
        
        if 'ifsc_code' in columns_map:
            data['IFSC Code'] = df[columns_map['ifsc_code']].astype(str).str.strip()
        else:
            data['IFSC Code'] = ''
        
        if 'district' in columns_map:
            data['District'] = df[columns_map['district']].astype(str).str.strip()
        else:
            data['District'] = ''
        
        if 'state' in columns_map:
            data['State'] = df[columns_map['state']].astype(str).str.strip()
        else:
            data['State'] = ''
        
        if 'address' in columns_map:
            data['Address'] = df[columns_map['address']].astype(str).str.strip()
        else:
            data['Address'] = ''
        
        # Remove rows with no transaction amount
        data = data[data['Transaction Amount'] != 0]
        
        # Remove rows with empty account numbers
        data = data[data['Account No.'].str.strip() != '']
        data = data[data['Account No.'] != 'nan']
        
        if len(data) == 0:
            return None, "❌ Error: No valid data rows after filtering (all account numbers or amounts were empty/invalid)"
        
        # Show detected columns
        detected_info = f"✅ {len(data):,} valid rows. Detected: Account='{columns_map['account_no']}', Amount='{columns_map['transaction_amount']}'"
        
        return data, detected_info
        
    except KeyError as e:
        return None, f"❌ Error: Column not found - {str(e)}"
    except Exception as e:
        return None, f"❌ Error: {str(e)}"


def aggregate_data(combined_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate data by account number - OPTIMIZED."""
    
    # Group by Account No., Bank Name, IFSC Code
    grouped = combined_df.groupby(['Account No.', 'Bank Name', 'IFSC Code'], dropna=False)
    
    # Aggregations
    summary = grouped.agg({
        'Acknowledgement No.': lambda x: ';'.join(x.dropna().unique()),
        'Transaction Amount': 'sum',
        'Disputed Amount': 'sum',
        'District': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else '',
        'State': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else '',
        'Address': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else ''
    }).reset_index()
    
    # Add transaction count
    txn_counts = grouped.size().reset_index(name='Transaction Count')
    summary = summary.merge(txn_counts, on=['Account No.', 'Bank Name', 'IFSC Code'])
    
    # Count distinct ACK numbers
    summary['Distinct ACK Count'] = summary['Acknowledgement No.'].apply(
        lambda x: len(set(x.split(';'))) if x else 0
    )
    
    # Reorder columns
    summary = summary[[
        'Account No.', 'Bank Name', 'IFSC Code', 'District', 'State', 'Address',
        'Transaction Count', 'Distinct ACK Count', 'Acknowledgement No.',
        'Transaction Amount', 'Disputed Amount'
    ]]
    
    # Sort by Transaction Amount descending
    summary = summary.sort_values('Transaction Amount', ascending=False).reset_index(drop=True)
    
    return summary


def render_merge_files_page():
    """Render the Merge Excel Files page."""
    st.title("📂 Merge Excel Files")
    st.markdown("""
    Upload **1 to 15 Excel files**, auto-detect columns, merge and aggregate by account number.
    Download the summary directly as Excel or CSV.
    """)
    
    # Show expected columns
    with st.expander("📋 Expected Columns (Auto-Detected)", expanded=False):
        st.markdown("""
        **Required Columns** (at least one of these names):
        - **Account Number**: `Account No.`, `Account No`, `Acc No.`, `Account Number`, `AccountNo`, etc.
        - **Transaction Amount**: `Transaction Amount`, `Txn Amount`, `Amount`, `Trans Amount`, etc.
        
        **Optional Columns** (will be included if found):
        - **Acknowledgement No**: `Acknowledgement No.`, `Ack No.`, `ACK No`, etc.
        - **Bank Name**: `Bank Name`, `Bank`, `Bank/FI`, `Bank/FIs`, etc.
        - **IFSC Code**: `IFSC Code`, `IFSC`, etc.
        - **District**: `District`
        - **State**: `State`
        - **Address**: `Address`
        - **Disputed Amount**: `Disputed Amount`, `Dispute Amount`, etc.
        
        💡 Column names are case-insensitive and flexible (spaces, dots, underscores are handled automatically)
        """)
    
    st.markdown("---")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose Excel/CSV files (1-15 files)",
        type=['xlsx', 'xls', 'csv'],
        accept_multiple_files=True,
        key="merge_file_uploader"
    )
    
    if uploaded_files:
        st.info(f"📁 **{len(uploaded_files)}** file(s) uploaded")
        
        # Show file list
        with st.expander("View uploaded files", expanded=False):
            for f in uploaded_files:
                size_kb = f.size / 1024
                if size_kb > 1024:
                    size_str = f"{size_kb/1024:.2f} MB"
                else:
                    size_str = f"{size_kb:.2f} KB"
                st.write(f"• **{f.name}** — {size_str}")
    
    st.markdown("---")
    
    # Process button
    process_btn = st.button("🚀 Process & Merge Files", type="primary", use_container_width=True)
    
    if process_btn:
        if not uploaded_files:
            st.warning("⚠️ Please upload at least 1 file")
            return
        
        if len(uploaded_files) > 15:
            st.warning("⚠️ Maximum 15 files allowed. Please remove some files.")
            return
        
        # Process each file
        all_data = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processing {uploaded_file.name}...")
            progress_bar.progress((i + 1) / len(uploaded_files))
            
            data, message = process_single_file(uploaded_file, i)
            
            if data is not None:
                st.success(f"**{uploaded_file.name}**: {message}")
                all_data.append(data)
            else:
                st.error(f"**{uploaded_file.name}**: {message}")
        
        progress_bar.progress(100)
        status_text.text("Processing complete!")
        
        if not all_data:
            st.error("❌ No valid data found in any uploaded files.")
            return
        
        # Combine all data
        st.markdown("---")
        st.subheader("📊 Generating Summary...")
        
        with st.spinner("Merging and aggregating data..."):
            combined_df = pd.concat(all_data, ignore_index=True)
            st.info(f"Combined: **{len(combined_df):,}** total rows from {len(all_data)} file(s)")
            
            # Aggregate
            summary = aggregate_data(combined_df)
        
        st.success(f"✅ Summary generated: **{len(summary):,}** unique accounts")
        
        # Store in session state
        st.session_state['merge_summary'] = summary
        st.session_state['merge_combined'] = combined_df
    
    # Show results if available
    if 'merge_summary' in st.session_state:
        summary = st.session_state['merge_summary']
        combined_df = st.session_state.get('merge_combined', None)
        
        st.markdown("---")
        
        # Add tabs for different views
        tab1, tab2 = st.tabs(["📊 Summary (Aggregated)", "📋 Full Data (All Rows)"])
        
        with tab1:
            st.subheader("Summary Results (Grouped by Account)")
            
            # Stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Unique Accounts", f"{len(summary):,}")
            with col2:
                total_amount = summary['Transaction Amount'].sum()
                st.metric("Total Amount", f"₹{total_amount:,.2f}")
            with col3:
                total_disputed = summary['Disputed Amount'].sum()
                st.metric("Total Disputed", f"₹{total_disputed:,.2f}")
            with col4:
                total_txns = summary['Transaction Count'].sum()
                st.metric("Total Transactions", f"{total_txns:,}")
            
            # Preview
            with st.expander("📋 Preview Summary (First 100 rows)", expanded=True):
                display_df = summary.head(100).copy()
                display_df['Transaction Amount'] = display_df['Transaction Amount'].apply(lambda x: f"₹{x:,.2f}")
                display_df['Disputed Amount'] = display_df['Disputed Amount'].apply(lambda x: f"₹{x:,.2f}")
                st.dataframe(display_df, use_container_width=True)
            
            st.markdown("---")
            st.subheader("📥 Download Summary")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Excel download
                buffer = io.BytesIO()
                MAX_ROWS = 1_048_576
                MAX_DATA_ROWS = MAX_ROWS - 1
                
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    if len(summary) > MAX_DATA_ROWS:
                        st.warning("⚠️ Data too large for single sheet. Splitting...")
                        for i in range(0, len(summary), MAX_DATA_ROWS):
                            chunk = summary.iloc[i:i + MAX_DATA_ROWS]
                            chunk.to_excel(writer, sheet_name=f"Summary_Part_{(i // MAX_DATA_ROWS) + 1}", index=False)
                    else:
                        summary.to_excel(writer, sheet_name="Summary", index=False)
                
                buffer.seek(0)
                st.download_button(
                    label="📊 Download Summary Excel",
                    data=buffer,
                    file_name="merged_summary.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            with col2:
                # CSV download
                csv_data = summary.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📄 Download Summary CSV",
                    data=csv_data,
                    file_name="merged_summary.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        with tab2:
            st.subheader("Full Merged Data (All Rows)")
            
            if combined_df is not None:
                # Stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Rows", f"{len(combined_df):,}")
                with col2:
                    st.metric("Total Columns", len(combined_df.columns))
                with col3:
                    size_mb = combined_df.memory_usage(deep=True).sum() / (1024 * 1024)
                    st.metric("Size", f"{size_mb:.1f} MB")
                
                st.info("💡 This is the complete merged data with ALL rows from all files (not aggregated)")
                
                # Preview
                with st.expander("📋 Preview Full Data (First 100 rows)", expanded=True):
                    st.dataframe(combined_df.head(100), use_container_width=True)
                
                st.markdown("---")
                st.subheader("📥 Download Full Data")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Excel download
                    buffer = io.BytesIO()
                    MAX_ROWS = 1_048_576
                    MAX_DATA_ROWS = MAX_ROWS - 1
                    
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        if len(combined_df) > MAX_DATA_ROWS:
                            st.warning("⚠️ Data too large for single sheet. Splitting...")
                            for i in range(0, len(combined_df), MAX_DATA_ROWS):
                                chunk = combined_df.iloc[i:i + MAX_DATA_ROWS]
                                chunk.to_excel(writer, sheet_name=f"Data_Part_{(i // MAX_DATA_ROWS) + 1}", index=False)
                        else:
                            combined_df.to_excel(writer, sheet_name="Merged Data", index=False)
                    
                    buffer.seek(0)
                    st.download_button(
                        label=f"📊 Download Full Excel ({len(combined_df):,} rows)",
                        data=buffer,
                        file_name="merged_full_data.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        type="primary"
                    )
                
                with col2:
                    # CSV download
                    csv_data = combined_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label=f"📄 Download Full CSV ({len(combined_df):,} rows)",
                        data=csv_data,
                        file_name="merged_full_data.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            else:
                st.warning("⚠️ Full data not available. Please re-process the files.")
        
        # Clear button
        st.markdown("---")
        if st.button("🔄 Clear & Start Over", use_container_width=True):
            if 'merge_summary' in st.session_state:
                del st.session_state['merge_summary']
            if 'merge_combined' in st.session_state:
                del st.session_state['merge_combined']
            st.rerun()
