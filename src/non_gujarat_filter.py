import streamlit as st
import pandas as pd
import io
from datetime import datetime
from src.persistent_mapping import PersistentMapping


def render_non_gujarat_filter_page():
    """Render the Non-Gujarat Data Filter page - excludes all Gujarat state records."""
    
    # Initialize persistent mapping
    mapping = PersistentMapping('non_gujarat_filter')
    
    # Title and description
    st.title("🗺️ Non-Gujarat Data Filter")
    st.markdown("Upload an Excel file and get back only the records that are **NOT from Gujarat state**.")
    
    st.info("💡 This tool will filter out all records where the state/location is Gujarat, giving you only data from other states.")

    # File upload
    uploaded_file = st.file_uploader(
        "Choose an Excel file (.xlsx or .csv)",
        type=['xlsx', 'xls', 'csv'],
        help="Upload a file containing state/location information",
        key="non_gujarat_uploader"
    )

    if uploaded_file is not None:
        try:
            # Read the file
            with st.spinner("Reading file..."):
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
            
            st.success(f"✅ File uploaded successfully! Total records: {len(df):,}")
            
            # Show preview of data
            with st.expander("📋 Preview Original Data (First 10 rows)"):
                st.dataframe(df.head(10))
            
            # Manual column selection - PRIMARY METHOD
            st.markdown("### 🎯 Select State Column")
            st.info("👇 Please select the column that contains state information")
            
            # Show saved mappings indicator
            saved_count = mapping.get_saved_count()
            if saved_count > 0:
                st.success(f"✅ {saved_count} column mapping(s) remembered")
            
            state_col = st.selectbox(
                "Select the column containing state information:",
                options=["-- Select Column --"] + list(df.columns),
                index=mapping.get_default_index('state_col', ["-- Select Column --"] + list(df.columns)),
                key="manual_state_select",
                help="Choose the column that has state names (e.g., Gujarat, Maharashtra, Delhi, etc.)"
            )
            if state_col != "-- Select Column --":
                mapping.set('state_col', state_col)
            
            if state_col == "-- Select Column --":
                st.warning("⚠️ Please select a state column to proceed")
                return
            
            # Show unique states in the data
            with st.expander("📊 Unique States in Data"):
                unique_states = df[state_col].dropna().unique()
                st.write(f"Found {len(unique_states)} unique states:")
                
                # Create a dataframe showing state counts
                state_counts = df[state_col].value_counts().reset_index()
                state_counts.columns = ['State', 'Count']
                st.dataframe(state_counts, use_container_width=True)
            
            # Count Gujarat records
            gujarat_variations = ['gujarat', 'gujrat', 'guj', 'gujraat']
            
            # Create a mask for Gujarat records (case-insensitive)
            gujarat_mask = df[state_col].astype(str).str.lower().str.strip().isin(gujarat_variations)
            
            # Also check for partial matches
            for variation in gujarat_variations:
                gujarat_mask |= df[state_col].astype(str).str.lower().str.contains(variation, na=False)
            
            gujarat_count = gujarat_mask.sum()
            non_gujarat_count = len(df) - gujarat_count
            
            # Show statistics
            st.markdown("### 📊 Data Statistics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Records", f"{len(df):,}")
            with col2:
                st.metric("Gujarat Records", f"{gujarat_count:,}", delta=f"-{gujarat_count:,}", delta_color="inverse")
            with col3:
                st.metric("Non-Gujarat Records", f"{non_gujarat_count:,}", delta=f"+{non_gujarat_count:,}")
            
            if gujarat_count > 0:
                st.info(f"🔍 Found {gujarat_count:,} Gujarat records that will be excluded")
            else:
                st.warning("⚠️ No Gujarat records found in the data")
            
            if non_gujarat_count == 0:
                st.error("❌ All records are from Gujarat! No data to export.")
                return
            
            # Filter button
            st.markdown("---")
            
            if st.button("🔄 Filter Non-Gujarat Data", type="primary", use_container_width=True, key="filter_non_gujarat"):
                with st.spinner("Filtering data..."):
                    # Filter out Gujarat records
                    non_gujarat_df = df[~gujarat_mask].copy()
                    
                    # Reset index
                    non_gujarat_df.reset_index(drop=True, inplace=True)
                    
                    # Add Sr No column if not present
                    if 'Sr No' not in non_gujarat_df.columns:
                        non_gujarat_df.insert(0, 'Sr No', range(1, len(non_gujarat_df) + 1))
                    else:
                        # Update existing Sr No
                        non_gujarat_df['Sr No'] = range(1, len(non_gujarat_df) + 1)
                    
                    st.session_state.non_gujarat_filtered_df = non_gujarat_df
                    st.success(f"✅ Successfully filtered! {len(non_gujarat_df):,} non-Gujarat records ready for download")
            
            # Show filtered data and download options
            if 'non_gujarat_filtered_df' in st.session_state and st.session_state.non_gujarat_filtered_df is not None:
                filtered_df = st.session_state.non_gujarat_filtered_df
                
                st.markdown("---")
                st.markdown("### 📋 Filtered Data Preview")
                
                # Show preview
                with st.expander("👁️ View Filtered Data (First 20 rows)", expanded=True):
                    st.dataframe(filtered_df.head(20), use_container_width=True)
                
                # Show state distribution in filtered data
                with st.expander("📊 State Distribution (After Filtering)"):
                    filtered_state_counts = filtered_df[state_col].value_counts().reset_index()
                    filtered_state_counts.columns = ['State', 'Count']
                    st.dataframe(filtered_state_counts, use_container_width=True)
                
                st.markdown("---")
                st.markdown("### 📥 Download Filtered Data")
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Download options
                dl_col1, dl_col2, dl_col3 = st.columns(3)
                
                with dl_col1:
                    # Excel download
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        filtered_df.to_excel(writer, sheet_name='Non-Gujarat Data', index=False)
                        
                        # Auto-adjust column widths
                        worksheet = writer.sheets['Non-Gujarat Data']
                        for idx, col in enumerate(filtered_df.columns):
                            max_length = max(
                                filtered_df[col].astype(str).apply(len).max(),
                                len(str(col))
                            )
                            # Limit to 50 characters width
                            worksheet.column_dimensions[chr(65 + idx) if idx < 26 else f"A{chr(65 + idx - 26)}"].width = min(max_length + 2, 50)
                    
                    excel_data = excel_buffer.getvalue()
                    
                    st.download_button(
                        label=f"⬇️ Download Excel ({len(filtered_df):,} rows)",
                        data=excel_data,
                        file_name=f"non_gujarat_data_{timestamp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="download_excel_non_guj"
                    )
                
                with dl_col2:
                    # CSV download
                    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
                    
                    st.download_button(
                        label=f"⬇️ Download CSV ({len(filtered_df):,} rows)",
                        data=csv_data,
                        file_name=f"non_gujarat_data_{timestamp}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key="download_csv_non_guj"
                    )
                
                with dl_col3:
                    # Summary report
                    summary_text = f"""NON-GUJARAT DATA FILTER REPORT
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

ORIGINAL DATA:
- Total Records: {len(df):,}
- Gujarat Records: {gujarat_count:,}
- Non-Gujarat Records: {non_gujarat_count:,}

FILTERED DATA:
- Records Exported: {len(filtered_df):,}
- State Column Used: {state_col}

STATES INCLUDED:
{chr(10).join([f"- {row['State']}: {row['Count']:,} records" for _, row in filtered_state_counts.head(20).iterrows()])}

Note: All Gujarat state records have been excluded from this export.
"""
                    
                    st.download_button(
                        label="📄 Download Summary Report",
                        data=summary_text.encode('utf-8'),
                        file_name=f"non_gujarat_summary_{timestamp}.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key="download_summary_non_guj"
                    )
        
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.info("Please ensure the file is a valid Excel or CSV file with state information.")

    else:
        # Instructions when no file is uploaded
        st.info("👆 Please upload an Excel or CSV file to get started")
        
        with st.expander("ℹ️ Instructions"):
            st.markdown("""
            ### How to use this tool:
            
            1. **Upload** your Excel (.xlsx) or CSV file
            2. **Select** the column that contains state information
            3. Review the **statistics** to see Gujarat vs Non-Gujarat breakdown
            4. Click **Filter Non-Gujarat Data** to process
            5. **Download** the filtered data in your preferred format
            
            ### What gets filtered out:
            - All records where state = "Gujarat" (case-insensitive)
            - Variations like "Gujrat", "Guj", "Gujraat" are also excluded
            
            ### Features:
            - ✅ Manual column selection (you choose the state column)
            - ✅ Case-insensitive Gujarat filtering
            - ✅ Handles multiple Gujarat name variations
            - ✅ Preserves all original columns
            - ✅ Auto-adjusts Sr No after filtering
            - ✅ Multiple download formats (Excel, CSV, Summary)
            - ✅ Shows state distribution before and after filtering
            
            ### Use Cases:
            - Extract data for other states only
            - Separate Gujarat and non-Gujarat records
            - Generate reports excluding Gujarat transactions
            - Data analysis for non-Gujarat regions
            """)

    # Footer
    st.markdown("---")
    st.markdown("🗺️ Non-Gujarat Filter | Built with Streamlit")
