"""
Excel Merger Module.

Simple tool to merge multiple Excel/CSV files into one combined file.
"""
import streamlit as st
import pandas as pd
from io import BytesIO
from typing import List, Tuple
from datetime import datetime


def generate_merged_excel(df: pd.DataFrame) -> bytes:
    """Generate Excel file bytes from DataFrame."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Merged Data')
    return output.getvalue()


def generate_merged_csv(df: pd.DataFrame) -> bytes:
    """Generate CSV file bytes from DataFrame."""
    return df.to_csv(index=False).encode('utf-8')


def read_file(uploaded_file) -> pd.DataFrame:
    """Read uploaded Excel/CSV file with better error handling."""
    try:
        filename = uploaded_file.name.lower()
        
        # Reset file pointer to beginning
        uploaded_file.seek(0)
        
        if filename.endswith('.csv'):
            # Try different encodings for CSV
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding='latin-1')
        else:
            # Read Excel file
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        
        # Clean column names - strip whitespace
        df.columns = df.columns.str.strip()
        
        return df
    except Exception as e:
        raise Exception(f"Error reading file '{uploaded_file.name}': {str(e)}")


def check_column_compatibility(files_list: List[Tuple[str, pd.DataFrame]]) -> Tuple[bool, str]:
    """
    Check if all files have compatible columns.
    Returns (is_compatible, message)
    """
    if len(files_list) < 2:
        return True, "Need at least 2 files to check compatibility"
    
    # Get columns from first file
    first_file_name, first_df = files_list[0]
    first_columns = set(first_df.columns)
    
    # Check each subsequent file
    for filename, df in files_list[1:]:
        current_columns = set(df.columns)
        
        # Check if columns match
        if first_columns != current_columns:
            missing_in_current = first_columns - current_columns
            extra_in_current = current_columns - first_columns
            
            error_msg = f"❌ Column mismatch detected!\n\n"
            error_msg += f"**Reference file:** {first_file_name} ({len(first_columns)} columns)\n"
            error_msg += f"**Problem file:** {filename} ({len(current_columns)} columns)\n\n"
            
            if missing_in_current:
                error_msg += f"**Missing columns in '{filename}':**\n"
                for col in sorted(missing_in_current):
                    error_msg += f"  • {col}\n"
            
            if extra_in_current:
                error_msg += f"\n**Extra columns in '{filename}':**\n"
                for col in sorted(extra_in_current):
                    error_msg += f"  • {col}\n"
            
            return False, error_msg
    
    return True, f"✅ All {len(files_list)} files have matching columns ({len(first_columns)} columns)"


def render_excel_merger_page():
    """Render the Excel merger page."""
    st.title("📎 Merge Excel Files")
    st.markdown("""
    Upload multiple Excel/CSV files and merge them into one file.
    - Files can have **different column structures** (columns will be combined)
    - Files uploaded together will be stacked vertically
    - Missing columns will be filled with empty values
    - Download the merged file as Excel or CSV
    """)
    
    st.markdown("---")
    
    # Merge mode selection
    st.subheader("🔧 Merge Mode")
    merge_mode = st.radio(
        "How should files be merged?",
        options=[
            "Smart Merge (Union of all columns)",
            "Strict Merge (Only common columns)",
            "Keep All Columns (Fill missing with blanks)"
        ],
        index=0,
        help="""
        - **Smart Merge**: Combines all columns from all files. Missing columns filled with empty values.
        - **Strict Merge**: Only keeps columns that exist in ALL files.
        - **Keep All Columns**: Same as Smart Merge (recommended for different file structures).
        """
    )
    
    st.markdown("---")
    
    # Initialize session state
    if 'merger_files' not in st.session_state:
        st.session_state.merger_files = []  # List of (filename, dataframe) tuples
    if 'merger_counter' not in st.session_state:
        st.session_state.merger_counter = 0
    
    # Two columns layout
    col_upload, col_list = st.columns([1, 1])
    
    with col_upload:
        st.subheader("➕ Add Files")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Upload Excel/CSV file",
            type=['xlsx', 'xls', 'csv'],
            key=f"merger_uploader_{st.session_state.merger_counter}",
            help="Add files one by one. Each file will be added to the list."
        )
        
        # Add file button
        if uploaded_file is not None:
            # Check if already exists
            existing_names = [name for name, _ in st.session_state.merger_files]
            
            if uploaded_file.name in existing_names:
                st.warning(f"⚠️ '{uploaded_file.name}' already added!")
            else:
                if st.button("➕ Add This File", type="primary", use_container_width=True):
                    try:
                        with st.spinner(f"Reading {uploaded_file.name}..."):
                            df = read_file(uploaded_file)
                            
                            # Validate the file has data
                            if len(df) == 0:
                                st.error(f"❌ File '{uploaded_file.name}' is empty!")
                            elif len(df.columns) == 0:
                                st.error(f"❌ File '{uploaded_file.name}' has no columns!")
                            else:
                                st.session_state.merger_files.append((uploaded_file.name, df))
                                st.session_state.merger_counter += 1
                                st.success(f"✅ Added: {uploaded_file.name} ({len(df)} rows, {len(df.columns)} columns)")
                                st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error reading file: {str(e)}")
    
    with col_list:
        st.subheader(f"📁 Files List ({len(st.session_state.merger_files)})")
        
        if st.session_state.merger_files:
            # Show file list
            for i, (filename, df) in enumerate(st.session_state.merger_files):
                file_col, rows_col, cols_col, remove_col = st.columns([2.5, 1, 1, 0.5])
                with file_col:
                    display_name = filename[:30] + "..." if len(filename) > 30 else filename
                    st.text(f"{i+1}. {display_name}")
                with rows_col:
                    st.text(f"{len(df):,} rows")
                with cols_col:
                    st.text(f"{len(df.columns)} cols")
                with remove_col:
                    if st.button("❌", key=f"rm_{i}_{st.session_state.merger_counter}"):
                        st.session_state.merger_files.pop(i)
                        st.rerun()
            
            st.markdown("---")
            
            # Clear all button
            col_clear1, col_clear2 = st.columns([1, 1])
            with col_clear1:
                if st.button("🗑️ Clear All", use_container_width=True):
                    st.session_state.merger_files = []
                    st.session_state.merger_counter += 1
                    st.rerun()
            
            # Show column analysis
            with col_clear2:
                if st.button("🔍 Analyze Columns", use_container_width=True):
                    all_columns = set()
                    common_columns = None
                    
                    for filename, df in st.session_state.merger_files:
                        file_cols = set(df.columns)
                        all_columns.update(file_cols)
                        
                        if common_columns is None:
                            common_columns = file_cols
                        else:
                            common_columns = common_columns.intersection(file_cols)
                    
                    st.info(f"""
                    **Column Analysis:**
                    - Total unique columns across all files: {len(all_columns)}
                    - Common columns in all files: {len(common_columns)}
                    - Files with different structures: {'Yes' if len(all_columns) > len(common_columns) else 'No'}
                    """)
                    
                    if len(all_columns) > len(common_columns):
                        st.warning("⚠️ Files have different column structures. Smart Merge recommended.")
        else:
            st.info("No files added yet")
    
    # Show merged preview and download
    if len(st.session_state.merger_files) >= 2:
        st.markdown("---")
        st.subheader("📊 Merge & Download")
        
        # Analyze columns
        all_columns = set()
        common_columns = None
        file_column_info = []
        
        for filename, df in st.session_state.merger_files:
            file_cols = set(df.columns)
            all_columns.update(file_cols)
            file_column_info.append((filename, len(df.columns), list(df.columns)))
            
            if common_columns is None:
                common_columns = file_cols
            else:
                common_columns = common_columns.intersection(file_cols)
        
        # Show column info
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.metric("Total Unique Columns", len(all_columns))
        with col_info2:
            st.metric("Common Columns", len(common_columns))
        with col_info3:
            different = len(all_columns) > len(common_columns)
            st.metric("Different Structures", "Yes" if different else "No")
        
        # Show detailed column breakdown
        if len(all_columns) > len(common_columns):
            with st.expander("📋 Column Details by File", expanded=False):
                for filename, col_count, cols in file_column_info:
                    st.write(f"**{filename}** ({col_count} columns):")
                    st.write(", ".join(cols[:20]))
                    if len(cols) > 20:
                        st.write(f"... and {len(cols) - 20} more")
                    st.markdown("---")
        
        # Combine all dataframes based on merge mode
        try:
            with st.spinner("Merging files..."):
                if merge_mode == "Strict Merge (Only common columns)":
                    # Only keep common columns
                    if len(common_columns) == 0:
                        st.error("❌ No common columns found across all files. Cannot use Strict Merge mode.")
                        st.info("💡 Try 'Smart Merge' or 'Keep All Columns' mode instead.")
                        return
                    
                    # Filter each dataframe to only common columns
                    filtered_dfs = []
                    for filename, df in st.session_state.merger_files:
                        filtered_df = df[list(common_columns)]
                        filtered_dfs.append(filtered_df)
                    
                    combined_df = pd.concat(filtered_dfs, ignore_index=True)
                    st.info(f"ℹ️ Strict Merge: Kept only {len(common_columns)} common columns")
                
                else:  # Smart Merge or Keep All Columns (both do the same thing)
                    # Concatenate with all columns (union)
                    combined_df = pd.concat(
                        [df for _, df in st.session_state.merger_files], 
                        ignore_index=True,
                        sort=False  # Preserve column order
                    )
                    
                    if len(all_columns) > len(common_columns):
                        missing_cols = len(all_columns) - len(common_columns)
                        st.success(f"✅ Smart Merge: Combined all {len(all_columns)} unique columns. {missing_cols} columns had missing values filled with blanks.")
                
                # Auto-renumber serial number columns if they exist
                serial_col_names = ['S No.', 'S.No.', 'S No', 'SNo', 'Serial No', 'Sr No', 'Sr. No.', 'Sl No', 'Sl. No.']
                for col in combined_df.columns:
                    if col in serial_col_names or col.lower() in [s.lower() for s in serial_col_names]:
                        combined_df[col] = range(1, len(combined_df) + 1)
                        st.info(f"✅ Auto-renumbered column: '{col}'")
                        break
            
            # Stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Files", len(st.session_state.merger_files))
            with col2:
                st.metric("Total Rows", f"{len(combined_df):,}")
            with col3:
                st.metric("Final Columns", len(combined_df.columns))
            with col4:
                # Calculate total size estimate
                size_mb = combined_df.memory_usage(deep=True).sum() / (1024 * 1024)
                st.metric("Size", f"{size_mb:.1f} MB")
            
            # Show breakdown by file
            with st.expander("📋 Files Breakdown", expanded=False):
                breakdown_data = []
                for filename, df in st.session_state.merger_files:
                    breakdown_data.append({
                        'File Name': filename,
                        'Rows': len(df),
                        'Columns': len(df.columns)
                    })
                breakdown_df = pd.DataFrame(breakdown_data)
                st.dataframe(breakdown_df, use_container_width=True, hide_index=True)
            
            # Preview
            with st.expander("📋 Preview Merged Data (First 50 rows)", expanded=False):
                st.dataframe(combined_df.head(50), use_container_width=True)
            
            # Download buttons
            st.markdown("### ⬇️ Download Merged File")
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            download_col1, download_col2 = st.columns(2)
            
            with download_col1:
                with st.spinner("Generating Excel file..."):
                    excel_bytes = generate_merged_excel(combined_df)
                st.download_button(
                    label=f"📊 Download Excel ({len(combined_df):,} rows)",
                    data=excel_bytes,
                    file_name=f"merged_data_{timestamp}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary"
                )
            
            with download_col2:
                csv_bytes = generate_merged_csv(combined_df)
                st.download_button(
                    label=f"📄 Download CSV ({len(combined_df):,} rows)",
                    data=csv_bytes,
                    file_name=f"merged_data_{timestamp}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
        except Exception as e:
            st.error(f"❌ Error merging files: {str(e)}")
            st.exception(e)
            st.info("💡 Try a different merge mode or check your files for compatibility issues.")
    
    elif len(st.session_state.merger_files) == 1:
        st.markdown("---")
        st.info("📤 Add at least one more file to merge (minimum 2 files required).")
    
    else:
        st.markdown("---")
        st.info("📤 Upload and add files to get started (minimum 2 files required).")
        
        # Show usage tips
        with st.expander("💡 Usage Tips", expanded=False):
            st.markdown("""
            **How to use:**
            1. Select your merge mode (Smart Merge recommended for different file structures)
            2. Upload your first Excel/CSV file
            3. Click "Add This File" button
            4. Upload and add more files (minimum 2 files)
            5. Click "Analyze Columns" to see column compatibility
            6. Download the merged file
            
            **Merge Modes:**
            - **Smart Merge**: Best for files with different columns. Combines all columns and fills missing values with blanks.
            - **Strict Merge**: Only keeps columns that exist in ALL files. Use when you want only common data.
            - **Keep All Columns**: Same as Smart Merge.
            
            **Important:**
            - Files can have completely different column structures
            - Smart Merge will handle missing columns automatically
            - Serial numbers (S No.) will be auto-renumbered
            - Empty files will be rejected
            
            **Supported formats:**
            - Excel: .xlsx, .xls
            - CSV: .csv (UTF-8 and Latin-1 encoding)
            
            **Examples:**
            - File 1 has columns: Name, Age, City
            - File 2 has columns: Name, Salary, Department
            - Smart Merge result: Name, Age, City, Salary, Department (with blanks where data is missing)
            - Strict Merge result: Name only (the only common column)
            """)
