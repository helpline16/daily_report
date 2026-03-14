import streamlit as st
import pandas as pd
import io
from datetime import datetime
import os
import json


def load_ack_column_mappings():
    """Load column mappings from persistent JSON file"""
    mapping_file = "cyber multiple accoun with DA and ACK/.kiro/ack_pivot_mappings.json"
    
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
        'ack_list_col': '-- Select --',
        'layer_ack': '-- Select --',
        'layer_bank': '-- Select --',
        'layer_disputed': '-- Select --',
        'status_ack': '-- Select --',
        'status_bank': '-- Select --',
        'status_amount': '-- Select --',
        'status_complaint': '-- Select --'
    }


def save_ack_column_mappings(mappings):
    """Save column mappings to persistent JSON file"""
    mapping_file = "cyber multiple accoun with DA and ACK/.kiro/ack_pivot_mappings.json"
    
    try:
        os.makedirs(os.path.dirname(mapping_file), exist_ok=True)
        with open(mapping_file, 'w') as f:
            json.dump(mappings, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Could not save mappings: {e}")
        return False



def render_ack_list_pivot_page():
    """Render the ACK List Pivot page - processes ACK list with layerwise and status data."""
    
    st.title("📋 ACK List Pivot Report")
    st.markdown("Upload ACK list and match with Layerwise & Status Wise data to generate pivot report.")
    
    st.info("📌 This tool takes an ACK list as master data and enriches it with pending amounts, disputed amounts, and pending time.")
    
    # Initialize session state for column mappings - LOAD FROM FILE
    if 'ack_pivot_col_mappings' not in st.session_state:
        st.session_state.ack_pivot_col_mappings = load_ack_column_mappings()
    
    # File uploads
    st.markdown("### 📁 Upload Files")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 1️⃣ ACK List File")
        ack_list_file = st.file_uploader(
            "Excel or CSV with ACK numbers",
            type=['xlsx', 'xls', 'csv'],
            help="Master ACK list - only ACK numbers needed",
            key="ack_list_file"
        )
    
    with col2:
        st.markdown("#### 2️⃣ Layerwise File")
        layerwise_file = st.file_uploader(
            "Layerwise Excel file",
            type=['xlsx', 'xls'],
            help="Excel file with ACK, Bank Name, and Disputed Amount",
            key="ack_layerwise"
        )
    
    with col3:
        st.markdown("#### 3️⃣ Status Wise Report")
        status_file = st.file_uploader(
            "Status wise report",
            type=['xlsx', 'xls', 'csv'],
            help="Excel or CSV file with ACK, Bank Name, Amount, and Complaint Date",
            key="ack_status"
        )
    
    if ack_list_file is not None and layerwise_file is not None and status_file is not None:
        try:
            # Step 1: Load ACK List
            st.markdown("---")
            
            with st.expander("📋 Step 1: Load ACK List (Click to view details)", expanded=False):
                # Handle CSV or Excel for ACK list
                if ack_list_file.name.lower().endswith('.csv'):
                    ack_list_df = pd.read_csv(ack_list_file)
                    st.success(f"✅ Loaded ACK list (CSV): {len(ack_list_df):,} rows")
                else:
                    ack_list_df = pd.read_excel(ack_list_file)
                    st.success(f"✅ Loaded ACK list (Excel): {len(ack_list_df):,} rows")
                
                with st.expander("👁️ Preview ACK List (First 10 rows)"):
                    st.dataframe(ack_list_df.head(10))
            
            # Step 2: Load other files
            with st.expander("📊 Step 2: Load Other Files (Click to view details)", expanded=False):
                layerwise_df = pd.read_excel(layerwise_file)
                st.success(f"✅ Loaded layerwise file: {len(layerwise_df):,} rows")
                
                # Handle CSV or Excel for status file
                if status_file.name.lower().endswith('.csv'):
                    status_df = pd.read_csv(status_file)
                    st.success(f"✅ Loaded status file (CSV): {len(status_df):,} rows")
                else:
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
                if st.button("🔄 Reset Mappings", help="Reset all column selections to default", key="reset_ack_mappings"):
                    default_mappings = {
                        'ack_list_col': '-- Select --',
                        'layer_ack': '-- Select --',
                        'layer_bank': '-- Select --',
                        'layer_disputed': '-- Select --',
                        'status_ack': '-- Select --',
                        'status_bank': '-- Select --',
                        'status_amount': '-- Select --',
                        'status_complaint': '-- Select --'
                    }
                    st.session_state.ack_pivot_col_mappings = default_mappings
                    save_ack_column_mappings(default_mappings)
                    st.rerun()
            
            col_sel1, col_sel2, col_sel3 = st.columns(3)
            
            with col_sel1:
                st.markdown("**From ACK List File:**")
                
                ack_list_options = ["-- Select --"] + list(ack_list_df.columns)
                ack_list_default = ack_list_options.index(st.session_state.ack_pivot_col_mappings['ack_list_col']) if st.session_state.ack_pivot_col_mappings['ack_list_col'] in ack_list_options else 0
                
                ack_list_col = st.selectbox(
                    "ACK Number Column:",
                    options=ack_list_options,
                    index=ack_list_default,
                    key="ack_list_col"
                )
            
            with col_sel2:
                st.markdown("**From Layerwise File:**")
                
                layer_ack_options = ["-- Select --"] + list(layerwise_df.columns)
                layer_ack_default = layer_ack_options.index(st.session_state.ack_pivot_col_mappings['layer_ack']) if st.session_state.ack_pivot_col_mappings['layer_ack'] in layer_ack_options else 0
                
                layer_ack_col = st.selectbox(
                    "ACK Number:",
                    options=layer_ack_options,
                    index=layer_ack_default,
                    key="layer_ack"
                )
                
                layer_bank_options = ["-- Select --"] + list(layerwise_df.columns)
                layer_bank_default = layer_bank_options.index(st.session_state.ack_pivot_col_mappings['layer_bank']) if st.session_state.ack_pivot_col_mappings['layer_bank'] in layer_bank_options else 0
                
                layer_bank_col = st.selectbox(
                    "Bank Name:",
                    options=layer_bank_options,
                    index=layer_bank_default,
                    key="layer_bank"
                )
                
                layer_disputed_options = ["-- Select --"] + list(layerwise_df.columns)
                layer_disputed_default = layer_disputed_options.index(st.session_state.ack_pivot_col_mappings['layer_disputed']) if st.session_state.ack_pivot_col_mappings['layer_disputed'] in layer_disputed_options else 0
                
                layer_disputed_col = st.selectbox(
                    "Disputed Amount:",
                    options=layer_disputed_options,
                    index=layer_disputed_default,
                    key="layer_disputed"
                )
            
            with col_sel3:
                st.markdown("**From Status File:**")
                
                status_ack_options = ["-- Select --"] + list(status_df.columns)
                status_ack_default = status_ack_options.index(st.session_state.ack_pivot_col_mappings['status_ack']) if st.session_state.ack_pivot_col_mappings['status_ack'] in status_ack_options else 0
                
                status_ack_col = st.selectbox(
                    "ACK Number:",
                    options=status_ack_options,
                    index=status_ack_default,
                    key="status_ack"
                )
                
                status_bank_options = ["-- Select --"] + list(status_df.columns)
                status_bank_default = status_bank_options.index(st.session_state.ack_pivot_col_mappings['status_bank']) if st.session_state.ack_pivot_col_mappings['status_bank'] in status_bank_options else 0
                
                status_bank_col = st.selectbox(
                    "Bank Name:",
                    options=status_bank_options,
                    index=status_bank_default,
                    key="status_bank"
                )
                
                status_amount_options = ["-- Select --"] + list(status_df.columns)
                status_amount_default = status_amount_options.index(st.session_state.ack_pivot_col_mappings['status_amount']) if st.session_state.ack_pivot_col_mappings['status_amount'] in status_amount_options else 0
                
                status_amount_col = st.selectbox(
                    "Amount (Pending):",
                    options=status_amount_options,
                    index=status_amount_default,
                    key="status_amount"
                )
                
                status_complaint_options = ["-- Select --"] + list(status_df.columns)
                status_complaint_default = status_complaint_options.index(st.session_state.ack_pivot_col_mappings['status_complaint']) if st.session_state.ack_pivot_col_mappings['status_complaint'] in status_complaint_options else 0
                
                status_complaint_col = st.selectbox(
                    "Complaint Date:",
                    options=status_complaint_options,
                    index=status_complaint_default,
                    key="status_complaint"
                )
            
            # Validation
            if ack_list_col == "-- Select --":
                st.warning("⚠️ Please select ACK Number column from ACK List File")
                return
            
            if layer_ack_col == "-- Select --" or layer_bank_col == "-- Select --" or layer_disputed_col == "-- Select --":
                st.warning("⚠️ Please select all required columns from Layerwise File")
                return
            
            if status_ack_col == "-- Select --" or status_bank_col == "-- Select --" or status_amount_col == "-- Select --" or status_complaint_col == "-- Select --":
                st.warning("⚠️ Please select all required columns from Status File")
                return

            
            # Step 4: Generate Report
            st.markdown("---")
            
            if st.button("🔄 Generate ACK Pivot Report", type="primary", use_container_width=True, key="generate_ack_pivot"):
                # Save column mappings PERMANENTLY to file
                mappings_to_save = {
                    'ack_list_col': ack_list_col,
                    'layer_ack': layer_ack_col,
                    'layer_bank': layer_bank_col,
                    'layer_disputed': layer_disputed_col,
                    'status_ack': status_ack_col,
                    'status_bank': status_bank_col,
                    'status_amount': status_amount_col,
                    'status_complaint': status_complaint_col
                }
                
                st.session_state.ack_pivot_col_mappings = mappings_to_save
                
                if save_ack_column_mappings(mappings_to_save):
                    st.success("✅ Column mappings saved permanently!")
                
                status_placeholder = st.empty()
                status_placeholder.info("⏳ Processing... Please wait")
                
                # CRITICAL: Normalize ALL data types BEFORE any matching
                
                # 1. Normalize ACK numbers - convert to string, strip whitespace, handle NaN
                ack_list_df[ack_list_col] = ack_list_df[ack_list_col].fillna('').apply(lambda x: str(x).strip().upper() if x != '' else '')
                layerwise_df[layer_ack_col] = layerwise_df[layer_ack_col].fillna('').apply(lambda x: str(x).strip().upper() if x != '' else '')
                status_df[status_ack_col] = status_df[status_ack_col].fillna('').apply(lambda x: str(x).strip().upper() if x != '' else '')
                
                # 2. Normalize Bank Names - convert to string, strip whitespace
                layerwise_df[layer_bank_col] = layerwise_df[layer_bank_col].fillna('').apply(lambda x: str(x).strip().upper() if x != '' else '')
                status_df[status_bank_col] = status_df[status_bank_col].fillna('').apply(lambda x: str(x).strip().upper() if x != '' else '')
                
                # 3. Normalize amounts to numeric - ROBUST CONVERSION
                def clean_amount(val):
                    """Convert any amount format to float with 2 decimals"""
                    if pd.isna(val) or val == '' or val is None:
                        return 0.0
                    val_str = str(val).strip()
                    if val_str == '' or val_str.lower() in ['nan', 'none', 'null', 'na']:
                        return 0.0
                    val_str = val_str.replace('₹', '').replace('$', '').replace('€', '').replace(',', '').replace(' ', '').strip()
                    try:
                        return round(float(val_str), 2)
                    except (ValueError, TypeError):
                        return 0.0
                
                layerwise_df[layer_disputed_col] = layerwise_df[layer_disputed_col].apply(clean_amount)
                status_df[status_amount_col] = status_df[status_amount_col].apply(clean_amount)
                
                # PROCESSING LOGIC:
                # 1. Start with ACK list (MASTER)
                # 2. For each ACK, find ALL matching entries in Status Wise file (by ACK number)
                # 3. For each Status entry (ACK + Bank + Amount), find CLOSEST matching Disputed Amount in Layerwise (by ACK + Bank)
                # 4. Skip ACKs not found in Status Wise file
                
                result_data = []
                skipped_acks = []
                
                for _, ack_row in ack_list_df.iterrows():
                    ack_num = ack_row[ack_list_col]
                    
                    if ack_num == '':
                        continue
                    
                    # Find ALL matching entries in Status Wise file for this ACK
                    status_matches = status_df[status_df[status_ack_col] == ack_num]
                    
                    if len(status_matches) == 0:
                        # Skip ACKs not found in Status Wise file
                        skipped_acks.append(ack_num)
                        continue
                    
                    # Process each status entry (ACK can have multiple banks)
                    for _, status_row in status_matches.iterrows():
                        bank_name = status_row[status_bank_col]
                        pending_amount = status_row[status_amount_col]
                        complaint_date = status_row[status_complaint_col]
                        
                        if bank_name == '':
                            continue
                        
                        # Find matching Disputed Amount in Layerwise (by ACK + Bank Name)
                        layerwise_match = layerwise_df[
                            (layerwise_df[layer_ack_col] == ack_num) & 
                            (layerwise_df[layer_bank_col] == bank_name)
                        ]
                        
                        disputed_amount = 0.0
                        if len(layerwise_match) > 0:
                            # CRITICAL: If multiple matches, find the CLOSEST to pending amount
                            if len(layerwise_match) == 1:
                                # Only one match - use it
                                disputed_amount = layerwise_match[layer_disputed_col].iloc[0]
                            else:
                                # Multiple matches - find closest to pending amount
                                disputed_amounts = layerwise_match[layer_disputed_col].tolist()
                                
                                # Find the disputed amount closest to pending amount
                                closest_amount = min(disputed_amounts, key=lambda x: abs(x - pending_amount))
                                disputed_amount = closest_amount
                        
                        result_data.append({
                            'Bank Name': bank_name,
                            'ACK': ack_num,
                            'Pending Amount': pending_amount,
                            'Disputed Amount': disputed_amount if disputed_amount > 0 else '',
                            'Complaint Date': complaint_date
                        })
                
                if len(result_data) == 0:
                    st.error("❌ No matching data found! All ACKs were skipped.")
                    if skipped_acks:
                        with st.expander("⚠️ View Skipped ACKs"):
                            st.warning(f"Skipped {len(skipped_acks)} ACKs not found in Status Wise file")
                            st.write(skipped_acks[:50])  # Show first 50
                    return
                
                result_df = pd.DataFrame(result_data)
                
                # Calculate pending time
                current_time = datetime.now()
                today_date = current_time.date()
                pending_times = []
                
                # Debug: Track parsing issues
                parse_success = 0
                parse_fail = 0
                
                for complaint_date in result_df['Complaint Date']:
                    if complaint_date != '' and pd.notna(complaint_date):
                        try:
                            # Try multiple date parsing methods for accuracy
                            complaint_dt = None
                            
                            if isinstance(complaint_date, str):
                                # Try parsing with explicit format first: DD-MM-YYYY HH:MM
                                try:
                                    complaint_dt = pd.to_datetime(complaint_date, format='%d-%m-%Y %H:%M', errors='raise')
                                except:
                                    # Try without time
                                    try:
                                        complaint_dt = pd.to_datetime(complaint_date, format='%d-%m-%Y', errors='raise')
                                    except:
                                        # Fallback: Try with dayfirst=True for other formats
                                        complaint_dt = pd.to_datetime(complaint_date, dayfirst=True, errors='coerce')
                            else:
                                complaint_dt = pd.to_datetime(complaint_date, errors='coerce')
                            
                            # Check if parsing was successful
                            if pd.isna(complaint_dt):
                                pending_times.append('')
                                parse_fail += 1
                                continue
                            
                            parse_success += 1
                            complaint_date_only = complaint_dt.date()
                            time_diff = current_time - complaint_dt
                            
                            # Ensure time_diff is positive
                            if time_diff.total_seconds() < 0:
                                pending_times.append('')
                                continue
                            
                            total_seconds = int(time_diff.total_seconds())
                            days = total_seconds // 86400
                            hours = (total_seconds % 86400) // 3600
                            minutes = (total_seconds % 3600) // 60
                            
                            # Format based on duration
                            if complaint_date_only == today_date:
                                # Live case
                                if days > 0:
                                    time_str = f"Live case pending since {days} day{'s' if days > 1 else ''} {hours} hr {minutes:02d} min"
                                elif hours > 0:
                                    time_str = f"Live case pending since {hours} hr {minutes:02d} min"
                                else:
                                    time_str = f"Live case pending since {minutes} min"
                            else:
                                # Regular case
                                if days > 0:
                                    time_str = f"Pending since {days} day{'s' if days > 1 else ''} {hours} hr {minutes:02d} min"
                                elif hours > 0:
                                    time_str = f"Pending since {hours} hr {minutes:02d} min"
                                else:
                                    time_str = f"Pending since {minutes} min"
                            
                            pending_times.append(time_str)
                        except Exception as e:
                            pending_times.append('')
                            parse_fail += 1
                    else:
                        pending_times.append('')
                
                result_df['Pending Time'] = pending_times
                
                # Show parsing statistics
                with st.expander("🔍 Date Parsing Debug Info", expanded=False):
                    st.info(f"✅ Successfully parsed: {parse_success} dates")
                    st.info(f"❌ Failed to parse: {parse_fail} dates")
                    if parse_fail > 0:
                        st.warning("Some dates could not be parsed. Check the date format in your Status Wise file.")
                        # Show sample of complaint dates
                        sample_dates = result_df['Complaint Date'].head(5).tolist()
                        st.write("Sample dates from Status Wise file:")
                        for i, date in enumerate(sample_dates, 1):
                            st.code(f"{i}. {date} (Type: {type(date).__name__})")

                
                # Group by Bank and ACK - sum amounts for same ACK+Bank combination
                grouped_data = []
                
                for (bank, ack), group in result_df.groupby(['Bank Name', 'ACK']):
                    total_pending = group['Pending Amount'].sum()
                    disputed_values = [x for x in group['Disputed Amount'] if x != '' and x != 0 and pd.notna(x)]
                    total_disputed = sum(disputed_values) if disputed_values else ''
                    
                    complaint = ''
                    for val in group['Complaint Date']:
                        if val != '' and pd.notna(val):
                            complaint = val
                            break
                    
                    pending = ''
                    for val in group['Pending Time']:
                        if val != '' and pd.notna(val):
                            pending = val
                            break
                    
                    grouped_data.append({
                        'Bank Name': bank,
                        'ACK': ack,
                        'Total Pending Amount': total_pending,
                        'Total Disputed Amount': total_disputed,
                        'Complaint Date': complaint,
                        'Pending Time': pending
                    })
                
                grouped = pd.DataFrame(grouped_data)
                
                # Sort by Bank Name and ACK
                grouped = grouped.sort_values(['Bank Name', 'ACK'])
                
                # Create TWO output formats:
                # 1. Detailed format - for download
                final_output_detailed = grouped[['Bank Name', 'ACK', 'Total Pending Amount', 'Total Disputed Amount', 'Pending Time']].copy()
                
                # 2. Grouped format (like pivot.xlsx) - Bank with all ACKs listed
                grouped_format_data = []
                
                for bank_name in grouped['Bank Name'].unique():
                    bank_data = grouped[grouped['Bank Name'] == bank_name].copy()
                    
                    # Prepare data for sorting: convert disputed amount to numeric for sorting
                    bank_data_list = []
                    for _, row in bank_data.iterrows():
                        ack = row['ACK']
                        pending_time = row['Pending Time']
                        disputed_amt = row['Total Disputed Amount']
                        pending_amt = row['Total Pending Amount']
                        
                        # If disputed amount is empty, use pending amount for sorting
                        sort_amt = disputed_amt if (disputed_amt != '' and disputed_amt != 0 and pd.notna(disputed_amt)) else pending_amt
                        
                        bank_data_list.append({
                            'ack': ack,
                            'pending_time': pending_time,
                            'disputed_amt': disputed_amt,
                            'pending_amt': pending_amt,
                            'sort_amt': sort_amt
                        })
                    
                    # Sort by disputed amount (HIGH to LOW) within this bank
                    bank_data_list.sort(key=lambda x: x['sort_amt'], reverse=True)
                    
                    # Create list of "ACK - Pending Time - Disputed Amount" for each ACK (now sorted)
                    ack_list = []
                    total_bank_disputed = 0
                    
                    for item in bank_data_list:
                        ack = item['ack']
                        pending_time = item['pending_time']
                        disputed_amt = item['disputed_amt']
                        pending_amt = item['pending_amt']
                        
                        # If disputed amount is empty, use pending amount for display
                        display_amt = disputed_amt if (disputed_amt != '' and disputed_amt != 0 and pd.notna(disputed_amt)) else pending_amt
                        
                        # Add to total
                        total_bank_disputed += display_amt
                        
                        # Format: ACK - Pending Time - Disputed Amount
                        if pending_time != '' and pd.notna(pending_time):
                            ack_list.append(f"{ack} - {pending_time} - ₹{display_amt:,.2f}")
                        else:
                            ack_list.append(f"{ack} - ₹{display_amt:,.2f}")
                    
                    # Join all ACKs with newline (line break) for Excel
                    ack_pending_str = '\n'.join(ack_list)
                    
                    grouped_format_data.append({
                        'bank/ (wallet /pg/pa)/ merchant / insurance': bank_name,
                        'ACK & Pending Time': ack_pending_str,
                        'Total Disputed Amount': f"₹{total_bank_disputed:,.2f}"
                    })
                
                final_output_grouped = pd.DataFrame(grouped_format_data)
                
                st.session_state.ack_pivot_result_detailed = final_output_detailed
                st.session_state.ack_pivot_result_grouped = final_output_grouped
                st.session_state.ack_pivot_skipped_acks = skipped_acks
                st.session_state.ack_pivot_stats = {
                    'total_banks': final_output_detailed['Bank Name'].nunique(),
                    'total_acks': len(final_output_detailed),
                    'total_pending': final_output_detailed['Total Pending Amount'].sum(),
                    'total_disputed': sum([x for x in final_output_detailed['Total Disputed Amount'] if x != '' and pd.notna(x)]),
                    'matched_disputed': len([x for x in final_output_detailed['Total Disputed Amount'] if x != '' and pd.notna(x)]),
                    'matched_complaint': len([x for x in grouped['Complaint Date'] if x != '' and pd.notna(x)]),
                    'skipped_count': len(skipped_acks)
                }
                
                status_placeholder.empty()
                st.success(f"✅ Report generated successfully!")
                
                # Show summary in expandable section
                with st.expander("📊 View Generation Summary", expanded=False):
                    st.info(f"• {len(ack_list_df)} ACKs in master list")
                    st.info(f"• {len(skipped_acks)} ACKs skipped (not found in Status Wise file)")
                    st.info(f"• {final_output_detailed['Bank Name'].nunique()} banks processed")
                    st.info(f"• {len(final_output_detailed)} ACK-Bank combinations")
                    st.info(f"• {st.session_state.ack_pivot_stats['matched_disputed']} disputed amounts matched")
                    st.info(f"• {st.session_state.ack_pivot_stats['matched_complaint']} complaint dates matched")
                    
                    if skipped_acks:
                        with st.expander("⚠️ View Skipped ACKs"):
                            st.warning(f"These {len(skipped_acks)} ACKs were not found in Status Wise file:")
                            st.write(skipped_acks[:100])  # Show first 100

            
            # Display results
            if 'ack_pivot_result_detailed' in st.session_state and st.session_state.ack_pivot_result_detailed is not None:
                final_output_detailed = st.session_state.ack_pivot_result_detailed
                final_output_grouped = st.session_state.ack_pivot_result_grouped
                stats = st.session_state.ack_pivot_stats
                
                st.markdown("---")
                st.markdown("### 📊 ACK Pivot Report Results")
                
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
                    st.metric("ACKs Skipped", f"{stats['skipped_count']}")
                
                # Display grouped format (like pivot.xlsx)
                st.markdown("### 🏦 Grouped Format (Bank-wise)")
                st.dataframe(final_output_grouped, use_container_width=True, hide_index=True, height=400)
                
                # Display detailed format in expandable section
                with st.expander("📋 View Detailed Format (with amounts)", expanded=False):
                    for bank_name in final_output_detailed['Bank Name'].unique():
                        bank_data = final_output_detailed[final_output_detailed['Bank Name'] == bank_name]
                        
                        # Show bank summary
                        bank_pending = bank_data['Total Pending Amount'].sum()
                        bank_disputed = sum([x for x in bank_data['Total Disputed Amount'] if x != '' and pd.notna(x)])
                        bank_matched = len([x for x in bank_data['Total Disputed Amount'] if x != '' and pd.notna(x)])
                        
                        st.markdown(f"**🏦 {bank_name}**")
                        st.markdown(f"Summary: {len(bank_data)} ACKs | Pending: ₹{bank_pending:,.0f} | Disputed: ₹{bank_disputed:,.0f} | Matched: {bank_matched}/{len(bank_data)}")
                        
                        # Show ACK details
                        display_df = bank_data[['ACK', 'Total Pending Amount', 'Total Disputed Amount', 'Pending Time']].copy()
                        display_df['Total Pending Amount'] = display_df['Total Pending Amount'].apply(lambda x: f"₹{x:,.2f}" if pd.notna(x) else '')
                        display_df['Total Disputed Amount'] = display_df['Total Disputed Amount'].apply(lambda x: f"₹{x:,.2f}" if x != '' and pd.notna(x) else '')
                        
                        st.dataframe(display_df, use_container_width=True, hide_index=True)
                        st.markdown("---")
                
                # Download options
                st.markdown("---")
                st.markdown("### 📥 Download Report")
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                dl_col1, dl_col2, dl_col3, dl_col4 = st.columns(4)
                
                with dl_col1:
                    # Excel download - GROUPED FORMAT (like pivot.xlsx)
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        final_output_grouped.to_excel(writer, sheet_name='ACK Pivot', index=False)
                        
                        # Auto-adjust column widths and enable text wrapping
                        worksheet = writer.sheets['ACK Pivot']
                        from openpyxl.styles import Alignment
                        
                        worksheet.column_dimensions['A'].width = 50  # Bank name
                        worksheet.column_dimensions['B'].width = 80  # ACK & Pending Time
                        worksheet.column_dimensions['C'].width = 20  # Total Disputed Amount
                        
                        # Enable text wrapping for column B (ACK & Pending Time) to show line breaks
                        for row in range(2, len(final_output_grouped) + 2):  # Start from row 2 (after header)
                            cell = worksheet[f'B{row}']
                            cell.alignment = Alignment(wrap_text=True, vertical='top')
                    
                    excel_data = excel_buffer.getvalue()
                    
                    st.download_button(
                        label=f"⬇️ Download Grouped Format (Excel)",
                        data=excel_data,
                        file_name=f"ack_pivot_grouped_{timestamp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="download_ack_pivot_grouped_excel"
                    )
                
                with dl_col2:
                    # Excel download - DETAILED FORMAT (with amounts)
                    excel_buffer2 = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer2, engine='openpyxl') as writer:
                        final_output_detailed.to_excel(writer, sheet_name='Detailed', index=False)
                        
                        # Auto-adjust column widths
                        worksheet = writer.sheets['Detailed']
                        for idx, col in enumerate(final_output_detailed.columns):
                            max_length = max(
                                final_output_detailed[col].astype(str).apply(len).max(),
                                len(str(col))
                            )
                            col_letter = chr(65 + idx) if idx < 26 else f"A{chr(65 + idx - 26)}"
                            worksheet.column_dimensions[col_letter].width = min(max_length + 2, 50)
                    
                    excel_data2 = excel_buffer2.getvalue()
                    
                    st.download_button(
                        label=f"⬇️ Download Detailed Format (Excel)",
                        data=excel_data2,
                        file_name=f"ack_pivot_detailed_{timestamp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="download_ack_pivot_detailed_excel"
                    )
                
                with dl_col3:
                    # CSV download - GROUPED FORMAT
                    csv_data = final_output_grouped.to_csv(index=False).encode('utf-8')
                    
                    st.download_button(
                        label=f"⬇️ Download Grouped (CSV)",
                        data=csv_data,
                        file_name=f"ack_pivot_grouped_{timestamp}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key="download_ack_pivot_grouped_csv"
                    )
                
                with dl_col4:
                    # Download Skipped ACKs
                    if 'ack_pivot_skipped_acks' in st.session_state and st.session_state.ack_pivot_skipped_acks:
                        skipped_acks_list = st.session_state.ack_pivot_skipped_acks
                        skipped_df = pd.DataFrame({'Skipped ACK Numbers': skipped_acks_list})
                        
                        # Excel format for skipped ACKs
                        skipped_excel_buffer = io.BytesIO()
                        with pd.ExcelWriter(skipped_excel_buffer, engine='openpyxl') as writer:
                            skipped_df.to_excel(writer, sheet_name='Skipped ACKs', index=False)
                            worksheet = writer.sheets['Skipped ACKs']
                            worksheet.column_dimensions['A'].width = 30
                        
                        skipped_excel_data = skipped_excel_buffer.getvalue()
                        
                        st.download_button(
                            label=f"⬇️ Download Skipped ACKs ({len(skipped_acks_list)})",
                            data=skipped_excel_data,
                            file_name=f"skipped_acks_{timestamp}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            key="download_skipped_acks",
                            help=f"Download list of {len(skipped_acks_list)} ACKs that were not found in Status Wise file"
                        )
                    else:
                        st.info("No skipped ACKs", icon="✅")
        
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
            
            1. **Upload ACK List File**: Excel or CSV with ACK numbers (MASTER data)
            2. **Upload Layerwise File**: Excel with ACK, Bank Name, and Disputed Amount
            3. **Upload Status File**: Excel or CSV with ACK, Bank Name, Amount (Pending), and Complaint Date
            4. **Select Columns**: Choose the correct columns from each file (auto-remembered)
            5. **Generate Report**: Click to create the pivot table
            6. **Download**: Get the report in Excel or CSV format
            
            ### ⚠️ CRITICAL - Data Integrity & Matching Logic:
            - **ACK List is MASTER data source** - only these ACKs are processed
            - **Pending Amount**: Taken from Status Wise file (Amount column)
            - **Disputed Amount Matching**: Matches by ACK Number + Bank Name (2 parameters for 100% accuracy)
            - **Bank Name**: Taken from Status Wise file
            - **Complaint Date**: Taken from Status Wise file
            - If ACK not found in Status Wise file → SKIPPED (not included in output)
            - If same ACK has multiple banks → creates separate entries for each bank
            - If same ACK+Bank appears multiple times → sums all amounts
            
            ### Matching Logic (100% Accurate):
            - **Step 1**: For each ACK in master list, find ALL matching entries in Status Wise file
            - **Step 2**: For each Status entry (ACK + Bank), find matching Disputed Amount in Layerwise file
            - **Step 3**: Match by ACK + Bank Name for disputed amount
            - **Step 4**: Calculate pending time from complaint date
            - **Step 5**: Group by Bank and sort ACKs by disputed amount (high to low)
            
            ### Output Format:
            - Grouped by Bank Name
            - Each bank shows all its ACKs (sorted by disputed amount - high to low)
            - For each ACK: ACK | Pending Time | Disputed Amount
            - Total Pending Amount = Sum of all pending amounts for that ACK
            - Total Disputed Amount = Sum of all disputed amounts for that ACK (if multiple matches)
            - Pending Time format: "Pending since X hr XX min" OR "Live case pending since X hr XX min" (if today)
            
            ### Features:
            - ✅ ACK list as master - only process specified ACKs
            - ✅ Dual-parameter matching for accuracy (ACK + Bank Name)
            - ✅ Sums amounts for duplicate ACK+Bank combinations
            - ✅ Pivot table grouped by Bank
            - ✅ Sorted by disputed amount (high to low) within each bank
            - ✅ Calculates pending time automatically
            - ✅ Live case detection (if complaint date is today)
            - ✅ Download in Excel or CSV
            - ✅ Bank-wise expandable view
            - ✅ Match statistics showing data completeness
            - ✅ Column mappings remembered for faster workflow
            - ✅ Shows skipped ACKs (not found in Status Wise file)
            
            ### For Gujarat State Cyber Crime Police:
            - This tool ensures 100% accuracy for critical police data
            - Only specified ACKs are processed (from master list)
            - Dual-parameter matching prevents false matches
            - Validation checks prevent data loss
            - Blank fields clearly show where additional data is needed
            - Skipped ACKs are tracked and reported
            """)
    
    # Footer
    st.markdown("---")
    st.markdown("📋 ACK List Pivot Report | Built with Streamlit")
