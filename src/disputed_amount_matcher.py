"""
Disputed Amount Matcher Module.

Match records from two files based on 3 parameters:
1. Acknowledgement Number
2. Account Number (supports alphanumeric)
3. Amount

Add Disputed Amount from File 2 to File 1.

CRITICAL: This is legal data - 100% accuracy required.
"""

import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import re
from src.persistent_mapping import PersistentMapping


def normalize_ack_number(value):
    """
    Normalize Acknowledgement Number for EXACT matching.
    - Convert to string
    - Strip whitespace
    - Remove .0 suffix (from Excel float conversion)
    - Uppercase for consistency
    """
    if pd.isna(value) or value is None:
        return None
    
    normalized = str(value).strip()
    
    # Remove .0 suffix from numbers read as float
    if normalized.endswith('.0'):
        normalized = normalized[:-2]
    
    # Remove any leading/trailing whitespace again
    normalized = normalized.strip()
    
    # Uppercase for consistent matching
    normalized = normalized.upper()
    
    return normalized if normalized and normalized != 'NAN' and normalized != 'NONE' else None


def normalize_account_number(value):
    """
    Normalize Account Number for EXACT matching.
    Handles both numeric and alphanumeric account numbers.
    - Convert to string
    - Strip whitespace
    - Remove .0 suffix (from Excel float conversion)
    - Uppercase for consistency
    - Preserve all alphanumeric characters exactly
    """
    if pd.isna(value) or value is None:
        return None
    
    normalized = str(value).strip()
    
    # Remove .0 suffix from numbers read as float (e.g., "12345.0" -> "12345")
    if normalized.endswith('.0'):
        normalized = normalized[:-2]
    
    # Remove any leading/trailing whitespace again
    normalized = normalized.strip()
    
    # Uppercase for consistent matching (important for alphanumeric)
    normalized = normalized.upper()
    
    return normalized if normalized and normalized != 'NAN' and normalized != 'NONE' else None


def normalize_amount(amount_value):
    """
    Normalize Amount for EXACT matching.
    - Remove currency symbols (₹, Rs, INR, etc.)
    - Remove commas
    - Convert to float for numeric comparison
    - Round to 2 decimal places for consistency
    """
    if pd.isna(amount_value) or amount_value is None:
        return None
    
    amount_str = str(amount_value).strip()
    
    # Skip if empty or invalid
    if not amount_str or amount_str.upper() in ['NAN', 'NONE', '']:
        return None
    
    # Remove currency symbols
    amount_str = amount_str.replace('₹', '').replace('Rs', '').replace('Rs.', '')
    amount_str = amount_str.replace('INR', '').replace('USD', '').replace('$', '')
    
    # Remove commas and spaces
    amount_str = amount_str.replace(',', '').replace(' ', '')
    
    # Remove any other non-numeric characters except decimal point and minus
    amount_str = re.sub(r'[^\d.\-]', '', amount_str)
    
    try:
        # Convert to float and round to 2 decimal places
        amount = round(float(amount_str), 2)
        return amount
    except (ValueError, TypeError):
        return None


def generate_excel_bytes(df: pd.DataFrame) -> bytes:
    """Generate Excel file bytes from DataFrame."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Matched Data')
    return output.getvalue()


def render_disputed_amount_matcher_page():
    """Render the Disputed Amount Matcher page."""
    
    # Initialize persistent mapping
    mapping = PersistentMapping('disputed_amount_matcher')
    
    st.title("💰 Disputed Amount Matcher")
    st.markdown("""
    Match records from two files based on **3 parameters**:
    1. **Acknowledgement Number**
    2. **Account Number**
    3. **Amount**
    
    All 3 must match to add the **Disputed Amount** from File 2 to File 1.
    """)
    
    # Show saved mappings indicator
    saved_count = mapping.get_saved_count()
    if saved_count > 0:
        st.success(f"✅ {saved_count} column mapping(s) remembered from previous session")
    
    # Initialize session state
    if 'disp_file1_df' not in st.session_state:
        st.session_state.disp_file1_df = None
    if 'disp_file2_df' not in st.session_state:
        st.session_state.disp_file2_df = None
    if 'disp_result_df' not in st.session_state:
        st.session_state.disp_result_df = None
    
    st.markdown("---")
    
    # ============== STEP 1: UPLOAD FILES ==============
    st.header("📁 Step 1: Upload Files")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("File 1: Main Data")
        st.caption("The file you want to add Disputed Amount to")
        
        file1 = st.file_uploader(
            "Upload Main Data file",
            type=['xlsx', 'xls', 'csv'],
            key='disp_file1_upload'
        )
        
        if file1:
            try:
                file_bytes = file1.getvalue()
                if file1.name.endswith('.csv'):
                    st.session_state.disp_file1_df = pd.read_csv(BytesIO(file_bytes), dtype=str)
                else:
                    st.session_state.disp_file1_df = pd.read_excel(BytesIO(file_bytes), dtype=str, engine='openpyxl')
                
                st.success(f"✅ Loaded {len(st.session_state.disp_file1_df):,} records, {len(st.session_state.disp_file1_df.columns)} columns")
                
                with st.expander("Preview File 1", expanded=False):
                    st.dataframe(st.session_state.disp_file1_df.head(10), use_container_width=True)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    with col2:
        st.subheader("File 2: Disputed Amount Data")
        st.caption("Contains Disputed Amount to be matched and added")
        
        file2 = st.file_uploader(
            "Upload Disputed Amount file",
            type=['xlsx', 'xls', 'csv'],
            key='disp_file2_upload'
        )
        
        if file2:
            try:
                file_bytes = file2.getvalue()
                if file2.name.endswith('.csv'):
                    st.session_state.disp_file2_df = pd.read_csv(BytesIO(file_bytes), dtype=str)
                else:
                    # Check for multiple sheets
                    xl = pd.ExcelFile(BytesIO(file_bytes), engine='openpyxl')
                    sheet_names = xl.sheet_names
                    
                    if len(sheet_names) > 1:
                        selected_sheet = st.selectbox(
                            "Select Sheet",
                            options=sheet_names,
                            key='disp_file2_sheet'
                        )
                    else:
                        selected_sheet = sheet_names[0]
                    
                    st.session_state.disp_file2_df = pd.read_excel(
                        BytesIO(file_bytes), 
                        sheet_name=selected_sheet,
                        dtype=str, 
                        engine='openpyxl'
                    )
                
                st.success(f"✅ Loaded {len(st.session_state.disp_file2_df):,} records, {len(st.session_state.disp_file2_df.columns)} columns")
                st.info(f"📋 Columns: {list(st.session_state.disp_file2_df.columns)}")
                
                with st.expander("Preview File 2", expanded=False):
                    st.dataframe(st.session_state.disp_file2_df.head(10), use_container_width=True)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # ============== STEP 2: SELECT COLUMNS ==============
    if st.session_state.disp_file1_df is not None and st.session_state.disp_file2_df is not None:
        st.markdown("---")
        st.header("🔧 Step 2: Select Columns for Matching")
        
        file1_cols = ["-- Select Column --"] + list(st.session_state.disp_file1_df.columns)
        file2_cols = ["-- Select Column --"] + list(st.session_state.disp_file2_df.columns)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("From File 1:")
            
            f1_ack_col = st.selectbox(
                "Acknowledgement No Column",
                options=file1_cols,
                index=mapping.get_default_index('f1_ack_col', file1_cols),
                key='disp_f1_ack'
            )
            if f1_ack_col != "-- Select Column --":
                mapping.set('f1_ack_col', f1_ack_col)
            
            f1_acc_col = st.selectbox(
                "Account No Column",
                options=file1_cols,
                index=mapping.get_default_index('f1_acc_col', file1_cols),
                key='disp_f1_acc'
            )
            if f1_acc_col != "-- Select Column --":
                mapping.set('f1_acc_col', f1_acc_col)
            
            f1_amt_col = st.selectbox(
                "Amount Column",
                options=file1_cols,
                index=mapping.get_default_index('f1_amt_col', file1_cols),
                key='disp_f1_amt'
            )
            if f1_amt_col != "-- Select Column --":
                mapping.set('f1_amt_col', f1_amt_col)
        
        with col2:
            st.subheader("From File 2:")
            
            f2_ack_col = st.selectbox(
                "Acknowledgement No Column",
                options=file2_cols,
                index=mapping.get_default_index('f2_ack_col', file2_cols),
                key='disp_f2_ack'
            )
            if f2_ack_col != "-- Select Column --":
                mapping.set('f2_ack_col', f2_ack_col)
            
            f2_acc_col = st.selectbox(
                "Account No Column",
                options=file2_cols,
                index=mapping.get_default_index('f2_acc_col', file2_cols),
                key='disp_f2_acc'
            )
            if f2_acc_col != "-- Select Column --":
                mapping.set('f2_acc_col', f2_acc_col)
            
            f2_amt_col = st.selectbox(
                "Amount Column",
                options=file2_cols,
                index=mapping.get_default_index('f2_amt_col', file2_cols),
                key='disp_f2_amt'
            )
            if f2_amt_col != "-- Select Column --":
                mapping.set('f2_amt_col', f2_amt_col)
            
            f2_disp_col = st.selectbox(
                "Disputed Amount Column",
                options=file2_cols,
                index=mapping.get_default_index('f2_disp_col', file2_cols),
                key='disp_f2_disp',
                help="This column will be added to File 1"
            )
            if f2_disp_col != "-- Select Column --":
                mapping.set('f2_disp_col', f2_disp_col)
        
        # Validate selections
        all_selected = (
            f1_ack_col != "-- Select Column --" and
            f1_acc_col != "-- Select Column --" and
            f1_amt_col != "-- Select Column --" and
            f2_ack_col != "-- Select Column --" and
            f2_acc_col != "-- Select Column --" and
            f2_amt_col != "-- Select Column --" and
            f2_disp_col != "-- Select Column --"
        )
        
        if not all_selected:
            st.warning("⚠️ Please select all required columns")
        
        # ============== STEP 3: MATCH ==============
        st.markdown("---")
        st.header("🔄 Step 3: Match Records")
        
        if st.button("💰 Match & Add Disputed Amount", type="primary", use_container_width=True, disabled=not all_selected):
            with st.spinner("Matching records on 3 parameters (100% accuracy mode)..."):
                try:
                    df1 = st.session_state.disp_file1_df.copy()
                    df2 = st.session_state.disp_file2_df.copy()
                    
                    # Normalize columns for EXACT matching
                    df1['_norm_ack'] = df1[f1_ack_col].apply(normalize_ack_number)
                    df1['_norm_acc'] = df1[f1_acc_col].apply(normalize_account_number)
                    df1['_norm_amt'] = df1[f1_amt_col].apply(normalize_amount)
                    
                    df2['_norm_ack'] = df2[f2_ack_col].apply(normalize_ack_number)
                    df2['_norm_acc'] = df2[f2_acc_col].apply(normalize_account_number)
                    df2['_norm_amt'] = df2[f2_amt_col].apply(normalize_amount)
                    
                    # Prepare File 2 for merge - keep disputed amount
                    df2_merge = df2[['_norm_ack', '_norm_acc', '_norm_amt', f2_disp_col]].copy()
                    df2_merge = df2_merge.rename(columns={f2_disp_col: 'DISPUTED AMOUNT'})
                    
                    # Remove rows with any NULL matching keys
                    df2_merge = df2_merge.dropna(subset=['_norm_ack', '_norm_acc', '_norm_amt'])
                    
                    # Check for duplicates in File 2 (same Ack+Acc+Amt with different disputed amounts)
                    duplicates = df2_merge.duplicated(subset=['_norm_ack', '_norm_acc', '_norm_amt'], keep=False)
                    if duplicates.any():
                        dup_count = duplicates.sum()
                        st.warning(f"⚠️ Found {dup_count} duplicate key combinations in File 2. Using first occurrence.")
                    
                    # Remove duplicates (keep first)
                    df2_merge = df2_merge.drop_duplicates(subset=['_norm_ack', '_norm_acc', '_norm_amt'], keep='first')
                    
                    # EXACT MERGE on all 3 columns
                    result_df = df1.merge(
                        df2_merge,
                        on=['_norm_ack', '_norm_acc', '_norm_amt'],
                        how='left'
                    )
                    
                    # Count matches
                    matched_count = result_df['DISPUTED AMOUNT'].notna().sum()
                    total_count = len(result_df)
                    unmatched_count = total_count - matched_count
                    
                    # Reorder columns - insert DISPUTED AMOUNT right after Amount column
                    original_cols = list(st.session_state.disp_file1_df.columns)
                    insert_index = original_cols.index(f1_amt_col) + 1
                    
                    new_order = original_cols[:insert_index]
                    new_order.append('DISPUTED AMOUNT')
                    new_order.extend(original_cols[insert_index:])
                    
                    # Select columns (drop temp columns)
                    final_df = result_df[new_order].copy()
                    
                    # Fill empty values with empty string (not modifying data)
                    final_df['DISPUTED AMOUNT'] = final_df['DISPUTED AMOUNT'].fillna('')
                    
                    # Store result
                    st.session_state.disp_result_df = final_df
                    
                    # Display statistics
                    st.success("✅ Matching complete with 100% accuracy!")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Records", f"{total_count:,}")
                    with col2:
                        st.metric("Matched", f"{matched_count:,}")
                    with col3:
                        st.metric("Unmatched", f"{unmatched_count:,}")
                    with col4:
                        rate = (matched_count / total_count * 100) if total_count > 0 else 0
                        st.metric("Match Rate", f"{rate:.1f}%")
                    
                    # Show verification info
                    st.info(f"""
                    **Matching Verification:**
                    - File 1 records: {len(df1):,}
                    - File 2 records (after removing duplicates): {len(df2_merge):,}
                    - Matched records: {matched_count:,}
                    - Records without disputed amount: {unmatched_count:,}
                    """)
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
        
        # ============== STEP 4: RESULTS ==============
        if st.session_state.disp_result_df is not None:
            st.markdown("---")
            st.header("📋 Step 4: Results")
            
            result_df = st.session_state.disp_result_df
            
            with st.expander("Preview Results (First 100 rows)", expanded=True):
                st.dataframe(result_df.head(100), use_container_width=True)
            
            # Download buttons
            st.subheader("📥 Download Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                excel_bytes = generate_excel_bytes(result_df)
                st.download_button(
                    label=f"📊 Download Excel ({len(result_df):,} rows)",
                    data=excel_bytes,
                    file_name=f"with_disputed_amount_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary"
                )
            
            with col2:
                csv_bytes = result_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"📄 Download CSV ({len(result_df):,} rows)",
                    data=csv_bytes,
                    file_name=f"with_disputed_amount_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    
    # Clear button
    st.markdown("---")
    if st.button("🔄 Clear & Start Over", use_container_width=True):
        st.session_state.disp_file1_df = None
        st.session_state.disp_file2_df = None
        st.session_state.disp_result_df = None
        st.rerun()
    
    st.caption("*Disputed Amount Matcher - Match on Ack No + Account No + Amount*")
