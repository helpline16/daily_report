"""
MySQL Database Viewer Module
View, search, filter, and download data from MySQL tables
"""

import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from io import BytesIO
from typing import Dict, Any, Optional


def get_db_connection(params: Dict[str, Any]) -> mysql.connector.MySQLConnection:
    """Establish and return a MySQL database connection."""
    return mysql.connector.connect(**params)


def generate_excel_bytes(df: pd.DataFrame) -> bytes:
    """Generate Excel file bytes from DataFrame."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
    return output.getvalue()


def render_mysql_database_viewer_page():
    """Render the MySQL Database Viewer page."""
    
    st.title("🗄️ MySQL Database Viewer")
    st.markdown("Browse, search, and download data from MySQL tables")
    st.markdown("---")
    
    st.subheader("🔌 Step 1: Connect to Database")
    
    col1, col2 = st.columns(2)
    with col1:
        host = st.text_input("Host:", value="localhost", key="viewer_mysql_host")
        database = st.text_input("Database:", value="fraud_analysis", key="viewer_mysql_database")
        user = st.text_input("Username:", value="root", key="viewer_mysql_user")
    
    with col2:
        port = st.number_input("Port:", value=3306, min_value=1, max_value=65535, key="viewer_mysql_port")
        password = st.text_input("Password:", type="password", key="viewer_mysql_password")
    
    if st.button("🔗 Connect to Database", type="primary", use_container_width=True):
        conn_params = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database
        }
        try:
            connection = get_db_connection(conn_params)
            if connection.is_connected():
                st.session_state.db_connection_params = conn_params
                st.session_state.db_connected = True
                connection.close()
                st.success("✅ Connected successfully!")
                st.rerun()
        except Error as e:
            st.error(f"❌ Connection failed: {str(e)}")
            st.session_state.db_connected = False
    
    if not st.session_state.get('db_connected', False):
        st.info("👆 Please connect to database to continue")
        return
    
    conn_params = st.session_state.get('db_connection_params', {})
    
    try:
        connection = get_db_connection(conn_params)
        cursor = connection.cursor()
        
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        
        if not tables:
            st.warning("⚠️ No tables found in database")
            cursor.close()
            connection.close()
            return
        
        st.markdown("---")
        st.subheader("📊 Database Overview")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Database", conn_params.get('database', 'Unknown'))
        with col2:
            st.metric("Total Tables", len(tables))
        with col3:
            total_records = 0
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                    total_records += cursor.fetchone()[0]
                except Error:
                    pass
            st.metric("Total Records", f"{total_records:,}")
        
        st.markdown("---")
        st.subheader("📋 Step 2: Select Table")
        
        table_info = []
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                count = cursor.fetchone()[0]
                table_info.append({'Table': table, 'Rows': f"{count:,}"})
            except Error:
                table_info.append({'Table': table, 'Rows': 'Error'})
        
        with st.expander("📋 View All Tables", expanded=False):
            table_df = pd.DataFrame(table_info)
            st.dataframe(table_df, use_container_width=True, hide_index=True)
        
        # Bulk delete tables section
        with st.expander("🗑️ Bulk Delete Tables (Danger Zone)", expanded=False):
            st.error("⚠️ **DANGER ZONE** - Delete multiple tables at once!")
            
            st.markdown("**Select tables to delete:**")
            
            tables_to_delete = st.multiselect(
                "Choose tables:",
                options=tables,
                help="Select one or more tables to delete permanently"
            )
            
            if tables_to_delete:
                st.warning(f"**You are about to delete {len(tables_to_delete)} table(s):**")
                
                # Show tables to be deleted with row counts
                delete_preview = []
                total_rows_to_delete = 0
                
                for table in tables_to_delete:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                        count = cursor.fetchone()[0]
                        total_rows_to_delete += count
                        delete_preview.append({
                            'Table': table,
                            'Rows': f"{count:,}",
                            'Status': '🗑️ Will be deleted'
                        })
                    except:
                        delete_preview.append({
                            'Table': table,
                            'Rows': 'Unknown',
                            'Status': '🗑️ Will be deleted'
                        })
                
                delete_df = pd.DataFrame(delete_preview)
                st.dataframe(delete_df, use_container_width=True, hide_index=True)
                
                st.error(f"**Total records to be deleted: {total_rows_to_delete:,}**")
                
                st.warning("""
                **Warning:**
                - All data in these tables will be permanently deleted
                - This action cannot be undone
                - Make sure you have backups
                """)
                
                # First confirmation
                confirm_bulk_delete = st.checkbox(
                    f"I understand that deleting {len(tables_to_delete)} table(s) will permanently remove {total_rows_to_delete:,} records",
                    key="confirm_bulk_delete_checkbox"
                )
                
                if confirm_bulk_delete:
                    st.markdown("---")
                    st.markdown("**🔐 Final Confirmation Required**")
                    
                    # Type confirmation phrase
                    confirmation_phrase = f"DELETE {len(tables_to_delete)} TABLES"
                    
                    typed_confirmation = st.text_input(
                        f"Type `{confirmation_phrase}` to confirm bulk deletion:",
                        key="typed_bulk_confirmation",
                        placeholder="Type confirmation phrase exactly"
                    )
                    
                    if typed_confirmation == confirmation_phrase:
                        st.success("✅ Confirmation phrase verified")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button(f"🗑️ DELETE {len(tables_to_delete)} TABLES PERMANENTLY", type="primary", use_container_width=True):
                                success_count = 0
                                error_count = 0
                                
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                for idx, table in enumerate(tables_to_delete):
                                    status_text.text(f"Deleting {table}...")
                                    
                                    try:
                                        drop_query = f"DROP TABLE `{table}`"
                                        cursor.execute(drop_query)
                                        connection.commit()
                                        
                                        st.success(f"✅ Deleted: {table}")
                                        success_count += 1
                                        
                                    except Exception as e:
                                        st.error(f"❌ Failed to delete {table}: {str(e)}")
                                        error_count += 1
                                    
                                    progress_bar.progress((idx + 1) / len(tables_to_delete))
                                
                                progress_bar.empty()
                                status_text.empty()
                                
                                # Summary
                                if success_count > 0:
                                    st.success(f"🎉 Successfully deleted {success_count} table(s)")
                                    st.balloons()
                                if error_count > 0:
                                    st.warning(f"⚠️ Failed to delete {error_count} table(s)")
                                
                                # Clear session state
                                if 'current_df' in st.session_state:
                                    del st.session_state.current_df
                                if 'current_table' in st.session_state:
                                    del st.session_state.current_table
                                
                                st.info("🔄 Refreshing page...")
                                
                                import time
                                time.sleep(2)
                                st.rerun()
                        
                        with col2:
                            if st.button("❌ Cancel Bulk Delete", use_container_width=True):
                                st.info("Bulk deletion cancelled")
                                st.rerun()
                    
                    elif typed_confirmation:
                        st.error(f"❌ Confirmation phrase doesn't match")
                        st.info(f"Please type exactly: `{confirmation_phrase}`")
            else:
                st.info("👆 Select tables above to delete them")
        
        selected_table = st.selectbox(
            "Choose a table:",
            options=tables,
            key="selected_table",
            help="Select which table to view"
        )
        
        if selected_table:
            cursor.execute(f"DESCRIBE `{selected_table}`")
            columns_info = cursor.fetchall()
            column_names = [col[0] for col in columns_info]
            
            cursor.execute(f"SELECT COUNT(*) FROM `{selected_table}`")
            total_rows = cursor.fetchone()[0]
            
            st.success(f"✅ Selected: `{selected_table}` ({total_rows:,} rows, {len(column_names)} columns)")
            
            # Delete table section
            with st.expander("🗑️ Delete Table (Danger Zone)", expanded=False):
                st.error("⚠️ **DANGER ZONE** - This action cannot be undone!")
                st.markdown(f"**Table to delete:** `{selected_table}`")
                st.markdown(f"**Records:** {total_rows:,} rows")
                st.markdown(f"**Columns:** {len(column_names)}")
                
                st.warning("""
                **Warning:**
                - All data in this table will be permanently deleted
                - This action cannot be undone
                - Make sure you have a backup
                """)
                
                # First confirmation
                confirm_delete = st.checkbox(
                    f"I understand that deleting `{selected_table}` will permanently remove all {total_rows:,} records",
                    key="confirm_delete_checkbox"
                )
                
                if confirm_delete:
                    st.markdown("---")
                    st.markdown("**🔐 Final Confirmation Required**")
                    
                    # Type table name to confirm
                    typed_table_name = st.text_input(
                        f"Type the table name `{selected_table}` to confirm deletion:",
                        key="typed_table_name",
                        placeholder="Enter table name exactly as shown"
                    )
                    
                    # Check if typed name matches
                    if typed_table_name == selected_table:
                        st.success("✅ Table name confirmed")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("🗑️ DELETE TABLE PERMANENTLY", type="primary", use_container_width=True):
                                try:
                                    # Drop table
                                    drop_query = f"DROP TABLE `{selected_table}`"
                                    cursor.execute(drop_query)
                                    connection.commit()
                                    
                                    st.success(f"✅ Table `{selected_table}` has been deleted successfully")
                                    st.balloons()
                                    
                                    # Clear session state
                                    if 'current_df' in st.session_state:
                                        del st.session_state.current_df
                                    if 'current_table' in st.session_state:
                                        del st.session_state.current_table
                                    
                                    st.info("🔄 Refreshing page...")
                                    
                                    # Wait a moment then refresh
                                    import time
                                    time.sleep(2)
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"❌ Error deleting table: {str(e)}")
                        
                        with col2:
                            if st.button("❌ Cancel", use_container_width=True):
                                st.info("Deletion cancelled")
                                st.rerun()
                    
                    elif typed_table_name:
                        st.error(f"❌ Table name doesn't match. You typed: `{typed_table_name}`")
                        st.info(f"Please type exactly: `{selected_table}`")
            
            with st.expander("🔍 Table Structure", expanded=False):
                structure_data = [{
                    'Column': col[0],
                    'Type': col[1],
                    'Null': col[2],
                    'Key': col[3],
                    'Default': col[4],
                    'Extra': col[5]
                } for col in columns_info]
                st.dataframe(pd.DataFrame(structure_data), use_container_width=True, hide_index=True)
            
            with st.expander("🔧 Modify Column Data Types", expanded=False):
                st.markdown("**Change column data types for better query performance:**")
                st.info("💡 All columns initially start as TEXT. Convert to appropriate types for faster queries and sorting.")
                
                data_types = [
                    'TEXT', 'VARCHAR(255)', 'VARCHAR(500)', 'INT', 'BIGINT',
                    'DECIMAL(10,2)', 'DECIMAL(15,2)', 'DOUBLE', 'FLOAT',
                    'DATE', 'DATETIME', 'TIMESTAMP', 'BOOLEAN', 'TINYINT', 'SMALLINT'
                ]
                
                columns_to_modify = st.multiselect(
                    "Choose columns to modify:",
                    options=column_names,
                    help="Select which columns you want to change data type"
                )
                
                if columns_to_modify:
                    st.markdown("**Set new data types:**")
                    type_changes = {}
                    
                    for col in columns_to_modify:
                        col1, col2, col3 = st.columns([2, 2, 1])
                        with col1:
                            st.text(f"Column: {col}")
                        with col2:
                            current_type = next((c[1] for c in columns_info if c[0] == col), 'TEXT')
                            new_type = st.selectbox(
                                f"New type for {col}:",
                                options=data_types,
                                index=data_types.index('TEXT') if 'TEXT' in data_types else 0,
                                key=f"type_{col}",
                                label_visibility="collapsed"
                            )
                            type_changes[col] = new_type
                        with col3:
                            st.caption(f"Current: {current_type}")
                    
                    st.markdown("---")
                    st.markdown("**Preview changes:**")
                    preview_data = []
                    for col, new_type in type_changes.items():
                        current_type = next((c[1] for c in columns_info if c[0] == col), 'TEXT')
                        preview_data.append({
                            'Column': col,
                            'Current Type': current_type,
                            'New Type': new_type,
                            'Change': '→'
                        })
                    
                    st.dataframe(pd.DataFrame(preview_data), use_container_width=True, hide_index=True)
                    st.warning("⚠️ **Warning**: Changing data types may fail if existing data is incompatible. Backup your data first!")
                    
                    col_apply1, col_apply2 = st.columns(2)
                    with col_apply1:
                        if st.button("🔄 Apply Changes", type="primary", use_container_width=True):
                            success_count, error_count = 0, 0
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            for idx, (col, new_type) in enumerate(type_changes.items()):
                                status_text.text(f"Modifying {col}...")
                                try:
                                    alter_query = f"ALTER TABLE `{selected_table}` MODIFY COLUMN `{col}` {new_type}"
                                    cursor.execute(alter_query)
                                    connection.commit()
                                    st.toast(f"✅ {col}: {new_type}")
                                    success_count += 1
                                except Error as e:
                                    st.error(f"❌ {col}: {str(e)}")
                                    error_count += 1
                                
                                progress_bar.progress((idx + 1) / len(type_changes))
                            
                            progress_bar.empty()
                            status_text.empty()
                            
                            if success_count > 0:
                                st.success(f"🎉 Successfully modified {success_count} column(s)")
                            if error_count > 0:
                                st.warning(f"⚠️ Failed to modify {error_count} column(s)")
                            
                            if success_count > 0:
                                st.info("🔄 Refresh the page to see updated column types")
                                if st.button("🔄 Refresh Now"):
                                    st.rerun()
                    
                    with col_apply2:
                        st.markdown("**💡 Quick Suggestions:**")
                        if st.button("📊 Auto-detect Types", use_container_width=True):
                            st.info("""
                            **Suggested conversions:**
                            - Numeric columns → INT, BIGINT, DECIMAL
                            - Date columns → DATE, DATETIME
                            - Short text → VARCHAR(255)
                            - Long text → TEXT
                            - Yes/No → BOOLEAN
                            """)
                else:
                    st.info("👆 Select columns above to modify their data types")
                
                st.markdown("---")
                st.markdown("**🚀 Quick Bulk Conversions:**")
                col_b1, col_b2, col_b3 = st.columns(3)
                
                with col_b1:
                    if st.button("💰 Convert Amount Columns", use_container_width=True):
                        st.session_state.bulk_convert_type = 'amount'
                        st.session_state.show_bulk_convert = True
                with col_b2:
                    if st.button("🔢 Convert ID Columns", use_container_width=True):
                        st.session_state.bulk_convert_type = 'id'
                        st.session_state.show_bulk_convert = True
                with col_b3:
                    if st.button("📅 Convert Date Columns", use_container_width=True):
                        st.session_state.bulk_convert_type = 'date'
                        st.session_state.show_bulk_convert = True
                
                if st.session_state.get('show_bulk_convert', False):
                    convert_type = st.session_state.get('bulk_convert_type', '')
                    st.markdown("---")
                    st.markdown(f"**Bulk Conversion: {convert_type.upper()}**")
                    
                    suggested_columns = []
                    target_type = 'TEXT'
                    
                    if convert_type == 'amount':
                        keywords = ['amount', 'value', 'price', 'total', 'sum', 'balance']
                        suggested_columns = [col for col in column_names if any(kw in col.lower() for kw in keywords)]
                        target_type = 'DECIMAL(15,2)'
                        st.info("💡 Converting to DECIMAL(15,2) for precise monetary calculations")
                    elif convert_type == 'id':
                        keywords = ['id', '_no', 'number', 'count', 'serial', 'ack']
                        suggested_columns = [col for col in column_names if any(kw in col.lower() for kw in keywords)]
                        target_type = 'BIGINT'
                        st.info("💡 Converting to BIGINT for large integer values")
                    elif convert_type == 'date':
                        keywords = ['date', 'time', 'created', 'updated', 'timestamp']
                        suggested_columns = [col for col in column_names if any(kw in col.lower() for kw in keywords)]
                        target_type = 'DATETIME'
                        st.info("💡 Converting to DATETIME for date/time values")
                    
                    if suggested_columns:
                        st.markdown(f"**Found {len(suggested_columns)} matching column(s):**")
                        selected_bulk_columns = st.multiselect(
                            "Select columns to convert:",
                            options=suggested_columns,
                            default=suggested_columns,
                            key="bulk_columns"
                        )
                        
                        if selected_bulk_columns:
                            st.markdown(f"**Will convert {len(selected_bulk_columns)} column(s) to `{target_type}`**")
                            bulk_preview = [{
                                'Column': col,
                                'Current': next((c[1] for c in columns_info if c[0] == col), 'TEXT'),
                                '→': '→',
                                'New': target_type
                            } for col in selected_bulk_columns]
                            
                            st.dataframe(pd.DataFrame(bulk_preview), use_container_width=True, hide_index=True)
                            
                            col_conf1, col_conf2 = st.columns(2)
                            with col_conf1:
                                if st.button("✅ Apply Bulk Conversion", type="primary", use_container_width=True):
                                    success_count, error_count = 0, 0
                                    progress_bar = st.progress(0)
                                    status_text = st.empty()
                                    
                                    for idx, col in enumerate(selected_bulk_columns):
                                        status_text.text(f"Converting {col}...")
                                        try:
                                            alter_query = f"ALTER TABLE `{selected_table}` MODIFY COLUMN `{col}` {target_type}"
                                            cursor.execute(alter_query)
                                            connection.commit()
                                            st.toast(f"✅ Converted {col}")
                                            success_count += 1
                                        except Error as e:
                                            st.error(f"❌ {col}: {str(e)}")
                                            error_count += 1
                                        
                                        progress_bar.progress((idx + 1) / len(selected_bulk_columns))
                                    
                                    progress_bar.empty()
                                    status_text.empty()
                                    
                                    if success_count > 0:
                                        st.success(f"🎉 Successfully converted {success_count} column(s)")
                                    if error_count > 0:
                                        st.warning(f"⚠️ Failed to convert {error_count} column(s)")
                                    
                                    st.session_state.show_bulk_convert = False
                                    if st.button("🔄 Refresh Page"):
                                        st.rerun()
                            
                            with col_conf2:
                                if st.button("❌ Cancel", use_container_width=True):
                                    st.session_state.show_bulk_convert = False
                                    st.rerun()
                    else:
                        st.warning(f"⚠️ No columns found matching {convert_type} pattern")
                        if st.button("❌ Close"):
                            st.session_state.show_bulk_convert = False
                            st.rerun()
            
            st.markdown("---")
            st.subheader("📊 Step 3: View & Filter Data")
            
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                limit = st.number_input("Rows to display:", min_value=10, max_value=10000, value=100, step=10, help="Number of rows to display")
            with col_f2:
                offset = st.number_input("Start from row:", min_value=0, max_value=max(0, total_rows - 1), value=0, step=100, help="Skip first N rows")
            with col_f3:
                sort_column = st.selectbox("Sort by:", options=['-- No sorting --'] + column_names, help="Sort data by column")
            
            st.markdown("**🔍 Search in table:**")
            col_s1, col_s2 = st.columns([2, 1])
            with col_s1:
                search_term = st.text_input("Search term:", placeholder="Enter text to search across all columns...", key="search_term")
            with col_s2:
                search_column = st.selectbox("Search in column:", options=['-- All columns --'] + column_names, help="Limit search to specific column")
            
            # Construct Query Securely
            query = f"SELECT * FROM `{selected_table}`"
            search_params = []
            
            if search_term:
                if search_column == '-- All columns --':
                    conditions = [f"`{col}` LIKE %s" for col in column_names]
                    query += f" WHERE {' OR '.join(conditions)}"
                    search_params = [f"%{search_term}%"] * len(column_names)
                else:
                    query += f" WHERE `{search_column}` LIKE %s"
                    search_params = [f"%{search_term}%"]
            
            if sort_column != '-- No sorting --':
                query += f" ORDER BY `{sort_column}` DESC"
            
            query += f" LIMIT {limit} OFFSET {offset}"
            
            if st.button("📊 Load Data", type="primary", use_container_width=True):
                try:
                    with st.spinner("Loading data..."):
                        cursor.execute(query, tuple(search_params))
                        rows = cursor.fetchall()
                        
                        if rows:
                            df = pd.DataFrame(rows, columns=column_names)
                            st.session_state.current_df = df
                            st.session_state.current_table = selected_table
                            st.success(f"✅ Loaded {len(df):,} rows")
                        else:
                            st.warning("⚠️ No data found matching your criteria")
                            st.session_state.current_df = None
                except Error as e:
                    st.error(f"❌ Error loading data: {str(e)}")
                    st.exception(e)
            
            if st.session_state.get('current_df') is not None:
                df = st.session_state.current_df
                
                st.markdown("---")
                st.subheader("📋 Data Preview")
                
                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                with col_stat1:
                    st.metric("Rows Displayed", f"{len(df):,}")
                with col_stat2:
                    st.metric("Total Rows", f"{total_rows:,}")
                with col_stat3:
                    st.metric("Columns", len(df.columns))
                with col_stat4:
                    coverage = (len(df) / total_rows * 100) if total_rows > 0 else 0
                    st.metric("Coverage", f"{coverage:.1f}%")
                
                st.markdown("**Select columns to display:**")
                col_disp1, col_disp2 = st.columns([3, 1])
                
                with col_disp1:
                    selected_columns = st.multiselect(
                        "Choose columns:",
                        options=df.columns.tolist(),
                        default=df.columns.tolist(),
                        help="Select which columns to display"
                    )
                with col_disp2:
                    st.markdown("**Quick Actions:**")
                    if st.button("✅ Select All Columns", use_container_width=True):
                        st.session_state.selected_columns = df.columns.tolist()
                        st.rerun()
                
                if selected_columns:
                    display_df = df[selected_columns]
                    st.dataframe(display_df, use_container_width=True, height=500)
                    
                    st.markdown("---")
                    st.subheader("📥 Download Data")
                    
                    col_dl1, col_dl2, col_dl3 = st.columns(3)
                    with col_dl1:
                        excel_bytes = generate_excel_bytes(display_df)
                        st.download_button(
                            label=f"📊 Download Current View ({len(display_df):,} rows)",
                            data=excel_bytes,
                            file_name=f"{selected_table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            type="primary"
                        )
                    with col_dl2:
                        csv_bytes = display_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label=f"📄 Download CSV ({len(display_df):,} rows)",
                            data=csv_bytes,
                            file_name=f"{selected_table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    with col_dl3:
                        if st.button("📦 Download Entire Table", use_container_width=True):
                            with st.spinner(f"Downloading entire table ({total_rows:,} rows)..."):
                                try:
                                    cursor.execute(f"SELECT * FROM `{selected_table}`")
                                    all_rows = cursor.fetchall()
                                    full_df = pd.DataFrame(all_rows, columns=column_names)
                                    excel_bytes = generate_excel_bytes(full_df)
                                    
                                    st.download_button(
                                        label=f"⬇️ Download Full Table ({len(full_df):,} rows)",
                                        data=excel_bytes,
                                        file_name=f"{selected_table}_FULL_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        use_container_width=True,
                                        type="primary",
                                        key="download_full_table"
                                    )
                                except Error as e:
                                    st.error(f"❌ Error downloading full table: {str(e)}")
                    
                    with st.expander("📊 Column Statistics", expanded=False):
                        st.markdown("**Data types and unique values:**")
                        stats_data = [{
                            'Column': col,
                            'Data Type': str(display_df[col].dtype),
                            'Unique Values': display_df[col].nunique(),
                            'Null Values': display_df[col].isnull().sum(),
                            'Non-Null': len(display_df) - display_df[col].isnull().sum()
                        } for col in selected_columns]
                        
                        st.dataframe(pd.DataFrame(stats_data), use_container_width=True, hide_index=True)
                else:
                    st.warning("⚠️ Please select at least one column to display")
    
        cursor.close()
        connection.close()
        
    except Error as e:
        st.error(f"❌ Database Error: {str(e)}")
        st.session_state.db_connected = False
    except Exception as e:
        st.error(f"❌ Application Error: {str(e)}")
        st.exception(e)

    st.markdown("---")
    with st.expander("ℹ️ Instructions & Features"):
        st.markdown("""
        ### Features:
        - **Table Browser**: View all tables with row counts and details.
        - **Table Structure**: See column types and properties.
        - **Modify Data Types**: Easily change column types for better performance, with bulk conversions.
        - **Search & Sort**: Fully functional text search across all columns or specific columns.
        - **Pagination**: Navigate large tables without lag.
        - **Statistics & Downloads**: Explore data structures and export easily.
        """)
    st.markdown("---")
    st.caption("🗄️ MySQL Database Viewer | Browse and download data from MySQL tables")
