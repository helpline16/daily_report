"""
Bulk MySQL Import Module
Import all Excel files from a folder into MySQL database
"""

import streamlit as st
import pandas as pd
import os
from pathlib import Path
import mysql.connector
from mysql.connector import Error
import re
from typing import List, Tuple, Generator, Optional


def get_db_connection(host: str, port: int, user: str, password: str, database: Optional[str] = None):
    """Helper to establish a MySQL connection."""
    config = {
        'host': host,
        'port': port,
        'user': user,
        'password': password
    }
    if database:
        config['database'] = database
    return mysql.connector.connect(**config)


def sanitize_name(name: str, prefix: str = 'item_', max_len: int = 64) -> str:
    """Core sanitization logic for generating valid MySQL names."""
    name_str = str(name)
    # Replace spaces and special characters with underscores
    name_str = re.sub(r'[^a-zA-Z0-9_]', '_', name_str)
    # Remove consecutive underscores and trim
    name_str = re.sub(r'_+', '_', name_str).strip('_')
    
    # Ensure it starts with a letter or underscore
    if name_str and name_str[0].isdigit():
        name_str = prefix + name_str
        
    # If empty after cleaning, use a default fallback
    if not name_str:
        name_str = f"{prefix}default"
        
    # Limit length to MySQL constraint and lowercase
    return name_str[:max_len].lower()


def sanitize_table_name(filename: str) -> str:
    """Convert filename to valid MySQL table name."""
    return sanitize_name(Path(filename).stem, prefix='table_')


def sanitize_column_name(col_name: str) -> str:
    """Sanitize column name for MySQL."""
    return sanitize_name(col_name, prefix='col_')


def create_table_from_dataframe(cursor, table_name: str, df: pd.DataFrame) -> List[str]:
    """Create MySQL table based on DataFrame structure."""
    cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
    table_exists = cursor.fetchone() is not None
    
    sanitized_columns = [sanitize_column_name(col) for col in df.columns]
    
    if not table_exists:
        columns = ["`id` INT AUTO_INCREMENT PRIMARY KEY"]
        # Always use TEXT for all dynamic columns for safety and broad compatibility
        for col_name in sanitized_columns:
            columns.append(f"`{col_name}` TEXT")
        
        create_statement = f"CREATE TABLE `{table_name}` ({', '.join(columns)})"
        cursor.execute(create_statement)
    
    return sanitized_columns


def insert_dataframe_to_mysql(connection, cursor, table_name: str, df: pd.DataFrame, sanitized_columns: List[str]) -> Generator[Tuple[float, int, int], None, None]:
    """Insert DataFrame data into MySQL table - Skip duplicates, add only new records."""
    # Efficiently convert data to strings and handle nulls
    df_copy = df.astype(str)
    for col in df_copy.columns:
        df_copy[col] = df_copy[col].replace(['nan', 'None', ''], None)
    
    # Fetch existing data from table to check for duplicates
    existing_set = set()
    try:
        columns_str = ', '.join([f"`{col}`" for col in sanitized_columns])
        cursor.execute(f"SELECT {columns_str} FROM `{table_name}`")
        existing_rows = cursor.fetchall()
        existing_set = set(existing_rows)
    except Error:
        # Table might be empty, might not exist yet, or columns don't match
        pass
    
    placeholders = ', '.join(['%s'] * len(sanitized_columns))
    columns_str = ', '.join([f"`{col}`" for col in sanitized_columns])
    insert_statement = f"INSERT IGNORE INTO `{table_name}` ({columns_str}) VALUES ({placeholders})"
    
    batch_size = 1000
    total_rows = len(df_copy)
    inserted_count = 0
    skipped_count = 0
    
    # Process in batches
    for i in range(0, total_rows, batch_size):
        batch = df_copy.iloc[i:i+batch_size]
        new_rows = []
        
        for row in batch.values:
            row_tuple = tuple(row)
            if row_tuple not in existing_set:
                new_rows.append(row_tuple)
                existing_set.add(row_tuple)
            else:
                skipped_count += 1
        
        if new_rows:
            cursor.executemany(insert_statement, new_rows)
            connection.commit()
            inserted_count += len(new_rows)
        
        progress = min((i + batch_size) / total_rows, 1.0)
        yield progress, inserted_count, skipped_count


def render_bulk_mysql_import_page():
    """Render the Bulk MySQL Import page."""
    
    st.title("📊 Bulk MySQL Import")
    st.markdown("Import all Excel files from a folder into MySQL database")
    st.markdown("---")
    
    st.subheader("📁 Step 1: Select Folder")
    default_path = r"D:\layerwise fin.year25-26"
    folder_path = st.text_input(
        "Folder Path:",
        value=default_path,
        help="Enter the full path to the folder containing Excel files"
    )
    
    excel_files = []
    if folder_path and os.path.exists(folder_path):
        st.success(f"✅ Folder found: {folder_path}")
        
        for file in os.listdir(folder_path):
            if file.lower().endswith(('.xlsx', '.xls', '.xlsm')):
                excel_files.append(file)
        
        if excel_files:
            st.info(f"📋 Found {len(excel_files)} Excel file(s)")
            with st.expander("📄 View Files", expanded=False):
                for idx, file in enumerate(excel_files, 1):
                    file_path = os.path.join(folder_path, file)
                    file_size = os.path.getsize(file_path) / (1024 * 1024)
                    st.text(f"{idx}. {file} ({file_size:.2f} MB)")
        else:
            st.warning("⚠️ No Excel files found in this folder")
            return
    elif folder_path:
        st.error(f"❌ Folder not found: {folder_path}")
        return
    else:
        st.info("👆 Please enter a folder path")
        return
    
    st.markdown("---")
    st.subheader("🔌 Step 2: MySQL Connection")
    
    col1, col2 = st.columns(2)
    with col1:
        host = st.text_input("Host:", value="localhost", key="mysql_host")
        database = st.text_input("Database:", value="fraud_analysis", key="mysql_database")
        user = st.text_input("Username:", value="root", key="mysql_user")
    
    with col2:
        port = st.number_input("Port:", value=3306, min_value=1, max_value=65535, key="mysql_port")
        password = st.text_input("Password:", type="password", key="mysql_password")
    
    if st.button("🔍 Test Connection", use_container_width=True):
        try:
            connection = get_db_connection(host, port, user, password, database)
            if connection.is_connected():
                st.success("✅ Connection successful!")
                connection.close()
        except Error as e:
            st.error(f"❌ Connection failed: {str(e)}")
    
    st.markdown("---")
    st.subheader("⚙️ Step 3: Import Options")
    
    col1, col2 = st.columns(2)
    with col1:
        table_prefix = st.text_input(
            "Table Name Prefix (optional):",
            value="layerwise_",
            help="Prefix to add to all table names"
        )
    
    with col2:
        skip_errors = st.checkbox(
            "Skip files with errors",
            value=True,
            help="Continue importing even if some files fail"
        )
    
    st.markdown("**Select files to import:**")
    selected_files = st.multiselect(
        "Choose files:",
        options=excel_files,
        default=excel_files,
        help="Select which files to import"
    )
    
    if not selected_files:
        st.warning("⚠️ Please select at least one file to import")
        return
    
    st.markdown("---")
    st.subheader("📋 Step 4: Configure Table Names")
    
    import_mode = st.radio(
        "Import Mode:",
        options=[
            "📁 Separate tables (one table per file)",
            "📊 Single table (all files into one table)"
        ],
        help="Choose whether to create separate tables or combine all files into one table"
    )
    
    use_single_table = "Single table" in import_mode
    
    existing_tables = []
    try:
        test_connection = get_db_connection(host, port, user, password, database)
        test_cursor = test_connection.cursor()
        test_cursor.execute("SHOW TABLES")
        existing_tables = [table[0] for table in test_cursor.fetchall()]
        test_cursor.close()
        test_connection.close()
        
        if existing_tables:
            st.info(f"📊 Found {len(existing_tables)} existing table(s) in database")
    except Error:
        pass
    
    if 'table_mappings' not in st.session_state:
        st.session_state.table_mappings = {}
    
    table_mappings = {}
    
    if use_single_table:
        st.markdown("**All selected files will be imported into ONE table:**")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            use_existing = st.checkbox(
                "Use existing table",
                key="single_use_existing",
                help="Select an existing table to append all data"
            )
            
            if use_existing and existing_tables:
                single_table_name = st.selectbox(
                    "Select existing table:",
                    options=existing_tables,
                    key="single_existing_table",
                    help="All files will be imported into this table"
                )
            else:
                default_single_name = table_prefix + "combined_import"
                single_table_name = st.text_input(
                    "Table name:",
                    value=default_single_name,
                    key="single_table_name",
                    help="Enter table name for all files"
                )
        
        with col2:
            st.markdown("**Preview:**")
            st.code(single_table_name, language="sql")
        
        for filename in selected_files:
            table_mappings[filename] = single_table_name
            
        st.success(f"✅ All {len(selected_files)} file(s) will be imported into: `{single_table_name}`")
    
    else:
        st.markdown("**Choose table name for each file:**")
        for idx, filename in enumerate(selected_files):
            st.markdown(f"**File {idx + 1}: `{filename}`**")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                default_table_name = table_prefix + sanitize_table_name(filename)
                saved_mapping = st.session_state.table_mappings.get(filename, default_table_name)
                
                use_existing = st.checkbox(
                    f"Use existing table",
                    key=f"use_existing_{idx}",
                    help="Select an existing table to append data"
                )
                
                if use_existing and existing_tables:
                    selected_table = st.selectbox(
                        f"Select existing table:",
                        options=existing_tables,
                        key=f"existing_table_{idx}",
                        help="Choose which table to append data to"
                    )
                    table_mappings[filename] = selected_table
                else:
                    table_name_input = st.text_input(
                        f"Table name:",
                        value=saved_mapping,
                        key=f"table_name_{idx}",
                        help="Enter custom table name or use default"
                    )
                    table_mappings[filename] = table_name_input
            
            with col2:
                st.markdown("**Preview:**")
                st.code(table_mappings[filename], language="sql")
            
            st.markdown("---")
    
    st.session_state.table_mappings = table_mappings
    
    st.markdown("---")
    st.subheader("🚀 Step 5: Start Import")
    
    with st.expander("📝 Import Summary - Review Table Mappings", expanded=True):
        st.markdown("**Files → Tables:**")
        
        summary_data = []
        for filename in selected_files:
            table_name = table_mappings.get(filename, table_prefix + sanitize_table_name(filename))
            is_existing = table_name in existing_tables
            status = "📊 Append to existing" if is_existing else "✨ Create new"
            
            summary_data.append({
                'File': filename,
                'Table Name': table_name,
                'Status': status
            })
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    st.info(f"📊 Ready to import {len(selected_files)} file(s)")
    
    if st.button("🚀 Start Import", type="primary", use_container_width=True):
        connection = None
        cursor = None
        
        try:
            with st.spinner("Connecting to MySQL..."):
                connection = get_db_connection(host, port, user, password, database)
                cursor = connection.cursor()
            
            st.success("✅ Connected to MySQL")
            
            total_files = len(selected_files)
            successful_imports = 0
            failed_imports = 0
            total_records = 0
            
            overall_progress = st.progress(0)
            status_text = st.empty()
            
            for idx, filename in enumerate(selected_files):
                file_path = os.path.join(folder_path, filename)
                table_name = table_mappings.get(filename, table_prefix + sanitize_table_name(filename))
                
                status_text.text(f"Processing {idx + 1}/{total_files}: {filename} → {table_name}")
                
                try:
                    with st.spinner(f"Reading {filename}..."):
                        df = pd.read_excel(file_path, dtype=str)
                        df.columns = [sanitize_column_name(col) for col in df.columns]
                    
                    if df.empty:
                        st.warning(f"⚠️ Skipped {filename}: Empty file")
                        failed_imports += 1
                        continue
                    
                    with st.spinner(f"Configuring table: {table_name}..."):
                        sanitized_columns = list(df.columns)
                        cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
                        table_exists = cursor.fetchone() is not None
                        
                        if not table_exists:
                            columns = ["`id` INT AUTO_INCREMENT PRIMARY KEY"]
                            for col_name in sanitized_columns:
                                columns.append(f"`{col_name}` TEXT")
                            
                            create_statement = f"CREATE TABLE `{table_name}` ({', '.join(columns)})"
                            cursor.execute(create_statement)
                            st.info(f"✨ Created new table: `{table_name}`")
                        else:
                            st.info(f"📋 Table `{table_name}` already exists, appending new records")
                    
                    st.info(f"📥 Importing {len(df):,} records into `{table_name}`...")
                    progress_bar = st.progress(0)
                    progress_info = st.empty()
                    
                    rows_inserted, rows_skipped = 0, 0
                    for progress, r_insert, r_skip in insert_dataframe_to_mysql(
                        connection, cursor, table_name, df, sanitized_columns
                    ):
                        progress_bar.progress(progress)
                        rows_inserted, rows_skipped = r_insert, r_skip
                        progress_info.text(f"Inserted: {rows_inserted:,} | Skipped: {rows_skipped:,} | Total: {len(df):,}")
                    
                    progress_bar.empty()
                    progress_info.empty()
                    
                    if rows_skipped > 0:
                        st.success(f"✅ {filename} → `{table_name}` ({rows_inserted:,} new records, {rows_skipped:,} duplicates skipped)")
                    else:
                        st.success(f"✅ {filename} → `{table_name}` ({rows_inserted:,} records)")
                    
                    successful_imports += 1
                    total_records += rows_inserted
                    
                except Exception as e:
                    st.error(f"❌ Failed to import {filename}: {str(e)}")
                    failed_imports += 1
                    if not skip_errors:
                        raise e
                
                overall_progress.progress((idx + 1) / total_files)
            
            st.markdown("---")
            st.subheader("📊 Import Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Files", total_files)
            with col2:
                st.metric("Successful", successful_imports, delta=f"{successful_imports}/{total_files}")
            with col3:
                st.metric("Failed", failed_imports, delta=f"-{failed_imports}" if failed_imports > 0 else "0")
            with col4:
                st.metric("Total Records", f"{total_records:,}")
            
            if successful_imports > 0:
                st.balloons()
                st.success(f"🎉 Import completed! {successful_imports} file(s) imported successfully.")
                
                with st.expander("📋 View Imported Tables", expanded=False):
                    cursor.execute("SHOW TABLES")
                    tables = cursor.fetchall()
                    
                    st.markdown("**Tables in database:**")
                    for table in tables:
                        tbl_name = table[0]
                        if tbl_name.startswith(table_prefix):
                            cursor.execute(f"SELECT COUNT(*) FROM `{tbl_name}`")
                            count = cursor.fetchone()[0]
                            st.text(f"• {tbl_name}: {count:,} rows")
            
            if failed_imports > 0:
                st.warning(f"⚠️ {failed_imports} file(s) failed to import.")
        
        except Error as e:
            st.error(f"❌ MySQL Error: {str(e)}")
            st.exception(e)
        except Exception as e:
            st.error(f"❌ Error during import: {str(e)}")
            st.exception(e)
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
                st.info("🔌 MySQL connection closed")
    
    st.markdown("---")
    with st.expander("ℹ️ Instructions & Notes"):
        st.markdown("""
        ### How to use:
        
        1. **Enter folder path** containing Excel files
        2. **Configure MySQL connection** (host, database, username, password)
        3. **Test connection** to ensure it works
        4. **Select files** to import
        5. **Choose import mode**:
           - **Separate tables**: One table per file
           - **Single table**: All files into one table
        6. **Configure table names**:
           - For single table: Choose one table name for all files
           - For separate tables: Choose name for each file
           - Option to use existing tables
        7. **Review mapping summary** to verify assignments
        8. **Click Start Import** to begin
        
        ### Important Notes:
        
        - **Data Types**: ALL columns stored as TEXT for maximum compatibility. No strict data validation.
        - **Duplicate Handling**: Smart duplicate detection skips duplicates but properly inserts new ones.
        - **Large Files**: Imported in batches of 1000 rows for efficiency.
        """)
        
    st.markdown("---")
    st.caption("📊 Bulk MySQL Import | Import Excel files to MySQL database")
