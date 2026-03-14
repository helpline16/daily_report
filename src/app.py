"""
Fraud Analysis Web Application.

A Streamlit-based web application for law enforcement cybercrime departments
to analyze and consolidate fraud transaction data from Excel files.
"""

import sys
import os

# Ensure the project root is on sys.path so `import src.xyz` works when
# Streamlit runs `src/app.py` as a script. This makes imports stable whether
# you run `python -m streamlit run src/app.py` from the repo root or from
# another working directory.
_THIS_FILE = os.path.abspath(__file__)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_THIS_FILE))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from typing import Optional, List, Dict, Any

from src.upload_service import UploadService
from src.column_detector import ColumnDetector
from src.data_processor import DataProcessor
from src.validation_engine import ValidationEngine
from src.aggregation_engine import AggregationEngine
from src.report_generator import ReportGenerator
from src.dashboard import Dashboard
from src.session_manager import SessionManager
from src.models import ColumnMapping, AggregatedAccount, ProcessingStats, ValidationResult
from src.district_data import render_district_download_page
from src.merge_files import render_merge_files_page
from src.excel_merger import render_excel_merger_page
from src.call_notice_data_merge import render_call_notice_merge_page
from src.transaction_matcher import render_transaction_matcher_page
from src.disputed_amount_matcher import render_disputed_amount_matcher_page
from src.money_transfer_dispute import render_money_transfer_dispute_page
from src.ack_bank_consolidator import render_ack_bank_consolidator_page
from src.database_service import DatabaseService
from src.districtwise import render_districtwise_page
from src.non_gujarat_filter import render_non_gujarat_filter_page
from src.column_selector import render_column_selector_page
from src.amount_matcher import render_amount_matcher_page
from src.bank_ack_pivot import render_bank_ack_pivot_page
from src.ack_list_pivot import render_ack_list_pivot_page
from src.filter_by_entry_count import render_filter_by_entry_count_page
from src.filter_by_unique_ack import render_filter_by_unique_ack_page
from src.bulk_mysql_import import render_bulk_mysql_import_page
from src.mysql_database_viewer import render_mysql_database_viewer_page
from src.ai_sql_assistant import render_ai_sql_assistant_page
from src.automated_workflow import render_automated_workflow_page
from src.ui_styling import apply_custom_css, render_page_header_with_info
from src.smart_district_split import render_smart_district_split_page
from src.ifsc_pincode_district_split import render_ifsc_pincode_district_split_page
from src.distinct_account_pivot import render_distinct_account_pivot_page
from src.auth import check_password, show_logout_button

# Page configuration
st.set_page_config(
    page_title="Fraud Analysis Tool - Gujarat Cyber Police",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom styling
apply_custom_css()

# Initialize services (cached to avoid recreation)
@st.cache_resource
def get_services():
    """Initialize and cache service instances."""
    return {
        'upload_service': UploadService(),
        'column_detector': ColumnDetector(),
        'data_processor': DataProcessor(),
        'validation_engine': ValidationEngine(),
        'aggregation_engine': AggregationEngine(),
        'report_generator': ReportGenerator(),
        'dashboard': Dashboard(),
        'session_manager': SessionManager()
    }


def init_session_state():
    """Initialize session state variables."""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'upload'
    if 'uploaded_df' not in st.session_state:
        st.session_state.uploaded_df = None
    if 'filename' not in st.session_state:
        st.session_state.filename = None
    if 'column_mapping' not in st.session_state:
        st.session_state.column_mapping = None
    if 'cleaned_df' not in st.session_state:
        st.session_state.cleaned_df = None
    if 'validation_result' not in st.session_state:
        st.session_state.validation_result = None
    if 'aggregated_accounts' not in st.session_state:
        st.session_state.aggregated_accounts = None
    if 'processing_stats' not in st.session_state:
        st.session_state.processing_stats = None
    if 'processing_logs' not in st.session_state:
        st.session_state.processing_logs = []


def render_sidebar():
    """Render the navigation sidebar."""
    with st.sidebar:
        st.title("🔍 Fraud Analysis")
        st.caption("Gujarat Cyber Police")
        st.markdown("---")
        
        # Page navigation
        pages = {
            'upload': '📤 Upload File',
            'mapping': '🔗 Column Mapping',
            'processing': '⚙️ Processing',
            'results': '📊 Results Dashboard',
            'district_download': '📍 District Data Download',
            'districtwise': '📊 Split Data by Column',
            'smart_district_split': '🗺️ Smart District Split',
            'ifsc_pincode_split': '🏦 IFSC/PIN District Split',
            'filter_by_entry_count': '🔢 Filter by Entry Count',
            'filter_by_unique_ack': '🏦 Filter by Unique ACK',
            'non_gujarat_filter': '🗺️ Non-Gujarat Filter',
            'amount_matcher': '💰 Amount Matcher',
            'bank_ack_pivot': '🏦 Bank ACK Pivot',
            'ack_list_pivot': '📋 ACK List Pivot',
            'automated_workflow': '🔄 Automated Workflow',
            'column_selector': '📋 Column Selector',
            'excel_merger': '📎 Merge Excel Files',
            'call_notice_merge': '📞 Call Notice Data Merge',
            'transaction_matcher': '🔄 Transaction Matcher',
            'disputed_amount_matcher': '💰 Disputed Amount Matcher',
            'money_transfer_dispute': '💸 Money Transfer Dispute Matcher',
            'ack_bank_consolidator': '📊 ACK + Bank Consolidator',
            'bulk_mysql_import': '📊 Bulk MySQL Import',
            'mysql_database_viewer': '🗄️ MySQL Database Viewer',
            'ai_sql_assistant': '🤖 AI SQL Assistant',
            'distinct_account_pivot': '📊 Distinct Account Pivot',
            'view_database': '🗄️ View Database'
        }
        
        for page_key, page_name in pages.items():
            # Determine if page should be enabled
            enabled = True
            if page_key == 'mapping' and st.session_state.uploaded_df is None:
                enabled = False
            elif page_key == 'processing' and st.session_state.column_mapping is None:
                enabled = False
            elif page_key == 'results' and st.session_state.aggregated_accounts is None:
                enabled = False
            # district_download, excel_merger, call_notice_merge, view_database are always enabled
            
            if enabled:
                if st.button(page_name, key=f"nav_{page_key}", use_container_width=True):
                    st.session_state.current_page = page_key
                    st.rerun()
            else:
                st.button(page_name, key=f"nav_{page_key}", use_container_width=True, disabled=True)
        
        st.markdown("---")
        
        # Session info
        st.caption("📊 Session Info")
        if st.session_state.filename:
            st.caption(f"📁 {st.session_state.filename}")
        
        st.markdown("---")
        
        # Data handling reminder
        st.caption("🔒 Security")
        st.caption("All data processed in-memory only.")
        st.caption("No data stored on servers.")
        
        # Reset button
        st.markdown("---")
        if st.button("🔄 Start Over", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


def render_upload_page():
    """Render the file upload page with multiple file selection support."""
    services = get_services()
    upload_service = services['upload_service']
    
    # Render page header with info button
    render_page_header_with_info('upload')
    
    # Check if data already processed - show option to proceed or upload new
    if st.session_state.uploaded_df is not None:
        st.success(f"✅ Data already loaded: {len(st.session_state.uploaded_df)} rows from {st.session_state.filename}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Proceed to Column Mapping", type="primary", use_container_width=True):
                st.session_state.current_page = 'mapping'
                st.rerun()
        with col2:
            if st.button("🔄 Upload New Files", use_container_width=True):
                st.session_state.uploaded_df = None
                st.session_state.filename = None
                st.session_state.column_mapping = None
                st.session_state.cleaned_df = None
                st.session_state.validation_result = None
                st.session_state.aggregated_accounts = None
                st.session_state.processing_stats = None
                st.rerun()
        
        # Show preview of current data
        st.markdown("---")
        st.subheader("📋 Current Data Preview")
        preview_df = upload_service.get_preview(st.session_state.uploaded_df, rows=10)
        st.dataframe(preview_df, use_container_width=True)
        return
    
    st.markdown("Upload **1 to 50 Excel/CSV files** using **Ctrl+Click** to select multiple files, then click **Process Files**.")
    
    # Multiple file uploader with Ctrl+Click support
    uploaded_files = st.file_uploader(
        "Choose Excel/CSV files (Ctrl+Click for multiple)",
        type=['xlsx', 'xls', 'csv'],
        accept_multiple_files=True,
        help="Supported formats: Excel (.xlsx, .xls) and CSV (.csv). Use Ctrl+Click to select multiple files."
    )
    
    # Show uploaded files list
    if uploaded_files:
        st.subheader(f"📁 {len(uploaded_files)} file(s) selected:")
        for f in uploaded_files:
            size_kb = f.size / 1024
            if size_kb > 1024:
                size_str = f"{size_kb/1024:.2f} MB"
            else:
                size_str = f"{size_kb:.2f} KB"
            st.write(f"• {f.name} — {size_str}")
        
        # Process Files button
        if st.button("🚀 Process Files", type="primary", use_container_width=True):
            if len(uploaded_files) > 50:
                st.warning("⚠️ Maximum 50 files allowed. Please remove some files.")
            else:
                all_data = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"Reading file {i+1}/{len(uploaded_files)}: {uploaded_file.name}...")
                    progress_bar.progress((i + 1) / len(uploaded_files))
                    
                    try:
                        # Validate file
                        file_bytes = BytesIO(uploaded_file.getvalue())
                        validation_result = upload_service.validate_file(file_bytes, uploaded_file.name)
                        
                        if not validation_result.is_valid:
                            st.warning(f"⚠️ Skipping {uploaded_file.name}: {validation_result.error_message}")
                            continue
                        
                        # Read file
                        file_bytes.seek(0)
                        df = upload_service.read_file(file_bytes, uploaded_file.name)
                        
                        st.success(f"✅ {uploaded_file.name}: {len(df)} rows loaded")
                        all_data.append((uploaded_file.name, df))
                        
                    except Exception as e:
                        st.error(f"❌ Error reading {uploaded_file.name}: {str(e)}")
                
                progress_bar.progress(100)
                status_text.text("✅ All files processed!")
                
                if all_data:
                    # Combine all dataframes
                    combined_df = pd.concat([df for _, df in all_data], ignore_index=True)
                    
                    # Store in session state immediately
                    st.session_state.uploaded_df = combined_df
                    st.session_state.filename = f"{len(all_data)}_files_combined"
                    
                    # Rerun to show the proceed option
                    st.rerun()
                else:
                    st.error("❌ No valid data found in uploaded files.")
    else:
        st.info("📤 Select files using Ctrl+Click for multiple selection, then click **Process Files**.")


def render_mapping_page():
    """Render the column mapping page."""
    services = get_services()
    column_detector = services['column_detector']
    
    if st.session_state.uploaded_df is None:
        st.warning("Please upload a file first.")
        return
    
    # Render page header with info button
    render_page_header_with_info('mapping')
    
    df = st.session_state.uploaded_df
    headers = list(df.columns)
    
    # Auto-detect columns
    auto_mapping = column_detector.detect_columns(headers)
    
    # Show confidence scores
    if auto_mapping.confidence_scores:
        st.subheader("🎯 Auto-Detection Confidence")
        conf_cols = st.columns(4)
        for i, (col_type, score) in enumerate(auto_mapping.confidence_scores.items()):
            with conf_cols[i % 4]:
                color = "green" if score >= 0.9 else "orange" if score >= 0.8 else "red"
                st.markdown(f"**{col_type.replace('_', ' ').title()}**: :{color}[{score:.0%}]")
    
    # Show ambiguous mappings warning
    if auto_mapping.ambiguous_mappings:
        st.warning("⚠️ Some columns have ambiguous mappings. Please verify the selections below.")
    
    st.markdown("---")
    st.subheader("📝 Column Assignments")
    
    # Create mapping form
    col1, col2 = st.columns(2)
    
    # Add "None" option to headers
    header_options = ["-- Not Mapped --"] + headers
    
    def get_default_index(mapped_value):
        if mapped_value and mapped_value in headers:
            return headers.index(mapped_value) + 1
        return 0
    
    with col1:
        bank_account_col = st.selectbox(
            "Bank Account Number",
            options=header_options,
            index=get_default_index(auto_mapping.bank_account_number),
            help="Column containing fraudster bank account numbers"
        )
        
        amount_col = st.selectbox(
            "Amount",
            options=header_options,
            index=get_default_index(auto_mapping.amount),
            help="Column containing transaction amounts"
        )
        
        ack_col = st.selectbox(
            "Acknowledgement Number",
            options=header_options,
            index=get_default_index(auto_mapping.acknowledgement_number),
            help="Column containing acknowledgement/reference numbers"
        )
        
        ifsc_col = st.selectbox(
            "IFSC Code",
            options=header_options,
            index=get_default_index(auto_mapping.ifsc_code),
            help="Column containing bank IFSC codes"
        )
    
    with col2:
        bank_name_col = st.selectbox(
            "Bank Name",
            options=header_options,
            index=get_default_index(auto_mapping.bank_name),
            help="Column containing bank names"
        )
        
        address_col = st.selectbox(
            "Address",
            options=header_options,
            index=get_default_index(auto_mapping.address),
            help="Column containing beneficiary addresses"
        )
        
        disputed_col = st.selectbox(
            "Disputed Amount",
            options=header_options,
            index=get_default_index(auto_mapping.disputed_amount),
            help="Column containing disputed/chargeback amounts"
        )
        
        serial_col = st.selectbox(
            "Serial Number",
            options=header_options,
            index=get_default_index(auto_mapping.serial_number),
            help="Column containing serial/row numbers"
        )
        
        district_col = st.selectbox(
            "District",
            options=header_options,
            index=get_default_index(auto_mapping.district),
            help="Column containing district names"
        )
        
        state_col = st.selectbox(
            "State",
            options=header_options,
            index=get_default_index(auto_mapping.state),
            help="Column containing state names"
        )


    # Validation
    st.markdown("---")
    
    st.success("✅ Map the columns that are available in your file")
    
    # Proceed button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Proceed to Processing", type="primary", use_container_width=True):
            # Create final mapping
            final_mapping = ColumnMapping(
                serial_number=serial_col if serial_col != "-- Not Mapped --" else None,
                acknowledgement_number=ack_col if ack_col != "-- Not Mapped --" else None,
                bank_account_number=bank_account_col if bank_account_col != "-- Not Mapped --" else None,
                ifsc_code=ifsc_col if ifsc_col != "-- Not Mapped --" else None,
                address=address_col if address_col != "-- Not Mapped --" else None,
                amount=amount_col if amount_col != "-- Not Mapped --" else None,
                disputed_amount=disputed_col if disputed_col != "-- Not Mapped --" else None,
                bank_name=bank_name_col if bank_name_col != "-- Not Mapped --" else None,
                district=district_col if district_col != "-- Not Mapped --" else None,
                state=state_col if state_col != "-- Not Mapped --" else None
            )
            
            st.session_state.column_mapping = final_mapping
            st.session_state.current_page = 'processing'
            st.rerun()


def render_processing_page():
    """Render the data processing page with progress tracking."""
    services = get_services()
    data_processor = services['data_processor']
    validation_engine = services['validation_engine']
    aggregation_engine = services['aggregation_engine']
    dashboard = services['dashboard']
    
    if st.session_state.uploaded_df is None or st.session_state.column_mapping is None:
        st.warning("Please complete the previous steps first.")
        return
    
    # Render page header with info button
    render_page_header_with_info('processing')
    
    df = st.session_state.uploaded_df
    mapping = st.session_state.column_mapping
    
    # Check if already processed
    if st.session_state.aggregated_accounts is not None:
        st.success("✅ Data has already been processed!")
        st.info("Click 'View Results' to see the dashboard, or 'Reprocess' to process again.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("View Results", type="primary", use_container_width=True):
                st.session_state.current_page = 'results'
                st.rerun()
        with col2:
            if st.button("Reprocess Data", use_container_width=True):
                st.session_state.aggregated_accounts = None
                st.session_state.processing_stats = None
                st.session_state.cleaned_df = None
                st.session_state.validation_result = None
                st.session_state.processing_logs = []
                st.rerun()
        return
    
    # Processing controls
    if st.button("🚀 Start Processing", type="primary", use_container_width=True):
        logs = []
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        log_container = st.container()
        
        # Metrics placeholders
        metrics_cols = st.columns(4)
        rows_metric = metrics_cols[0].empty()
        accounts_metric = metrics_cols[1].empty()
        errors_metric = metrics_cols[2].empty()
        amount_metric = metrics_cols[3].empty()
        
        total_rows = len(df)
        
        try:
            # Step 1: Data Cleaning (20%)
            status_text.text("Step 1/4: Cleaning data...")
            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Starting data cleaning...")
            
            cleaned_df = data_processor.clean_dataframe(df, mapping)
            rows_after_cleaning = len(cleaned_df)
            
            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Removed {total_rows - rows_after_cleaning} empty rows")
            progress_bar.progress(20)
            rows_metric.metric("Rows Processed", rows_after_cleaning)
            
            # Step 2: Validation (40%)
            status_text.text("Step 2/4: Validating data...")
            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Starting data validation...")
            
            validation_result = validation_engine.validate_dataframe(cleaned_df, mapping)
            
            if not validation_result.is_valid:
                for error in validation_result.critical_errors:
                    logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] CRITICAL: {error}")
                st.error("❌ Critical validation errors found. Cannot proceed.")
                for error in validation_result.critical_errors:
                    st.error(error)
                return
            
            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Found {len(validation_result.warnings)} warnings")
            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Flagged {len(validation_result.flagged_rows)} rows")
            progress_bar.progress(40)
            errors_metric.metric("Errors Found", len(validation_result.flagged_rows))


            # Step 3: Aggregation (70%)
            status_text.text("Step 3/4: Aggregating by account...")
            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Starting aggregation by account number...")
            
            aggregated = aggregation_engine.aggregate_by_account(cleaned_df, mapping)
            sorted_accounts = aggregation_engine.sort_results(aggregated)
            
            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Found {len(sorted_accounts)} unique accounts")
            progress_bar.progress(70)
            accounts_metric.metric("Unique Accounts", len(sorted_accounts))
            
            # Step 4: Calculate Statistics (100%)
            status_text.text("Step 4/4: Calculating statistics...")
            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Calculating summary statistics...")
            
            stats = dashboard.calculate_statistics(
                accounts=sorted_accounts,
                total_input_rows=total_rows,
                input_filename=st.session_state.filename or "",
                rows_with_errors=len(validation_result.flagged_rows)
            )
            
            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Total fraud amount: ₹{stats.total_fraud_amount:,.2f}")
            progress_bar.progress(100)
            amount_metric.metric("Total Amount", f"₹{stats.total_fraud_amount:,.0f}")
            
            # Store results
            st.session_state.cleaned_df = cleaned_df
            st.session_state.validation_result = validation_result
            st.session_state.aggregated_accounts = sorted_accounts
            st.session_state.processing_stats = stats
            st.session_state.processing_logs = logs
            
            status_text.text("✅ Processing complete!")
            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Processing completed successfully!")
            
            st.success("🎉 Processing completed successfully!")
            
            # Show logs
            with log_container:
                st.subheader("📜 Processing Log")
                log_text = "\n".join(logs)
                st.text_area("Logs", value=log_text, height=200, disabled=True)
            
            # Proceed button
            if st.button("View Results Dashboard", type="primary"):
                st.session_state.current_page = 'results'
                st.rerun()
                
        except Exception as e:
            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {str(e)}")
            st.error(f"❌ Processing failed: {str(e)}")
            
            with log_container:
                st.subheader("📜 Processing Log")
                log_text = "\n".join(logs)
                st.text_area("Logs", value=log_text, height=200, disabled=True)


def render_results_page():
    """Render the results dashboard with statistics, downloads, and filters."""
    services = get_services()
    dashboard = services['dashboard']
    report_generator = services['report_generator']
    
    if st.session_state.aggregated_accounts is None:
        st.warning("Please process data first.")
        return
    
    # Render page header with info button
    render_page_header_with_info('results')
    
    accounts = st.session_state.aggregated_accounts
    stats = st.session_state.processing_stats
    validation_result = st.session_state.validation_result
    
    # Summary Statistics
    st.subheader("📈 Summary Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Input Rows", stats.total_input_rows)
    with col2:
        st.metric("Unique Accounts", stats.unique_accounts)
    with col3:
        st.metric("Total Fraud Amount", f"₹{stats.total_fraud_amount:,.2f}")
    with col4:
        st.metric("Avg Amount/Account", f"₹{stats.average_amount_per_account:,.2f}")
    
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("Rows Processed", stats.rows_processed)
    with col6:
        st.metric("Rows with Errors", stats.rows_with_errors)
    with col7:
        st.metric("Total Disputed", f"₹{stats.total_disputed_amount:,.2f}")
    with col8:
        if stats.unique_accounts > 0:
            avg_txn = stats.total_input_rows / stats.unique_accounts
            st.metric("Avg Txn/Account", f"{avg_txn:.1f}")
        else:
            st.metric("Avg Txn/Account", "0")
    
    st.markdown("---")
    
    # Download Section - Lazy generation (no eager computation)
    st.subheader("📥 Download Reports")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    quality_metrics = validation_result.quality_report if validation_result else None
    errors = validation_result.warnings if validation_result else []
    
    # Row 1: Download buttons
    dl_col1, dl_col2, dl_col3, dl_col4 = st.columns(4)
    
    with dl_col1:
        if st.button("📊 Prepare Excel", use_container_width=True, key="prep_excel"):
            with st.spinner("Generating Excel..."):
                st.session_state.excel_ready = report_generator.generate_excel_bytes(accounts)
        
        if 'excel_ready' in st.session_state and st.session_state.excel_ready:
            st.download_button(
                label="⬇️ Download Excel",
                data=st.session_state.excel_ready,
                file_name=f"fraud_analysis_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    with dl_col2:
        if st.button("📄 Prepare CSV", use_container_width=True, key="prep_csv"):
            with st.spinner("Generating CSV..."):
                st.session_state.csv_ready = report_generator.generate_csv_bytes(accounts)
        
        if 'csv_ready' in st.session_state and st.session_state.csv_ready:
            st.download_button(
                label="⬇️ Download CSV",
                data=st.session_state.csv_ready,
                file_name=f"fraud_analysis_{timestamp}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with dl_col3:
        if st.button("📑 Prepare PDF", use_container_width=True, key="prep_pdf"):
            with st.spinner("Generating PDF..."):
                st.session_state.pdf_ready = report_generator.generate_pdf_bytes(accounts, stats, quality_metrics)
        
        if 'pdf_ready' in st.session_state and st.session_state.pdf_ready:
            st.download_button(
                label="⬇️ Download PDF",
                data=st.session_state.pdf_ready,
                file_name=f"fraud_analysis_{timestamp}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    
    with dl_col4:
        if st.button("📋 Prepare Audit Log", use_container_width=True, key="prep_audit"):
            with st.spinner("Generating Audit Log..."):
                audit_log = report_generator.generate_audit_log(
                    input_filename=st.session_state.filename or "",
                    rows_processed=stats.rows_processed,
                    errors_encountered=errors,
                    timestamp=stats.processing_timestamp
                )
                st.session_state.audit_ready = audit_log.encode('utf-8')
        
        if 'audit_ready' in st.session_state and st.session_state.audit_ready:
            st.download_button(
                label="⬇️ Download Audit Log",
                data=st.session_state.audit_ready,
                file_name=f"audit_log_{timestamp}.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    # Row 2: SAVE TO DATABASE - Prominent button
    st.markdown("")
    st.markdown("##### 🗄️ Save to MySQL Database")
    
    db_save_col1, db_save_col2, db_save_col3 = st.columns([2, 1, 1])
    
    with db_save_col1:
        save_dataset_name = st.text_input("Dataset Name", placeholder="e.g., January 2025 Fraud Data", key="save_ds_name_input")
    
    with db_save_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        save_to_db_btn = st.button("💾 SAVE TO DATABASE", use_container_width=True, key="save_to_db_main", type="primary")
    
    with db_save_col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚙️ DB Settings", use_container_width=True, key="db_settings_btn"):
            st.session_state.show_db_settings = True
    
    # Database settings expander
    if st.session_state.get('show_db_settings', False):
        with st.expander("Database Connection Settings", expanded=True):
            db_set_col1, db_set_col2 = st.columns(2)
            with db_set_col1:
                st.session_state.db_host = st.text_input("Host", value=st.session_state.get('db_host', 'localhost'), key="db_host_set")
                st.session_state.db_user = st.text_input("Username", value=st.session_state.get('db_user', 'root'), key="db_user_set")
            with db_set_col2:
                st.session_state.db_port = st.number_input("Port", value=st.session_state.get('db_port', 3306), key="db_port_set")
                st.session_state.db_password = st.text_input("Password", value=st.session_state.get('db_password', 'Cyber2026'), type="password", key="db_pass_set")
            
            if st.button("🔌 Test Connection", key="test_conn_btn"):
                db_service = DatabaseService(
                    host=st.session_state.get('db_host', 'localhost'),
                    port=st.session_state.get('db_port', 3306),
                    user=st.session_state.get('db_user', 'root'),
                    password=st.session_state.get('db_password', 'Cyber2026')
                )
                success, msg = db_service.test_connection()
                if success:
                    st.success(f"✅ {msg}")
                else:
                    st.error(f"❌ {msg}")
    
    # Handle Save to Database
    if save_to_db_btn:
        if not save_dataset_name:
            st.error("⚠️ Please enter a dataset name!")
        else:
            with st.spinner("💾 Saving to MySQL database..."):
                db_service = DatabaseService(
                    host=st.session_state.get('db_host', 'localhost'),
                    port=st.session_state.get('db_port', 3306),
                    user=st.session_state.get('db_user', 'root'),
                    password=st.session_state.get('db_password', 'Cyber2026')
                )
                
                # Progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(current, total):
                    progress = int((current / total) * 100)
                    progress_bar.progress(progress)
                    status_text.text(f"Saving... {current:,} / {total:,} records ({progress}%)")
                
                dataset_id, error_msg = db_service.save_dataset(
                    name=save_dataset_name,
                    description=f"Saved from Fraud Analysis Tool - {len(accounts)} accounts",
                    accounts=accounts,
                    source_filename=st.session_state.get('filename', ''),
                    progress_callback=update_progress
                )
                db_service.disconnect()
                
                progress_bar.empty()
                status_text.empty()
                
                if dataset_id:
                    st.success(f"""
                    ✅ **Data Saved Successfully!**
                    - Dataset ID: {dataset_id}
                    - Records: {len(accounts):,}
                    - Database: gujarat_cyber_police
                    - You can view this in MySQL Workbench
                    """)
                else:
                    st.error(f"❌ Save failed: {error_msg}")


    st.markdown("---")
    
    # Search and Filter Section
    st.subheader("🔍 Search & Filter")
    
    filter_cols = st.columns(3)
    
    with filter_cols[0]:
        search_query = st.text_input(
            "Search Account Number",
            placeholder="Enter account number to search...",
            help="Search for specific account numbers"
        )
    
    with filter_cols[1]:
        min_transactions = st.number_input(
            "Minimum Transactions",
            min_value=0,
            value=0,
            help="Filter accounts with at least this many transactions"
        )
    
    with filter_cols[2]:
        min_amount = st.number_input(
            "Minimum Amount (₹)",
            min_value=0.0,
            value=0.0,
            help="Filter accounts with at least this total amount"
        )
    
    # Apply filters
    filtered_accounts = accounts
    
    if search_query:
        filtered_accounts = dashboard.search_accounts(filtered_accounts, search_query)
    
    if min_transactions > 0:
        filtered_accounts = dashboard.filter_by_min_transactions(filtered_accounts, min_transactions)
    
    if min_amount > 0:
        filtered_accounts = dashboard.filter_by_min_amount(filtered_accounts, min_amount)
    
    # Show filter results count
    st.info(f"Showing {len(filtered_accounts)} of {len(accounts)} accounts")
    
    st.markdown("---")
    
    # Top 10 Accounts
    st.subheader("🏆 Top 10 Accounts by Amount")
    
    top_10 = filtered_accounts[:10] if len(filtered_accounts) >= 10 else filtered_accounts
    
    if top_10:
        top_10_data = []
        for i, acc in enumerate(top_10, 1):
            top_10_data.append({
                "Rank": i,
                "Account Number": acc.account_number,
                "Bank Name": acc.bank_name,
                "IFSC Code": acc.ifsc_code,
                "Transactions": acc.total_transactions,
                "Total Amount": f"₹{acc.total_amount:,.2f}",
                "Risk Score": f"{acc.risk_score:.1f}"
            })
        
        st.dataframe(
            pd.DataFrame(top_10_data),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No accounts match the current filters.")


    st.markdown("---")
    
    # Full Results Table
    st.subheader("📋 All Results")
    
    # Pagination
    items_per_page = st.selectbox("Items per page", [10, 25, 50, 100], index=1)
    total_pages = max(1, (len(filtered_accounts) + items_per_page - 1) // items_per_page)
    
    page_col1, page_col2, page_col3 = st.columns([1, 2, 1])
    with page_col2:
        current_page = st.number_input(
            "Page",
            min_value=1,
            max_value=total_pages,
            value=1,
            help=f"Total pages: {total_pages}"
        )
    
    # Get page data
    start_idx = (current_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(filtered_accounts))
    page_accounts = filtered_accounts[start_idx:end_idx]
    
    if page_accounts:
        results_data = []
        for acc in page_accounts:
            results_data.append({
                "Account Number": acc.account_number,
                "Bank Name": acc.bank_name,
                "IFSC Code": acc.ifsc_code,
                "Address": acc.address[:50] + "..." if len(acc.address) > 50 else acc.address,
                "District": acc.district,
                "State": acc.state,
                "Transactions": acc.total_transactions,
                "Ack Numbers": acc.acknowledgement_numbers[:30] + "..." if len(acc.acknowledgement_numbers) > 30 else acc.acknowledgement_numbers,
                "Total Amount": f"₹{acc.total_amount:,.2f}",
                "Disputed Amount": f"₹{acc.total_disputed_amount:,.2f}",
                "Risk Score": f"{acc.risk_score:.1f}"
            })
        
        st.dataframe(
            pd.DataFrame(results_data),
            use_container_width=True,
            hide_index=True
        )
        
        st.caption(f"Showing {start_idx + 1}-{end_idx} of {len(filtered_accounts)} accounts")
    else:
        st.info("No accounts to display.")
    
    st.markdown("---")
    
    # Flagged/Error Rows Section
    if validation_result and validation_result.flagged_rows:
        with st.expander("⚠️ View Flagged Rows", expanded=False):
            st.warning(f"Found {len(validation_result.flagged_rows)} rows with issues")
            
            # Show warnings
            if validation_result.warnings:
                st.subheader("Warnings")
                for warning in validation_result.warnings[:50]:  # Limit to first 50
                    st.text(f"• {warning}")
                
                if len(validation_result.warnings) > 50:
                    st.text(f"... and {len(validation_result.warnings) - 50} more warnings")
    
    # Data Quality Report
    if validation_result and validation_result.quality_report:
        with st.expander("📊 Data Quality Report", expanded=False):
            qr = validation_result.quality_report
            
            quality_cols = st.columns(4)
            with quality_cols[0]:
                st.metric("Total Rows", qr.get('total_rows', 0))
            with quality_cols[1]:
                st.metric("Valid Accounts", qr.get('valid_account_numbers', 0))
            with quality_cols[2]:
                st.metric("Valid IFSC Codes", qr.get('valid_ifsc_codes', 0))
            with quality_cols[3]:
                st.metric("Valid Amounts", qr.get('valid_amounts', 0))
            
            quality_cols2 = st.columns(4)
            with quality_cols2[0]:
                st.metric("Account Validity Rate", f"{qr.get('account_number_validity_rate', 0):.1f}%")
            with quality_cols2[1]:
                st.metric("IFSC Validity Rate", f"{qr.get('ifsc_validity_rate', 0):.1f}%")
            with quality_cols2[2]:
                st.metric("Amount Validity Rate", f"{qr.get('amount_validity_rate', 0):.1f}%")
            with quality_cols2[3]:
                st.metric("Data Completeness", f"{qr.get('data_completeness_rate', 0):.1f}%")


def render_view_database_page():
    """Render the View Database page - Gujarat Cyber Police Data Management."""
    # Render page header with info button
    render_page_header_with_info('view_database')
    
    # Database connection settings
    with st.expander("⚙️ Database Connection Settings", expanded=False):
        st.caption("Configure MySQL connection")
        
        db_col1, db_col2 = st.columns(2)
        with db_col1:
            db_host = st.text_input("Host", value="localhost", key="vdb_host")
            db_user = st.text_input("Username", value="root", key="vdb_user")
            db_name = st.text_input("Database Name", value="gujarat_cyber_police", key="vdb_dbname")
        with db_col2:
            db_port = st.number_input("Port", value=3306, key="vdb_port")
            db_password = st.text_input("Password", value="Cyber2026", type="password", key="vdb_password")
        
        st.caption("💡 Change 'Database Name' to create/use a different database")
        
        if st.button("🔌 Test Connection", key="vdb_test_conn"):
            db_service = DatabaseService(host=db_host, port=db_port, user=db_user, password=db_password, database=db_name)
            success, message = db_service.test_connection()
            if success:
                st.success(f"✅ {message}")
            else:
                st.error(f"❌ {message}")
    
    # Get database settings
    db_host = st.session_state.get('vdb_host', 'localhost')
    db_port = st.session_state.get('vdb_port', 3306)
    db_user = st.session_state.get('vdb_user', 'root')
    db_password = st.session_state.get('vdb_password', 'Cyber2026')
    db_name = st.session_state.get('vdb_dbname', 'gujarat_cyber_police')
    
    st.markdown("---")
    
    # Six action buttons
    action_cols = st.columns(6)
    
    with action_cols[0]:
        if st.button("📋 Datasets", use_container_width=True, type="primary", key="vdb_view_btn"):
            st.session_state.vdb_action = 'view'
    
    with action_cols[1]:
        if st.button("📊 View Full Data", use_container_width=True, type="primary", key="vdb_fulldata_btn"):
            st.session_state.vdb_action = 'fulldata'
    
    with action_cols[2]:
        if st.button("✅ Verify", use_container_width=True, type="primary", key="vdb_verify_btn"):
            st.session_state.vdb_action = 'verify'
    
    with action_cols[3]:
        if st.button("📂 Browse", use_container_width=True, type="primary", key="vdb_load_btn"):
            st.session_state.vdb_action = 'load'
    
    with action_cols[4]:
        if st.button("🔍 Search", use_container_width=True, type="primary", key="vdb_search_btn"):
            st.session_state.vdb_action = 'search'
    
    with action_cols[5]:
        if st.button("🗑️ Delete", use_container_width=True, type="primary", key="vdb_delete_btn"):
            st.session_state.vdb_action = 'delete'
    
    st.markdown("---")
    
    # Handle actions
    current_action = st.session_state.get('vdb_action', None)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # VIEW FULL DATA WITH EXCEL-LIKE FEATURES
    if current_action == 'fulldata':
        st.subheader("📊 View Full Data - Excel-Like Features")
        
        db_service = DatabaseService(host=db_host, port=db_port, user=db_user, password=db_password, database=db_name)
        datasets = db_service.get_all_datasets()
        
        if not datasets:
            st.warning("No saved datasets found")
            if st.button("❌ Close", key="vdb_close_fulldata_empty"):
                st.session_state.vdb_action = None
                st.rerun()
            db_service.disconnect()
            return
        
        # Dataset selection
        dataset_options = {f"{d['name']} ({d['total_accounts']:,} records)": d['id'] for d in datasets}
        selected_dataset = st.selectbox("📁 Select Dataset", options=["-- Select Dataset --"] + list(dataset_options.keys()), key="vdb_fulldata_select")
        
        if selected_dataset != "-- Select Dataset --":
            dataset_id = dataset_options[selected_dataset]
            total_count = db_service.get_dataset_count(dataset_id)
            
            st.info(f"📊 Total Records: **{total_count:,}**")
            
            # Warning for large datasets
            if total_count > 100000:
                st.warning(f"⚠️ Large dataset ({total_count:,} records). Loading may take time. Consider using filters.")
            
            # ========== EXCEL-LIKE CONTROLS ==========
            st.markdown("### 🎛️ Excel-Like Controls")
            
            # Row 1: Sort options
            sort_col1, sort_col2 = st.columns(2)
            with sort_col1:
                sort_by = st.selectbox("📊 Sort By", [
                    "Total Amount (High to Low)",
                    "Total Amount (Low to High)",
                    "Account Number (A-Z)",
                    "Account Number (Z-A)",
                    "Bank Name (A-Z)",
                    "Bank Name (Z-A)",
                    "District (A-Z)",
                    "Total Transactions (High to Low)",
                    "ACK Count (High to Low)",
                    "Risk Score (High to Low)"
                ], key="vdb_sort_by")
            
            with sort_col2:
                max_rows = st.selectbox("📋 Max Rows to Load", [1000, 5000, 10000, 50000, 100000, "All"], index=0, key="vdb_max_rows")
            
            # Row 2: Filters
            st.markdown("### 🔍 Filters")
            filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
            
            with filter_col1:
                filter_account = st.text_input("🔢 Account Number Contains", key="vdb_filter_account")
            with filter_col2:
                filter_bank = st.text_input("🏦 Bank Name Contains", key="vdb_filter_bank")
            with filter_col3:
                filter_district = st.text_input("📍 District", key="vdb_filter_district")
            with filter_col4:
                filter_state = st.text_input("🗺️ State", key="vdb_filter_state")
            
            # Row 3: Amount filters
            amount_col1, amount_col2, amount_col3, amount_col4 = st.columns(4)
            with amount_col1:
                min_amount = st.number_input("💰 Min Amount (₹)", min_value=0.0, value=0.0, key="vdb_min_amount")
            with amount_col2:
                max_amount = st.number_input("💰 Max Amount (₹)", min_value=0.0, value=0.0, key="vdb_max_amount")
            with amount_col3:
                min_txn = st.number_input("📈 Min Transactions", min_value=0, value=0, key="vdb_min_txn")
            with amount_col4:
                min_ack = st.number_input("🔖 Min ACK Count", min_value=0, value=0, key="vdb_min_ack")
            
            # Load Data Button
            if st.button("📥 Load Data with Filters", type="primary", use_container_width=True, key="vdb_load_fulldata"):
                with st.spinner("Loading data from database..."):
                    # Build SQL query based on filters
                    limit_val = None if max_rows == "All" else int(max_rows)
                    
                    # Determine sort column and order
                    sort_mapping = {
                        "Total Amount (High to Low)": ("total_amount", "DESC"),
                        "Total Amount (Low to High)": ("total_amount", "ASC"),
                        "Account Number (A-Z)": ("account_number", "ASC"),
                        "Account Number (Z-A)": ("account_number", "DESC"),
                        "Bank Name (A-Z)": ("bank_name", "ASC"),
                        "Bank Name (Z-A)": ("bank_name", "DESC"),
                        "District (A-Z)": ("district", "ASC"),
                        "Total Transactions (High to Low)": ("total_transactions", "DESC"),
                        "ACK Count (High to Low)": ("ack_count", "DESC"),
                        "Risk Score (High to Low)": ("risk_score", "DESC")
                    }
                    sort_column, sort_order = sort_mapping.get(sort_by, ("total_amount", "DESC"))
                    
                    # Load data with custom query
                    df = db_service.load_dataset_filtered(
                        dataset_id=dataset_id,
                        sort_column=sort_column,
                        sort_order=sort_order,
                        limit=limit_val,
                        filter_account=filter_account if filter_account else None,
                        filter_bank=filter_bank if filter_bank else None,
                        filter_district=filter_district if filter_district else None,
                        filter_state=filter_state if filter_state else None,
                        min_amount=min_amount if min_amount > 0 else None,
                        max_amount=max_amount if max_amount > 0 else None,
                        min_transactions=min_txn if min_txn > 0 else None,
                        min_ack_count=min_ack if min_ack > 0 else None
                    )
                    
                    if df is not None and len(df) > 0:
                        st.session_state.vdb_fulldata_df = df
                        st.success(f"✅ Loaded {len(df):,} records")
                    else:
                        st.warning("No records found matching filters")
                        st.session_state.vdb_fulldata_df = None
            
            # Display loaded data
            if 'vdb_fulldata_df' in st.session_state and isinstance(st.session_state.vdb_fulldata_df, pd.DataFrame):
                df = st.session_state.vdb_fulldata_df
                
                st.markdown("---")
                st.markdown(f"### 📋 Data Table ({len(df):,} records)")
                
                # Quick stats
                stat_cols = st.columns(5)
                with stat_cols[0]:
                    st.metric("Records", f"{len(df):,}")
                with stat_cols[1]:
                    st.metric("Total Amount", f"₹{df['Total Amount'].sum():,.0f}")
                with stat_cols[2]:
                    st.metric("Avg Amount", f"₹{df['Total Amount'].mean():,.0f}")
                with stat_cols[3]:
                    st.metric("Total Transactions", f"{df['Total Transactions'].sum():,}")
                with stat_cols[4]:
                    st.metric("Unique Districts", f"{df['District'].nunique()}")
                
                # Data table with Streamlit's built-in features
                st.dataframe(
                    df,
                    use_container_width=True,
                    height=500,
                    column_config={
                        "Total Amount": st.column_config.NumberColumn(format="₹%.2f"),
                        "Total Disputed Amount": st.column_config.NumberColumn(format="₹%.2f"),
                        "Risk Score": st.column_config.NumberColumn(format="%.1f")
                    }
                )
                
                # Download options
                st.markdown("### 📥 Download Options")
                dl_cols = st.columns(3)
                
                with dl_cols[0]:
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label=f"⬇️ Download CSV ({len(df):,} rows)",
                        data=csv_data,
                        file_name=f"data_export_{timestamp}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with dl_cols[1]:
                    # Excel download
                    buffer = BytesIO()
                    df.to_excel(buffer, index=False, engine='openpyxl')
                    buffer.seek(0)
                    st.download_button(
                        label=f"⬇️ Download Excel ({len(df):,} rows)",
                        data=buffer.getvalue(),
                        file_name=f"data_export_{timestamp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                with dl_cols[2]:
                    # Summary by district
                    if st.button("📊 Generate District Summary", use_container_width=True, key="vdb_gen_district_summary_btn"):
                        summary = df.groupby('District').agg({
                            'Fraudster Bank Account Number': 'count',
                            'Total Amount': 'sum',
                            'Total Transactions': 'sum',
                            'ACK Count': 'sum'
                        }).reset_index()
                        summary.columns = ['District', 'Account Count', 'Total Amount', 'Total Transactions', 'Total ACKs']
                        summary = summary.sort_values('Total Amount', ascending=False)
                        st.session_state.vdb_district_summary_df = summary
                
                # Show district summary if generated
                if 'vdb_district_summary_df' in st.session_state and isinstance(st.session_state.vdb_district_summary_df, pd.DataFrame):
                    st.markdown("#### 📊 District-wise Summary")
                    st.dataframe(st.session_state.vdb_district_summary_df, use_container_width=True)
                    
                    summary_csv = st.session_state.vdb_district_summary_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="⬇️ Download District Summary",
                        data=summary_csv,
                        file_name=f"district_summary_{timestamp}.csv",
                        mime="text/csv"
                    )
        
        if st.button("❌ Close", key="vdb_close_fulldata"):
            st.session_state.vdb_action = None
            st.session_state.vdb_fulldata_df = None
            st.session_state.vdb_district_summary_df = None
            st.rerun()
        
        db_service.disconnect()
        return
    
    # VIEW DATASETS
    if current_action == 'view':
        st.subheader("📋 All Saved Datasets")
        st.info("**ℹ️ Viewing all datasets with verification status**")
        
        db_service = DatabaseService(host=db_host, port=db_port, user=db_user, password=db_password, database=db_name)
        datasets = db_service.get_all_datasets()
        db_service.disconnect()
        
        if datasets:
            view_data = []
            for d in datasets:
                verified_status = "✅ Verified" if d.get('verified') else "⚠️ Not Verified"
                view_data.append({
                    'ID': d['id'],
                    'Name': d['name'],
                    'Description': d.get('description', ''),
                    'Total Accounts': f"{d['total_accounts']:,}",
                    'Total Amount': f"₹{d['total_amount']:,.0f}",
                    'Status': verified_status,
                    'Created At': d['created_at'],
                    'Source File': d.get('source_filename', '')
                })
            
            view_df = pd.DataFrame(view_data)
            st.dataframe(view_df, use_container_width=True)
            st.success(f"✅ Found {len(datasets)} saved dataset(s)")
        else:
            st.warning("No saved datasets found in database")
        
        if st.button("❌ Close", key="vdb_close_view"):
            st.session_state.vdb_action = None
            st.rerun()
    
    # VERIFY DATA INTEGRITY
    elif current_action == 'verify':
        st.subheader("✅ Verify Data Integrity")
        st.info("**ℹ️ Verify that saved data is complete and accurate**")
        
        db_service = DatabaseService(host=db_host, port=db_port, user=db_user, password=db_password, database=db_name)
        datasets = db_service.get_all_datasets()
        
        if datasets:
            dataset_options = {f"{d['name']} ({d['total_accounts']:,} accounts)": d['id'] for d in datasets}
            selected_dataset = st.selectbox("Select Dataset to Verify", options=["-- Select --"] + list(dataset_options.keys()), key="vdb_verify_select")
            
            if selected_dataset != "-- Select --":
                dataset_id = dataset_options[selected_dataset]
                
                if st.button("🔍 Run Integrity Check", type="primary", key="vdb_run_verify"):
                    with st.spinner("Verifying data integrity..."):
                        is_valid, message = db_service.verify_dataset_integrity(dataset_id)
                        
                        if is_valid:
                            st.success(message)
                        else:
                            st.error(f"❌ INTEGRITY CHECK FAILED: {message}")
                            st.warning("⚠️ This dataset may have data corruption. Please re-save from original source.")
        else:
            st.warning("No saved datasets found")
        
        if st.button("❌ Close", key="vdb_close_verify"):
            st.session_state.vdb_action = None
            st.rerun()
        
        db_service.disconnect()
    
    # LOAD DATASET WITH PAGINATION (for large data)
    elif current_action == 'load':
        st.subheader("📂 Load & Browse Dataset")
        st.info("**ℹ️ For large datasets, data is loaded in pages to prevent memory issues**")
        
        db_service = DatabaseService(host=db_host, port=db_port, user=db_user, password=db_password, database=db_name)
        datasets = db_service.get_all_datasets()
        
        if datasets:
            dataset_options = {f"{d['name']} ({d['total_accounts']:,} accounts) - {d['created_at']}": d['id'] for d in datasets}
            selected_dataset = st.selectbox("Select Dataset", options=["-- Select --"] + list(dataset_options.keys()), key="vdb_load_select")
            
            if selected_dataset != "-- Select --":
                dataset_id = dataset_options[selected_dataset]
                total_count = db_service.get_dataset_count(dataset_id)
                
                st.info(f"📊 Total records: **{total_count:,}**")
                
                # Pagination settings
                page_size = st.selectbox("Rows per page", [100, 500, 1000, 5000], index=1, key="vdb_page_size")
                total_pages = max(1, (total_count + page_size - 1) // page_size)
                
                page_col1, page_col2, page_col3 = st.columns([1, 2, 1])
                with page_col2:
                    current_page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, key="vdb_current_page")
                    st.caption(f"Total pages: {total_pages:,}")
                
                # Load current page
                offset = (current_page - 1) * page_size
                
                if st.button("📥 Load Page", type="primary", key="vdb_load_page"):
                    with st.spinner(f"Loading rows {offset+1:,} to {min(offset+page_size, total_count):,}..."):
                        page_df = db_service.load_dataset(dataset_id, limit=page_size, offset=offset)
                        if page_df is not None:
                            st.session_state.vdb_page_data = page_df
                            st.success(f"✅ Loaded {len(page_df):,} records")
                
                # Show page data
                if 'vdb_page_data' in st.session_state and st.session_state.vdb_page_data is not None:
                    st.dataframe(st.session_state.vdb_page_data, use_container_width=True)
                
                st.markdown("---")
                st.subheader("📥 Export Full Dataset")
                st.warning(f"⚠️ Full export will download all **{total_count:,}** records. For very large data (>1 lakh rows), use CSV format.")
                
                export_cols = st.columns(2)
                with export_cols[0]:
                    if st.button("📄 Export Full CSV", use_container_width=True, key="vdb_export_csv"):
                        with st.spinner("Exporting all data to CSV (this may take time for large datasets)..."):
                            # Load all data in chunks and combine
                            all_chunks = []
                            for chunk in db_service.load_dataset_chunked(dataset_id, chunk_size=50000):
                                all_chunks.append(chunk)
                            
                            if all_chunks:
                                full_df = pd.concat(all_chunks, ignore_index=True)
                                csv_data = full_df.to_csv(index=False).encode('utf-8')
                                st.session_state.vdb_full_csv = csv_data
                                st.success(f"✅ Prepared {len(full_df):,} records for download")
                
                if 'vdb_full_csv' in st.session_state and st.session_state.vdb_full_csv:
                    st.download_button(
                        label="⬇️ Download Full CSV",
                        data=st.session_state.vdb_full_csv,
                        file_name=f"full_export_{timestamp}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            
            if st.button("❌ Close", key="vdb_close_load"):
                st.session_state.vdb_action = None
                st.session_state.vdb_page_data = None
                st.session_state.vdb_full_csv = None
                st.rerun()
        else:
            st.warning("No saved datasets found")
            if st.button("❌ Close", key="vdb_close_load_empty"):
                st.session_state.vdb_action = None
                st.rerun()
        
        db_service.disconnect()
    
    # SEARCH DATA (fast indexed search)
    elif current_action == 'search':
        st.subheader("🔍 Search Accounts")
        st.info("**ℹ️ Fast indexed search - works efficiently even with crores of records**")
        
        db_service = DatabaseService(host=db_host, port=db_port, user=db_user, password=db_password, database=db_name)
        datasets = db_service.get_all_datasets()
        
        if datasets:
            dataset_options = {f"{d['name']} ({d['total_accounts']:,} accounts)": d['id'] for d in datasets}
            selected_dataset = st.selectbox("Select Dataset to Search", options=["-- Select --"] + list(dataset_options.keys()), key="vdb_search_dataset")
            
            if selected_dataset != "-- Select --":
                dataset_id = dataset_options[selected_dataset]
                
                search_col1, search_col2, search_col3 = st.columns(3)
                with search_col1:
                    search_account = st.text_input("Account Number (partial)", key="vdb_search_account")
                with search_col2:
                    search_district = st.text_input("District (exact)", key="vdb_search_district")
                with search_col3:
                    search_min_amount = st.number_input("Min Amount (₹)", min_value=0.0, value=0.0, key="vdb_search_amount")
                
                max_results = st.slider("Max Results", 100, 10000, 1000, key="vdb_max_results")
                
                if st.button("🔍 Search", type="primary", key="vdb_do_search"):
                    with st.spinner("Searching..."):
                        results = db_service.search_accounts(
                            dataset_id=dataset_id,
                            account_number=search_account if search_account else None,
                            district=search_district if search_district else None,
                            min_amount=search_min_amount if search_min_amount > 0 else None,
                            limit=max_results
                        )
                        
                        if results is not None and len(results) > 0:
                            st.session_state.vdb_search_results = results
                            st.success(f"✅ Found {len(results):,} matching records")
                        else:
                            st.warning("No matching records found")
                            st.session_state.vdb_search_results = None
                
                # Show search results
                if 'vdb_search_results' in st.session_state and st.session_state.vdb_search_results is not None:
                    st.dataframe(st.session_state.vdb_search_results, use_container_width=True)
                    
                    csv_data = st.session_state.vdb_search_results.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="⬇️ Download Search Results",
                        data=csv_data,
                        file_name=f"search_results_{timestamp}.csv",
                        mime="text/csv"
                    )
        else:
            st.warning("No saved datasets found")
        
        if st.button("❌ Close", key="vdb_close_search"):
            st.session_state.vdb_action = None
            st.session_state.vdb_search_results = None
            st.rerun()
        
        db_service.disconnect()
    
    # DELETE DATASET
    elif current_action == 'delete':
        st.subheader("🗑️ Delete Dataset")
        st.error("""
        **⚠️ WARNING - This action will:**
        - Permanently delete the selected dataset
        - Remove all associated account records
        - This action CANNOT be undone!
        """)
        
        db_service = DatabaseService(host=db_host, port=db_port, user=db_user, password=db_password, database=db_name)
        datasets = db_service.get_all_datasets()
        
        if datasets:
            dataset_options = {f"{d['name']} (ID: {d['id']}, {d['total_accounts']:,} accounts, ₹{d['total_amount']:,.0f})": d['id'] for d in datasets}
            selected_delete = st.selectbox("Select Dataset to DELETE", options=["-- Select --"] + list(dataset_options.keys()), key="vdb_delete_select")
            
            delete_col1, delete_col2 = st.columns(2)
            with delete_col1:
                if st.button("🗑️ Confirm DELETE", type="primary", use_container_width=True, key="vdb_confirm_delete"):
                    if selected_delete != "-- Select --":
                        dataset_id = dataset_options[selected_delete]
                        with st.spinner("Deleting dataset..."):
                            if db_service.delete_dataset(dataset_id):
                                st.success("✅ Dataset deleted successfully!")
                                st.session_state.vdb_action = None
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete dataset")
            
            with delete_col2:
                if st.button("❌ Cancel", use_container_width=True, key="vdb_cancel_delete"):
                    st.session_state.vdb_action = None
                    st.rerun()
        else:
            st.warning("No saved datasets found in database")
            if st.button("❌ Close", key="vdb_close_delete"):
                st.session_state.vdb_action = None
                st.rerun()
        
        db_service.disconnect()


def main():
    """Main application entry point."""
    
    # Check authentication (only for deployed app)
    # When running locally, this will be bypassed
    if not check_password():
        st.stop()
    
    # Show logout button in sidebar
    show_logout_button()
    
    # Initialize session state
    init_session_state()
    
    # Render sidebar navigation
    render_sidebar()
    
    # Render current page
    page = st.session_state.current_page
    
    if page == 'upload':
        render_upload_page()
    elif page == 'mapping':
        render_mapping_page()
    elif page == 'processing':
        render_processing_page()
    elif page == 'results':
        render_results_page()
    elif page == 'district_download':
        render_district_download_page()
    elif page == 'districtwise':
        render_districtwise_page()
    elif page == 'smart_district_split':
        render_smart_district_split_page()
    elif page == 'ifsc_pincode_split':
        render_ifsc_pincode_district_split_page()
    elif page == 'filter_by_entry_count':
        render_filter_by_entry_count_page()
    elif page == 'filter_by_unique_ack':
        render_filter_by_unique_ack_page()
    elif page == 'non_gujarat_filter':
        render_non_gujarat_filter_page()
    elif page == 'amount_matcher':
        render_amount_matcher_page()
    elif page == 'bank_ack_pivot':
        render_bank_ack_pivot_page()
    elif page == 'ack_list_pivot':
        render_ack_list_pivot_page()
    elif page == 'automated_workflow':
        render_automated_workflow_page()
    elif page == 'column_selector':
        render_column_selector_page()
    elif page == 'excel_merger':
        render_merge_files_page()
    elif page == 'call_notice_merge':
        render_call_notice_merge_page()
    elif page == 'transaction_matcher':
        render_transaction_matcher_page()
    elif page == 'disputed_amount_matcher':
        render_disputed_amount_matcher_page()
    elif page == 'money_transfer_dispute':
        render_money_transfer_dispute_page()
    elif page == 'ack_bank_consolidator':
        render_ack_bank_consolidator_page()
    elif page == 'bulk_mysql_import':
        render_bulk_mysql_import_page()
    elif page == 'mysql_database_viewer':
        render_mysql_database_viewer_page()
    elif page == 'ai_sql_assistant':
        render_ai_sql_assistant_page()
    elif page == 'distinct_account_pivot':
        render_distinct_account_pivot_page()
    elif page == 'view_database':
        render_view_database_page()
    else:
        render_upload_page()


if __name__ == "__main__":
    main()
