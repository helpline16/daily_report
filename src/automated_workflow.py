import streamlit as st
import pandas as pd
import io
from datetime import datetime
import zipfile
import os
import json


# Import styling
import sys
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.ui_styling import render_page_header_with_info


def load_column_mappings():
    """Load saved column mappings from JSON file"""
    mapping_file = "cyber multiple accoun with DA and ACK/.kiro/workflow_mappings.json"
    try:
        if os.path.exists(mapping_file):
            with open(mapping_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        st.warning(f"Could not load saved mappings: {e}")
    return {}


def save_column_mappings(mappings):
    """Save column mappings to JSON file"""
    mapping_file = "cyber multiple accoun with DA and ACK/.kiro/workflow_mappings.json"
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(mapping_file), exist_ok=True)
        with open(mapping_file, 'w') as f:
            json.dump(mappings, f, indent=2)
    except Exception as e:
        st.warning(f"Could not save mappings: {e}")


def render_automated_workflow_page():
    """
    Automated workflow page that processes files through multiple steps:
    1. Match Layerwise + Fraud Amount files
    2. Generate 4 filtered files (All, Gujarat, 5L+, Gujarat 5L+)
    3. Auto-filter Non-Gujarat data (2 files)
    4. Auto-split by district (4 ZIP files)
    """
    
    # Render page header with info button
    render_page_header_with_info('automated_workflow')
    
    # File uploads
    st.markdown("### 📁 Step 1: Upload Files")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 1️⃣ Layerwise File")
        layerwise_file = st.file_uploader(
            "Upload Layerwise Excel file",
            type=['xlsx', 'xls'],
            help="File containing State (Suspect State) column",
            key="workflow_layerwise"
        )
    
    with col2:
        st.markdown("#### 2️⃣ Fraud Amount File")
        fraud_file = st.file_uploader(
            "Upload Fraud Amount Excel file",
            type=['xlsx', 'xls'],
            help="File containing Amount Reported column",
            key="workflow_fraud"
        )
    
    if layerwise_file is not None and fraud_file is not None:
        try:
            # Read files
            with st.spinner("Reading files..."):
                layerwise_df = pd.read_excel(layerwise_file)
                fraud_df = pd.read_excel(fraud_file)
            
            st.success(f"✅ Layerwise: {len(layerwise_df):,} rows | Fraud Amount: {len(fraud_df):,} rows")
            
            # Show preview
            with st.expander("👁️ Preview Files"):
                col_prev1, col_prev2 = st.columns(2)
                with col_prev1:
                    st.markdown("**Layerwise File:**")
                    st.dataframe(layerwise_df.head(5))
                with col_prev2:
                    st.markdown("**Fraud Amount File:**")
                    st.dataframe(fraud_df.head(5))
            
            # Column selection
            st.markdown("---")
            st.markdown("### 🎯 Step 2: Map Columns to Output Format")
            
            st.info("📋 Map your file columns to the required output format (16 columns)")
            
            # Required output columns (15 columns - Transaction Amount is ONE column)
            required_columns = [
                "S No.",
                "Acknowledgement No.",
                "Victim District",
                "Victim State",
                "Reported Amount (Victim)",
                "Account No.",
                "IFSC Code",
                "Address",
                "District",
                "State",
                "Pin Code",
                "Transaction Amount",
                "Disputed Amount",
                "Bank/FIs",
                "Layers"
            ]
            
            # Initialize session state for column mappings if not exists
            if 'workflow_column_mapping' not in st.session_state:
                # Load saved mappings from file
                st.session_state.workflow_column_mapping = load_column_mappings()
            
            st.markdown("#### 🔗 Matching Columns (Required)")
            
            # Show info about saved mappings
            if st.session_state.workflow_column_mapping:
                st.success("✅ Using saved column mappings from previous session")
            
            col_sel1, col_sel2 = st.columns(2)
            
            with col_sel1:
                # Get previous value from session state
                prev_victim = st.session_state.workflow_column_mapping.get('_victim_col', "-- Select --")
                victim_idx = 0
                if prev_victim in fraud_df.columns:
                    victim_idx = list(fraud_df.columns).index(prev_victim) + 1
                
                victim_col = st.selectbox(
                    "Victim Column (Fraud file):",
                    options=["-- Select --"] + list(fraud_df.columns),
                    index=victim_idx,
                    key="workflow_victim",
                    help="Select Victim column from Fraud Amount file for matching"
                )
                if victim_col != st.session_state.workflow_column_mapping.get('_victim_col'):
                    st.session_state.workflow_column_mapping['_victim_col'] = victim_col
                    save_column_mappings(st.session_state.workflow_column_mapping)
            
            with col_sel2:
                # Get previous value from session state
                prev_suspect = st.session_state.workflow_column_mapping.get('_suspect_col', "-- Select --")
                suspect_idx = 0
                if prev_suspect in layerwise_df.columns:
                    suspect_idx = list(layerwise_df.columns).index(prev_suspect) + 1
                
                suspect_col = st.selectbox(
                    "Suspect Column (Layerwise):",
                    options=["-- Select --"] + list(layerwise_df.columns),
                    index=suspect_idx,
                    key="workflow_suspect",
                    help="Select Suspect column from Layerwise file for matching"
                )
                if suspect_col != st.session_state.workflow_column_mapping.get('_suspect_col'):
                    st.session_state.workflow_column_mapping['_suspect_col'] = suspect_col
                    save_column_mappings(st.session_state.workflow_column_mapping)
            
            st.markdown("#### 📊 Output Column Mapping")
            st.markdown("Map your file columns to the required output format (mappings are saved):")
            
            # Create column mapping
            column_mapping = {}
            
            # Helper function to get previous selection
            def get_prev_selection(col_name, default="-- Skip --"):
                return st.session_state.workflow_column_mapping.get(col_name, default)
            
            # Helper function to get index
            def get_col_index(col_name, columns, default_col=None):
                prev = get_prev_selection(col_name, default_col if default_col else "-- Skip --")
                if prev in columns:
                    return list(columns).index(prev) + 1
                elif default_col and default_col in columns:
                    return list(columns).index(default_col) + 1
                return 0
            
            # Split into 4 columns for better layout
            map_col1, map_col2, map_col3, map_col4 = st.columns(4)
            
            with map_col1:
                st.markdown("**Columns 1-4:**")
                # S No. is auto-generated
                st.text("1. S No. (Auto)")
                
                column_mapping["Acknowledgement No."] = st.selectbox(
                    "2. Acknowledgement No.",
                    options=["-- Skip --"] + list(layerwise_df.columns),
                    index=get_col_index("Acknowledgement No.", layerwise_df.columns),
                    key="map_ack",
                    help="From Layerwise file"
                )
                if column_mapping["Acknowledgement No."] != st.session_state.workflow_column_mapping.get("Acknowledgement No."):
                    st.session_state.workflow_column_mapping["Acknowledgement No."] = column_mapping["Acknowledgement No."]
                    save_column_mappings(st.session_state.workflow_column_mapping)
                
                column_mapping["Victim District"] = st.selectbox(
                    "3. Victim District",
                    options=["-- Skip --"] + list(fraud_df.columns),
                    index=get_col_index("Victim District", fraud_df.columns, "Victim District"),
                    key="map_vict_dist",
                    help="From Fraud Amount file"
                )
                if column_mapping["Victim District"] != st.session_state.workflow_column_mapping.get("Victim District"):
                    st.session_state.workflow_column_mapping["Victim District"] = column_mapping["Victim District"]
                    save_column_mappings(st.session_state.workflow_column_mapping)
                
                column_mapping["Victim State"] = st.selectbox(
                    "4. Victim State",
                    options=["-- Skip --"] + list(fraud_df.columns),
                    index=get_col_index("Victim State", fraud_df.columns),
                    key="map_vict_state",
                    help="From Fraud Amount file"
                )
                if column_mapping["Victim State"] != st.session_state.workflow_column_mapping.get("Victim State"):
                    st.session_state.workflow_column_mapping["Victim State"] = column_mapping["Victim State"]
                    save_column_mappings(st.session_state.workflow_column_mapping)
            
            with map_col2:
                st.markdown("**Columns 5-8:**")
                
                column_mapping["Reported Amount (Victim)"] = st.selectbox(
                    "5. Reported Amount",
                    options=["-- Skip --"] + list(fraud_df.columns),
                    index=get_col_index("Reported Amount (Victim)", fraud_df.columns, "Amount Reported"),
                    key="map_amount",
                    help="From Fraud Amount file"
                )
                if column_mapping["Reported Amount (Victim)"] != st.session_state.workflow_column_mapping.get("Reported Amount (Victim)"):
                    st.session_state.workflow_column_mapping["Reported Amount (Victim)"] = column_mapping["Reported Amount (Victim)"]
                    save_column_mappings(st.session_state.workflow_column_mapping)
                
                column_mapping["Account No."] = st.selectbox(
                    "6. Account No.",
                    options=["-- Skip --"] + list(layerwise_df.columns),
                    index=get_col_index("Account No.", layerwise_df.columns),
                    key="map_account",
                    help="From Layerwise file"
                )
                if column_mapping["Account No."] != st.session_state.workflow_column_mapping.get("Account No."):
                    st.session_state.workflow_column_mapping["Account No."] = column_mapping["Account No."]
                    save_column_mappings(st.session_state.workflow_column_mapping)
                
                column_mapping["IFSC Code"] = st.selectbox(
                    "7. IFSC Code",
                    options=["-- Skip --"] + list(layerwise_df.columns),
                    index=get_col_index("IFSC Code", layerwise_df.columns),
                    key="map_ifsc",
                    help="From Layerwise file"
                )
                if column_mapping["IFSC Code"] != st.session_state.workflow_column_mapping.get("IFSC Code"):
                    st.session_state.workflow_column_mapping["IFSC Code"] = column_mapping["IFSC Code"]
                    save_column_mappings(st.session_state.workflow_column_mapping)
                
                column_mapping["Address"] = st.selectbox(
                    "8. Address",
                    options=["-- Skip --"] + list(layerwise_df.columns),
                    index=get_col_index("Address", layerwise_df.columns),
                    key="map_address",
                    help="From Layerwise file"
                )
                if column_mapping["Address"] != st.session_state.workflow_column_mapping.get("Address"):
                    st.session_state.workflow_column_mapping["Address"] = column_mapping["Address"]
                    save_column_mappings(st.session_state.workflow_column_mapping)
            
            with map_col3:
                st.markdown("**Columns 9-12:**")
                
                column_mapping["District"] = st.selectbox(
                    "9. District (Suspect)",
                    options=["-- Skip --"] + list(layerwise_df.columns),
                    index=get_col_index("District", layerwise_df.columns),
                    key="map_district",
                    help="From Layerwise file"
                )
                if column_mapping["District"] != st.session_state.workflow_column_mapping.get("District"):
                    st.session_state.workflow_column_mapping["District"] = column_mapping["District"]
                    save_column_mappings(st.session_state.workflow_column_mapping)
                
                column_mapping["State"] = st.selectbox(
                    "10. State (Suspect)",
                    options=["-- Skip --"] + list(layerwise_df.columns),
                    index=get_col_index("State", layerwise_df.columns, "State"),
                    key="map_state",
                    help="From Layerwise file"
                )
                if column_mapping["State"] != st.session_state.workflow_column_mapping.get("State"):
                    st.session_state.workflow_column_mapping["State"] = column_mapping["State"]
                    save_column_mappings(st.session_state.workflow_column_mapping)
                
                column_mapping["Pin Code"] = st.selectbox(
                    "11. Pin Code",
                    options=["-- Skip --"] + list(layerwise_df.columns),
                    index=get_col_index("Pin Code", layerwise_df.columns),
                    key="map_pin",
                    help="From Layerwise file"
                )
                if column_mapping["Pin Code"] != st.session_state.workflow_column_mapping.get("Pin Code"):
                    st.session_state.workflow_column_mapping["Pin Code"] = column_mapping["Pin Code"]
                    save_column_mappings(st.session_state.workflow_column_mapping)
                
                column_mapping["Transaction Amount"] = st.selectbox(
                    "12. Transaction Amount",
                    options=["-- Skip --"] + list(layerwise_df.columns),
                    index=get_col_index("Transaction Amount", layerwise_df.columns),
                    key="map_transaction_amount",
                    help="From Layerwise file (Transaction Amount in one column)"
                )
                if column_mapping["Transaction Amount"] != st.session_state.workflow_column_mapping.get("Transaction Amount"):
                    st.session_state.workflow_column_mapping["Transaction Amount"] = column_mapping["Transaction Amount"]
                    save_column_mappings(st.session_state.workflow_column_mapping)
            
            with map_col4:
                st.markdown("**Columns 13-15:**")
                
                column_mapping["Disputed Amount"] = st.selectbox(
                    "13. Disputed Amount",
                    options=["-- Skip --"] + list(layerwise_df.columns),
                    index=get_col_index("Disputed Amount", layerwise_df.columns),
                    key="map_disputed",
                    help="From Layerwise file"
                )
                if column_mapping["Disputed Amount"] != st.session_state.workflow_column_mapping.get("Disputed Amount"):
                    st.session_state.workflow_column_mapping["Disputed Amount"] = column_mapping["Disputed Amount"]
                    save_column_mappings(st.session_state.workflow_column_mapping)
                
                column_mapping["Bank/FIs"] = st.selectbox(
                    "14. Bank/FIs",
                    options=["-- Skip --"] + list(layerwise_df.columns),
                    index=get_col_index("Bank/FIs", layerwise_df.columns),
                    key="map_bank",
                    help="From Layerwise file"
                )
                if column_mapping["Bank/FIs"] != st.session_state.workflow_column_mapping.get("Bank/FIs"):
                    st.session_state.workflow_column_mapping["Bank/FIs"] = column_mapping["Bank/FIs"]
                    save_column_mappings(st.session_state.workflow_column_mapping)
                
                column_mapping["Layers"] = st.selectbox(
                    "15. Layers",
                    options=["-- Skip --"] + list(layerwise_df.columns),
                    index=get_col_index("Layers", layerwise_df.columns),
                    key="map_layers",
                    help="From Layerwise file"
                )
                if column_mapping["Layers"] != st.session_state.workflow_column_mapping.get("Layers"):
                    st.session_state.workflow_column_mapping["Layers"] = column_mapping["Layers"]
                    save_column_mappings(st.session_state.workflow_column_mapping)
            
            # Validation
            if victim_col == "-- Select --" or suspect_col == "-- Select --":
                st.warning("⚠️ Please select Victim and Suspect columns for matching")
                return
            
            # Get required columns for filtering
            state_col = column_mapping.get("State", "-- Skip --")
            amount_col = column_mapping.get("Reported Amount (Victim)", "-- Skip --")
            district_col = column_mapping.get("Victim District", "-- Skip --")
            
            if state_col == "-- Skip --":
                st.warning("⚠️ Please map 'State (Suspect)' column for Gujarat/Non-Gujarat filtering")
                return
            
            if amount_col == "-- Skip --":
                st.warning("⚠️ Please map 'Reported Amount' column for 5 Lacs filtering")
                return
            
            if district_col == "-- Skip --":
                st.warning("⚠️ Please map 'Victim District' column for district-wise splitting")
                return
            
            # Process button
            st.markdown("---")
            if st.button("🚀 Start Automated Processing", type="primary", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # STEP 1: Match files
                    status_text.text("Step 1/4: Matching Layerwise and Fraud Amount files...")
                    progress_bar.progress(10)
                    
                    # Merge: Layerwise is MASTER (left join), Fraud Amount enriches it
                    # Suspect (from Layerwise) matches Victim (from Fraud Amount)
                    matched_df = pd.merge(
                        layerwise_df,
                        fraud_df,
                        left_on=suspect_col,
                        right_on=victim_col,
                        how='left',  # Keep ALL records from Layerwise
                        suffixes=('_suspect', '_victim')
                    )
                    
                    st.success(f"✅ Matched {len(matched_df):,} records from Layerwise file (master)")
                    progress_bar.progress(15)
                    
                    # STEP 2: Build output with ONLY required 15 columns in exact order
                    status_text.text("Step 2/5: Building output columns...")
                    
                    # Create new dataframe with only required columns
                    output_df = pd.DataFrame()
                    
                    # 1. S No. - Will be added later per file
                    
                    # 2. Acknowledgement No.
                    ack_col = column_mapping.get("Acknowledgement No.", "-- Skip --")
                    if ack_col != "-- Skip --":
                        if ack_col in matched_df.columns:
                            output_df["Acknowledgement No."] = matched_df[ack_col]
                        elif f"{ack_col}_suspect" in matched_df.columns:
                            output_df["Acknowledgement No."] = matched_df[f"{ack_col}_suspect"]
                    else:
                        output_df["Acknowledgement No."] = ""
                    
                    # 3. Victim District (from Fraud file)
                    if district_col != "-- Skip --":
                        if district_col in matched_df.columns:
                            output_df["Victim District"] = matched_df[district_col]
                        elif f"{district_col}_victim" in matched_df.columns:
                            output_df["Victim District"] = matched_df[f"{district_col}_victim"]
                    else:
                        output_df["Victim District"] = ""
                    
                    # 4. Victim State (from Fraud file)
                    vict_state_col = column_mapping.get("Victim State", "-- Skip --")
                    if vict_state_col != "-- Skip --":
                        if vict_state_col in matched_df.columns:
                            output_df["Victim State"] = matched_df[vict_state_col]
                        elif f"{vict_state_col}_victim" in matched_df.columns:
                            output_df["Victim State"] = matched_df[f"{vict_state_col}_victim"]
                    else:
                        output_df["Victim State"] = ""
                    
                    # 5. Reported Amount (Victim) (from Fraud file)
                    if amount_col != "-- Skip --":
                        if amount_col in matched_df.columns:
                            output_df["Reported Amount (Victim)"] = matched_df[amount_col]
                        elif f"{amount_col}_victim" in matched_df.columns:
                            output_df["Reported Amount (Victim)"] = matched_df[f"{amount_col}_victim"]
                    else:
                        output_df["Reported Amount (Victim)"] = ""
                    
                    # 6-15: Map remaining columns from Layerwise file
                    remaining_cols = [
                        "Account No.", "IFSC Code", "Address", "District", "State",
                        "Pin Code", "Transaction Amount", "Disputed Amount", "Bank/FIs", "Layers"
                    ]
                    
                    for col_name in remaining_cols:
                        source_col = column_mapping.get(col_name, "-- Skip --")
                        if source_col != "-- Skip --":
                            if source_col in matched_df.columns:
                                output_df[col_name] = matched_df[source_col]
                            elif f"{source_col}_suspect" in matched_df.columns:
                                output_df[col_name] = matched_df[f"{source_col}_suspect"]
                            else:
                                output_df[col_name] = ""
                        else:
                            output_df[col_name] = ""
                    
                    # Store state and amount columns for filtering
                    state_column = "State"  # Column 10 in output
                    amount_column = "Reported Amount (Victim)"  # Column 5 in output
                    district_column = "Victim District"  # Column 3 in output
                    
                    st.success(f"✅ Built output with 15 required columns")
                    progress_bar.progress(20)
                    
                    # FILTER: Only keep records where ACK starts with "311"
                    status_text.text("Step 2.5/4: Filtering ACK numbers starting with 311...")
                    
                    original_count = len(output_df)
                    ack_column = "Acknowledgement No."
                    
                    if ack_column in output_df.columns:
                        # Filter for ACK numbers starting with "311"
                        output_df = output_df[output_df[ack_column].astype(str).str.startswith('311', na=False)].copy()
                        filtered_count = len(output_df)
                        excluded_count = original_count - filtered_count
                        
                        st.success(f"✅ ACK Filter Applied: {filtered_count:,} records kept, {excluded_count:,} excluded (non-311 ACK)")
                        
                        # Show debug info
                        with st.expander("🔍 Debug: ACK Filter Results"):
                            st.write(f"**Original Records:** {original_count:,}")
                            st.write(f"**Records with ACK starting with '311':** {filtered_count:,}")
                            st.write(f"**Excluded Records (non-311 ACK):** {excluded_count:,}")
                            if filtered_count > 0:
                                st.write(f"**Sample ACK numbers (first 10):**")
                                sample_acks = output_df[ack_column].head(10).tolist()
                                for i, ack in enumerate(sample_acks, 1):
                                    st.write(f"{i}. {ack}")
                    else:
                        st.warning("⚠️ ACK column not found - skipping ACK filter")
                    
                    progress_bar.progress(25)
                    
                    # STEP 3: Generate 4 filtered files
                    status_text.text("Step 3/4: Generating filtered files...")
                    
                    # CRITICAL: Convert Amount to numeric FIRST for accurate filtering (legal data)
                    # Remove any commas, spaces, or currency symbols before conversion
                    output_df[amount_column] = output_df[amount_column].astype(str).str.replace(',', '').str.replace('₹', '').str.replace('Rs', '').str.replace('rs', '').str.strip()
                    output_df[amount_column] = pd.to_numeric(output_df[amount_column], errors='coerce').fillna(0)
                    
                    # Debug: Show amount column info
                    with st.expander("🔍 Debug: Amount Column Info"):
                        st.write(f"**Amount Column Used:** {amount_column}")
                        st.write(f"**Data Type:** {output_df[amount_column].dtype}")
                        st.write(f"**Non-null Count:** {output_df[amount_column].notna().sum():,}")
                        st.write(f"**Records with Amount > 0:** {(output_df[amount_column] > 0).sum():,}")
                        st.write(f"**Records with Amount >= 5,00,000:** {(output_df[amount_column] >= 500000).sum():,}")
                        st.write(f"**Max Amount:** ₹{output_df[amount_column].max():,.2f}")
                        st.write(f"**Sample Values (first 10):**")
                        st.dataframe(output_df[[state_column, amount_column]].head(10))
                    
                    progress_bar.progress(30)
                    
                    # File 1: All Matched Data
                    file1_all = output_df.copy()
                    
                    # File 2: Gujarat Only
                    file2_gujarat = output_df[output_df[state_column].astype(str).str.upper().str.contains('GUJARAT|GUJRAT|GUJ', na=False)].copy()
                    
                    # File 3: 5 Lacs Plus (Amount >= 500000)
                    file3_5lacs = output_df[output_df[amount_column] >= 500000].copy()
                    
                    # File 4: Gujarat 5 Lacs Plus
                    file4_gujarat_5lacs = file3_5lacs[file3_5lacs[state_column].astype(str).str.upper().str.contains('GUJARAT|GUJRAT|GUJ', na=False)].copy()
                    
                    # Debug: Show filtering results
                    with st.expander("🔍 Debug: Filtering Results"):
                        st.write(f"**File 3 (5L+) Count:** {len(file3_5lacs):,}")
                        if len(file3_5lacs) > 0:
                            st.write(f"**Amount Range in 5L+ data:** ₹{file3_5lacs[amount_column].min():,.2f} to ₹{file3_5lacs[amount_column].max():,.2f}")
                            st.write(f"**Sample 5L+ records:**")
                            st.dataframe(file3_5lacs[[state_column, amount_column]].head(10))
                        else:
                            st.warning("⚠️ No records found with Amount >= 5,00,000")
                            st.write(f"**This might indicate:**")
                            st.write("- Amount column has no values >= 5,00,000")
                            st.write("- Amount column needs different cleaning")
                            st.write("- Check if amounts are in different units (e.g., thousands)")
                    
                    st.success(f"✅ File 1 (All): {len(file1_all):,} | File 2 (Gujarat): {len(file2_gujarat):,} | File 3 (5L+): {len(file3_5lacs):,} | File 4 (Guj 5L+): {len(file4_gujarat_5lacs):,}")
                    
                    # Show unique account counts for all files
                    account_col_name = "Account No."
                    if account_col_name in file1_all.columns:
                        st.markdown("#### 📊 Unique Account Statistics")
                        
                        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
                        
                        unique_acc_1 = file1_all[account_col_name].nunique()
                        unique_acc_2 = file2_gujarat[account_col_name].nunique()
                        unique_acc_3 = file3_5lacs[account_col_name].nunique()
                        unique_acc_4 = file4_gujarat_5lacs[account_col_name].nunique()
                        
                        with stats_col1:
                            st.metric("File 1 (All)", f"{len(file1_all):,} rows", f"{unique_acc_1:,} unique accounts")
                        
                        with stats_col2:
                            st.metric("File 2 (Gujarat)", f"{len(file2_gujarat):,} rows", f"{unique_acc_2:,} unique accounts")
                        
                        with stats_col3:
                            st.metric("File 3 (5L+)", f"{len(file3_5lacs):,} rows", f"{unique_acc_3:,} unique accounts")
                        
                        with stats_col4:
                            st.metric("File 4 (Guj 5L+)", f"{len(file4_gujarat_5lacs):,} rows", f"{unique_acc_4:,} unique accounts")
                        
                        # Store for later use
                        st.session_state.workflow_stats_1_4 = {
                            'unique_acc_1': unique_acc_1,
                            'unique_acc_2': unique_acc_2,
                            'unique_acc_3': unique_acc_3,
                            'unique_acc_4': unique_acc_4,
                            'total_rows_1': len(file1_all),
                            'total_rows_2': len(file2_gujarat),
                            'total_rows_3': len(file3_5lacs),
                            'total_rows_4': len(file4_gujarat_5lacs)
                        }
                    
                    progress_bar.progress(50)
                    
                    # STEP 4: Non-Gujarat Filter
                    status_text.text("Step 4/4: Filtering Non-Gujarat data...")
                    
                    # File 5: Non-Gujarat (from File 1)
                    file5_non_guj = file1_all[~file1_all[state_column].astype(str).str.upper().str.contains('GUJARAT|GUJRAT|GUJ', na=False)].copy()
                    
                    # File 6: Non-Gujarat 5 Lacs Plus (from File 3)
                    file6_non_guj_5lacs = file3_5lacs[~file3_5lacs[state_column].astype(str).str.upper().str.contains('GUJARAT|GUJRAT|GUJ', na=False)].copy()
                    
                    st.success(f"✅ File 5 (Non-Guj): {len(file5_non_guj):,} | File 6 (Non-Guj 5L+): {len(file6_non_guj_5lacs):,}")
                    
                    # Show unique account counts for Non-Gujarat files
                    if account_col_name in file5_non_guj.columns:
                        stats_col5, stats_col6 = st.columns(2)
                        
                        unique_acc_5 = file5_non_guj[account_col_name].nunique()
                        unique_acc_6 = file6_non_guj_5lacs[account_col_name].nunique()
                        
                        with stats_col5:
                            st.metric("File 5 (Non-Gujarat)", f"{len(file5_non_guj):,} rows", f"{unique_acc_5:,} unique accounts")
                        
                        with stats_col6:
                            st.metric("File 6 (Non-Guj 5L+)", f"{len(file6_non_guj_5lacs):,} rows", f"{unique_acc_6:,} unique accounts")
                        
                        # Create copyable summary text
                        st.markdown("---")
                        st.markdown("#### *Daily Report Summary*")
                        
                        # Get previous day's date
                        from datetime import timedelta
                        previous_date = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")
                        
                        # Get stats from session state
                        stats_1_4 = st.session_state.get('workflow_stats_1_4', {})
                        unique_acc_1 = stats_1_4.get('unique_acc_1', 0)
                        unique_acc_2 = stats_1_4.get('unique_acc_2', 0)
                        unique_acc_3 = stats_1_4.get('unique_acc_3', 0)
                        unique_acc_4 = stats_1_4.get('unique_acc_4', 0)
                        total_rows_1 = stats_1_4.get('total_rows_1', 0)
                        total_rows_2 = stats_1_4.get('total_rows_2', 0)
                        total_rows_3 = stats_1_4.get('total_rows_3', 0)
                        total_rows_4 = stats_1_4.get('total_rows_4', 0)
                        
                        # Calculate Non-Gujarat from All - Gujarat
                        non_guj_from_all = unique_acc_1 - unique_acc_2
                        non_guj_5l_from_5l = unique_acc_3 - unique_acc_4
                        non_guj_rows = total_rows_1 - total_rows_2
                        non_guj_5l_rows = total_rows_3 - total_rows_4
                        
                        # Calculate percentages for Gujarat
                        guj_acc_pct = (unique_acc_2 / unique_acc_1 * 100) if unique_acc_1 > 0 else 0
                        guj_5l_acc_pct = (unique_acc_4 / unique_acc_3 * 100) if unique_acc_3 > 0 else 0
                        guj_rows_pct = (total_rows_2 / total_rows_1 * 100) if total_rows_1 > 0 else 0
                        guj_5l_rows_pct = (total_rows_4 / total_rows_3 * 100) if total_rows_3 > 0 else 0
                        
                        # Calculate Top 5 Victim Districts from ORIGINAL fraud amount file (by complaint count)
                        # Note: Each ACK is unique in fraud amount file, so we count records per district
                        victim_district_counts = {}
                        
                        # Get the mapped district column name from fraud file
                        fraud_district_col = column_mapping.get("Victim District", "-- Skip --")
                        
                        if fraud_district_col != "-- Skip --" and fraud_district_col in fraud_df.columns and len(fraud_df) > 0:
                            # Use ORIGINAL fraud_df, not merged output_df
                            temp_fraud = fraud_df.copy()
                            temp_fraud['clean_district'] = temp_fraud[fraud_district_col].astype(str).str.strip().str.upper()
                            
                            # Remove empty/null districts
                            temp_fraud = temp_fraud[temp_fraud['clean_district'].notna() & 
                                                   (temp_fraud['clean_district'] != '') & 
                                                   (temp_fraud['clean_district'] != 'NAN')]
                            
                            # Count records per district (each record = 1 complaint since ACKs are unique)
                            victim_counts = temp_fraud['clean_district'].value_counts().head(5)
                            
                            for i, (district, count) in enumerate(victim_counts.items(), 1):
                                if pd.notna(district) and str(district).strip():
                                    # Convert to title case for better readability
                                    district_display = district.title()
                                    victim_district_counts[i] = f"{district_display} - {count}"
                        
                        # Calculate Top 5 Suspect Districts from layerwise data (Gujarat only, by transaction count)
                        suspect_district_counts = {}
                        suspect_district_col = "District"  # Column 9 in output (Suspect District)
                        suspect_state_col = "State"  # Column 10 in output (Suspect State)
                        if suspect_district_col in output_df.columns and suspect_state_col in output_df.columns and len(output_df) > 0:
                            # Filter for Gujarat state only
                            gujarat_data = output_df[output_df[suspect_state_col].astype(str).str.upper().str.contains('GUJARAT|GUJRAT|GUJ', na=False)].copy()
                            
                            if len(gujarat_data) > 0:
                                # Clean district names
                                gujarat_data['clean_suspect_district'] = gujarat_data[suspect_district_col].astype(str).str.strip().str.upper()
                                
                                # Remove empty/null districts
                                gujarat_data = gujarat_data[gujarat_data['clean_suspect_district'].notna() & 
                                                           (gujarat_data['clean_suspect_district'] != '') & 
                                                           (gujarat_data['clean_suspect_district'] != 'NAN')]
                                
                                # Count transactions per district
                                suspect_counts = gujarat_data['clean_suspect_district'].value_counts().head(5)
                                
                                for i, (district, count) in enumerate(suspect_counts.items(), 1):
                                    if pd.notna(district) and str(district).strip():
                                        # Convert to title case for better readability
                                        district_display = district.title()
                                        suspect_district_counts[i] = f"{district_display} - {count:02d}"
                        
                        # Create unified summary report with percentages
                        summary_report = f"""Date: {previous_date}

*• Unique Account Counts*
  • All: {unique_acc_1:,}
  • Gujarat: {unique_acc_2:,} ({guj_acc_pct:.2f}%)
  • Non Gujarat: {non_guj_from_all:,}
  • All 5L Plus: {unique_acc_3:,}
  • Gujarat 5L Plus: {unique_acc_4:,} ({guj_5l_acc_pct:.2f}%)
  • Non Gujarat 5L Plus: {non_guj_5l_from_5l:,}

*• Total L1 Transaction Records*
  • All: {total_rows_1:,}
  • Gujarat: {total_rows_2:,} ({guj_rows_pct:.2f}%)
  • Non Gujarat: {non_guj_rows:,}
  • All 5L Plus: {total_rows_3:,}
  • Gujarat 5L Plus: {total_rows_4:,} ({guj_5l_rows_pct:.2f}%)
  • Non Gujarat 5L Plus: {non_guj_5l_rows:,}

*•  Top 5 Victim Districts/Cities (By the number of complaints)*"""
                        
                        for i in range(1, 6):
                            if i in victim_district_counts:
                                summary_report += f"\n  {i}. {victim_district_counts[i]}"
                            else:
                                summary_report += f"\n  {i}. No data - 00"
                        
                        summary_report += "\n\n*•  Top 5 Suspect Districts/Cities (By the number of transactions)*"
                        
                        for i in range(1, 6):
                            if i in suspect_district_counts:
                                summary_report += f"\n  {i}. {suspect_district_counts[i]}"
                            else:
                                summary_report += f"\n  {i}. No data - 00"
                        
                        st.code(summary_report, language=None)
                       
                    
                    progress_bar.progress(60)
                    
                    # Add S No. to all files
                    for file_df in [file1_all, file2_gujarat, file3_5lacs, file4_gujarat_5lacs, file5_non_guj, file6_non_guj_5lacs]:
                        if len(file_df) > 0:
                            file_df.insert(0, 'S No.', range(1, len(file_df) + 1))
                    
                    # STEP 5: Split by District (4 ZIP files)
                    status_text.text("Step 5/5: Splitting by district and creating ZIP files...")
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    # Store all ZIP files
                    zip_files = {}
                    
                    # Process each file
                    files_to_split = [
                        (file2_gujarat, "Gujarat"),
                        (file4_gujarat_5lacs, "Gujarat_5Lacs_Plus"),
                        (file5_non_guj, "Non_Gujarat"),
                        (file6_non_guj_5lacs, "Non_Gujarat_5Lacs_Plus")
                    ]
                    
                    for idx, (df_to_split, zip_name) in enumerate(files_to_split):
                        if len(df_to_split) == 0:
                            st.warning(f"⚠️ {zip_name}: No data to split")
                            continue
                        
                        # Check if district column exists in this dataframe
                        if district_column not in df_to_split.columns:
                            st.error(f"❌ {zip_name}: District column '{district_column}' not found. Available columns: {list(df_to_split.columns)}")
                            continue
                        
                        # Create ZIP file
                        zip_buffer = io.BytesIO()
                        
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            # Get unique districts
                            unique_districts = df_to_split[district_column].dropna().unique()
                            
                            if len(unique_districts) == 0:
                                st.warning(f"⚠️ {zip_name}: No districts found (all values are null)")
                                continue
                            
                            for district in unique_districts:
                                # Filter by district
                                district_df = df_to_split[df_to_split[district_column] == district].copy()
                                
                                # Reset S No. for this district (renumber from 1)
                                if 'S No.' in district_df.columns:
                                    district_df['S No.'] = range(1, len(district_df) + 1)
                                
                                # Create Excel file
                                excel_buffer = io.BytesIO()
                                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                                    district_df.to_excel(writer, sheet_name='Data', index=False)
                                
                                # Clean district name for filename
                                clean_district = str(district).replace('/', '_').replace('\\', '_').replace(':', '_')
                                filename = f"{clean_district}.xlsx"
                                
                                # Add to ZIP
                                zip_file.writestr(filename, excel_buffer.getvalue())
                        
                        zip_files[zip_name] = zip_buffer.getvalue()
                        st.success(f"✅ {zip_name}.zip: {len(unique_districts)} districts")
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Processing complete!")
                    
                    # Store in session state
                    st.session_state.workflow_files = {
                        'file1_all': file1_all,
                        'file2_gujarat': file2_gujarat,
                        'file3_5lacs': file3_5lacs,
                        'file4_gujarat_5lacs': file4_gujarat_5lacs,
                        'file5_non_guj': file5_non_guj,
                        'file6_non_guj_5lacs': file6_non_guj_5lacs
                    }
                    st.session_state.workflow_zips = zip_files
                    st.session_state.workflow_timestamp = timestamp
                    
                    st.success("🎉 All processing complete! Download your files below.")
                    
                except Exception as e:
                    st.error(f"❌ Error during processing: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
            
            # Download section
            if 'workflow_files' in st.session_state and st.session_state.workflow_files:
                st.markdown("---")
                st.markdown("### 📥 Download Processed Files")
                
                timestamp = st.session_state.workflow_timestamp
                files = st.session_state.workflow_files
                zips = st.session_state.workflow_zips
                
                # Excel files (6 files)
                st.markdown("#### 📊 Excel Files (Individual)")
                
                dl_col1, dl_col2, dl_col3 = st.columns(3)
                
                with dl_col1:
                    # File 1
                    excel_buffer1 = io.BytesIO()
                    files['file1_all'].to_excel(excel_buffer1, index=False)
                    st.download_button(
                        "⬇️ 1. All Matched Data",
                        data=excel_buffer1.getvalue(),
                        file_name=f"All_Matched_{timestamp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="dl1"
                    )
                    
                    # File 4
                    excel_buffer4 = io.BytesIO()
                    files['file4_gujarat_5lacs'].to_excel(excel_buffer4, index=False)
                    st.download_button(
                        "⬇️ 4. Gujarat 5 Lacs Plus",
                        data=excel_buffer4.getvalue(),
                        file_name=f"Gujarat_5Lacs_Plus_{timestamp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="dl4"
                    )
                
                with dl_col2:
                    # File 2
                    excel_buffer2 = io.BytesIO()
                    files['file2_gujarat'].to_excel(excel_buffer2, index=False)
                    st.download_button(
                        "⬇️ 2. Gujarat Only",
                        data=excel_buffer2.getvalue(),
                        file_name=f"Gujarat_{timestamp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="dl2"
                    )
                    
                    # File 5
                    excel_buffer5 = io.BytesIO()
                    files['file5_non_guj'].to_excel(excel_buffer5, index=False)
                    st.download_button(
                        "⬇️ 5. Non-Gujarat",
                        data=excel_buffer5.getvalue(),
                        file_name=f"Non_Gujarat_{timestamp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="dl5"
                    )
                
                with dl_col3:
                    # File 3
                    excel_buffer3 = io.BytesIO()
                    files['file3_5lacs'].to_excel(excel_buffer3, index=False)
                    st.download_button(
                        "⬇️ 3. 5 Lacs Plus",
                        data=excel_buffer3.getvalue(),
                        file_name=f"5Lacs_Plus_{timestamp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="dl3"
                    )
                    
                    # File 6
                    excel_buffer6 = io.BytesIO()
                    files['file6_non_guj_5lacs'].to_excel(excel_buffer6, index=False)
                    st.download_button(
                        "⬇️ 6. Non-Gujarat 5 Lacs Plus",
                        data=excel_buffer6.getvalue(),
                        file_name=f"Non_Gujarat_5Lacs_Plus_{timestamp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="dl6"
                    )
                
                # ZIP files (4 files)
                st.markdown("#### 📦 ZIP Files (District-wise Split)")
                
                zip_col1, zip_col2, zip_col3, zip_col4 = st.columns(4)
                
                zip_buttons = [
                    (zip_col1, "Gujarat", "Gujarat"),
                    (zip_col2, "Gujarat_5Lacs_Plus", "Gujarat 5L+"),
                    (zip_col3, "Non_Gujarat", "Non-Gujarat"),
                    (zip_col4, "Non_Gujarat_5Lacs_Plus", "Non-Guj 5L+")
                ]
                
                for col, zip_key, label in zip_buttons:
                    with col:
                        if zip_key in zips:
                            st.download_button(
                                f"⬇️ {label}",
                                data=zips[zip_key],
                                file_name=f"{zip_key}_{timestamp}.zip",
                                mime="application/zip",
                                key=f"dlzip_{zip_key}"
                            )
                        else:
                            st.info(f"No data for {label}")
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    
    else:
        st.info("👆 Please upload both files to get started")
        
        with st.expander("ℹ️ Workflow Details"):
            st.markdown("""
            ### Automated Workflow Steps:
            
            **Step 1: Match Files**
            - **Layerwise is MASTER file** (all records kept)
            - Fraud Amount file enriches the data
            - Suspect (Layerwise) matches Victim (Fraud Amount)
            - Unmatched Layerwise records are kept with blank Fraud Amount data
            
            **Step 2: Build Output (15 Columns)**
            - Maps your columns to standardized output format
            - **Column mappings are saved** - will remember your selections next time
            - Only 15 required columns in exact order
            
            **Step 3: Generate 4 Filtered Files**
            1. **All Matched Data**: Complete dataset from Layerwise
            2. **Gujarat Only**: State (col 10) = Gujarat
            3. **5 Lacs Plus**: Reported Amount (col 5) >= ₹5,00,000
            4. **Gujarat 5 Lacs Plus**: Gujarat + Amount >= ₹5,00,000
            
            **Step 4: Non-Gujarat Filter (Auto)**
            5. **Non-Gujarat**: All data except Gujarat (State col 10)
            6. **Non-Gujarat 5 Lacs Plus**: 5L+ data except Gujarat
            
            **Step 5: Split by District (Auto)**
            - Creates 4 ZIP files, each containing district-wise Excel files:
              - Gujarat.zip (by Victim District - col 3)
              - Gujarat_5Lacs_Plus.zip (by Victim District)
              - Non_Gujarat.zip (by Victim District)
              - Non_Gujarat_5Lacs_Plus.zip (by Victim District)
            
            ### Output Columns (15 Total):
            1. S No. (Auto)
            2. Acknowledgement No.
            3. Victim District
            4. Victim State
            5. Reported Amount (Victim)
            6. Account No.
            7. IFSC Code
            8. Address
            9. District (Suspect)
            10. State (Suspect) - Used for Gujarat filtering
            11. Pin Code
            12. Transaction Amount - ONE column
            13. Disputed Amount
            14. Bank/FIs
            15. Layers
            
            ### Total Output:
            - **6 Excel files** (individual datasets)
            - **4 ZIP files** (district-wise splits)
            - **10 downloadable files** in total!
            
            ### Features:
            - ✅ **Column mappings saved permanently** (in .kiro/workflow_mappings.json)
            - ✅ Mappings persist across sessions and restarts
            - ✅ Consistent 15-column output
            - ✅ Legal data ready format
            - ✅ No manual steps required
            """)
    
    st.markdown("---")
    st.markdown("🔄 Automated Workflow | Built with Streamlit")
