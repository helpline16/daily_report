"""
ACK Bank Consolidator Module.

Groups rows by Acknowledgement Number + Bank Name, sums transaction amounts.
Example: ACK 123 with 4 SBI, 5 HDFC, 1 ICICI entries → 3 rows with summed amounts.

Supports multiple file uploads.
"""

import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import json
from pathlib import Path

# ---------- Persistent mapping ----------
_MAPPING_FILE = Path.home() / '.kiro' / 'ack_bank_consolidator_mappings.json'

def _load_mappings() -> dict:
    try:
        if _MAPPING_FILE.exists():
            return json.loads(_MAPPING_FILE.read_text(encoding='utf-8'))
    except Exception:
        pass
    return {}

def _save_mappings(data: dict):
    try:
        _MAPPING_FILE.parent.mkdir(parents=True, exist_ok=True)
        _MAPPING_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    except Exception:
        pass

def _get_saved_index(key: str, options: list, saved: dict) -> int:
    v = saved.get(key)
    if v and v in options:
        return options.index(v)
    return 0

def _generate_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Consolidated Data')
    return output.getvalue()

def _read_single_file(uploaded_file) -> pd.DataFrame:
    b = uploaded_file.getvalue()
    if uploaded_file.name.endswith('.csv'):
        return pd.read_csv(BytesIO(b), dtype=str)
    else:
        return pd.read_excel(BytesIO(b), dtype=str, engine='openpyxl')

def _compute_files_hash(files) -> str:
    parts = sorted(f"{f.name}_{f.size}" for f in files)
    return "|".join(parts)

def _load_multiple_files(files, label: str) -> pd.DataFrame:
    all_dfs = []
    total = len(files)

    if total == 1:
        with st.spinner(f"⏳ Loading {label}..."):
            df = _read_single_file(files[0])
            st.success(f"✅ {files[0].name}: {len(df):,} records")
            return df

    progress = st.progress(0, text=f"Loading {label} (0/{total})...")
    for idx, f in enumerate(files):
        progress.progress((idx) / total, text=f"Loading {label} ({idx+1}/{total}): {f.name}...")
        df = _read_single_file(f)
        all_dfs.append(df)

    progress.progress(100, text=f"Combining {total} files...")
    combined = pd.concat(all_dfs, ignore_index=True)
    progress.empty()

    with st.expander(f"📋 {total} files combined ({len(combined):,} total records)", expanded=False):
        breakdown = pd.DataFrame([
            {'#': i+1, 'Filename': f.name, 'Records': len(d)}
            for i, (f, d) in enumerate(zip(files, all_dfs))
        ])
        st.dataframe(breakdown, use_container_width=True, hide_index=True)

    return combined


# ---------- Main page ----------

def render_ack_bank_consolidator_page():
    st.title("📊 ACK + Bank Consolidator")
    st.markdown("""
    **Consolidate multiple rows into one per ACK Number + Bank Name.**
    
    **Example:** If ACK `123` has 4 SBI entries, 5 HDFC entries, and 1 ICICI entry (10 rows total),  
    this page will output **3 rows** — one per bank — with the **Transaction Amount summed** for each group.
    
    You can also choose **extra columns to keep** (first value from each group will be used).
    
    Supports **multiple file uploads** (Ctrl+Click).
    """)

    # Load saved mappings
    if 'ack_consol_saved' not in st.session_state:
        st.session_state.ack_consol_saved = _load_mappings()
    saved = st.session_state.ack_consol_saved

    saved_count = sum(1 for v in saved.values() if v)
    if saved_count > 0:
        st.success(f"✅ {saved_count} column mapping(s) remembered from previous session")

    # Init session state 
    for k in ['ack_consol_df', 'ack_consol_result_df']:
        if k not in st.session_state:
            st.session_state[k] = None

    st.markdown("---")
    st.header("📁 Step 1: Upload File(s)")
    st.caption("Ctrl+Click to select multiple files. All will be combined automatically.")

    files = st.file_uploader(
        "Upload Excel/CSV file(s)",
        type=['xlsx', 'xls', 'csv'],
        key='ack_consol_files',
        accept_multiple_files=True,
        help="Upload up to 50 files. They will be combined into one dataset."
    )

    if files:
        if len(files) > 50:
            st.error("❌ Maximum 50 files allowed.")
        else:
            fhash = _compute_files_hash(files)
            if st.session_state.get('_ack_consol_hash') != fhash:
                st.session_state.ack_consol_df = _load_multiple_files(files, "data")
                st.session_state['_ack_consol_hash'] = fhash
                # Clear old results when new files loaded
                st.session_state.ack_consol_result_df = None

            if st.session_state.ack_consol_df is not None:
                st.success(f"✅ {len(st.session_state.ack_consol_df):,} total records loaded")

    # ---------- Step 2: Column selection ----------
    if st.session_state.ack_consol_df is not None:
        st.markdown("---")
        st.header("🔧 Step 2: Select Columns")

        df = st.session_state.ack_consol_df
        all_cols = ["-- Select Column --"] + list(df.columns)

        c1, c2 = st.columns(2)

        with c1:
            ack_col = st.selectbox(
                "📋 Acknowledgement Number column",
                options=all_cols,
                index=_get_saved_index('ack_col', all_cols, saved),
                key='ack_consol_ack',
                help="Rows with the same ACK number will be grouped together"
            )
            bank_col = st.selectbox(
                "🏦 Bank Name column",
                options=all_cols,
                index=_get_saved_index('bank_col', all_cols, saved),
                key='ack_consol_bank',
                help="Within each ACK group, rows will be further grouped by bank"
            )

        with c2:
            amt_col = st.selectbox(
                "💰 Transaction Amount column",
                options=all_cols,
                index=_get_saved_index('amt_col', all_cols, saved),
                key='ack_consol_amt',
                help="This column will be SUMMED for each ACK+Bank group"
            )

        # Extra columns to keep
        st.markdown("##### 📌 Extra columns to keep (optional)")
        st.caption("Select any additional columns you want in the output. For each group, the first non-empty value will be used.")

        # Filter out already-selected columns for the multiselect
        remaining_cols = [c for c in df.columns if c not in [
            ack_col if ack_col != "-- Select Column --" else "",
            bank_col if bank_col != "-- Select Column --" else "",
            amt_col if amt_col != "-- Select Column --" else "",
        ]]
        
        # Restore saved extra columns
        saved_extra = saved.get('extra_cols', [])
        default_extra = [c for c in saved_extra if c in remaining_cols]
        
        extra_cols = st.multiselect(
            "Additional columns to include",
            options=remaining_cols,
            default=default_extra,
            key='ack_consol_extra',
            help="These columns will show the first non-empty value from each group"
        )

        # Batch save mappings  
        new_map = {
            'ack_col': ack_col if ack_col != "-- Select Column --" else None,
            'bank_col': bank_col if bank_col != "-- Select Column --" else None,
            'amt_col': amt_col if amt_col != "-- Select Column --" else None,
            'extra_cols': extra_cols,
        }
        if new_map != saved:
            st.session_state.ack_consol_saved = new_map
            _save_mappings(new_map)

        all_sel = "-- Select Column --" not in [ack_col, bank_col, amt_col]

        # ---------- Step 3: Consolidate ----------
        st.markdown("---")
        st.header("🔄 Step 3: Consolidate")
        if st.button("📊 Consolidate Rows", type="primary", use_container_width=True, disabled=not all_sel):
            with st.spinner("⚡ Consolidating..."):
                try:
                    work_df = df.copy()
                    progress = st.progress(0, text="Preparing data...")

                    # Convert amount to numeric
                    work_df['_amt_numeric'] = (
                        work_df[amt_col]
                        .fillna('0')
                        .astype(str)
                        .str.replace('₹', '', regex=False)
                        .str.replace('Rs', '', regex=False)
                        .str.replace('Rs.', '', regex=False)
                        .str.replace('INR', '', regex=False)
                        .str.replace('USD', '', regex=False)
                        .str.replace('$', '', regex=False)
                        .str.replace(',', '', regex=False)
                        .str.replace(' ', '', regex=False)
                    )
                    work_df['_amt_numeric'] = pd.to_numeric(work_df['_amt_numeric'], errors='coerce').fillna(0)

                    progress.progress(30, text="Grouping by ACK + Bank...")

                    # Build aggregation: sum for amount, 'first' for extras, size for count
                    agg_dict = {amt_col: ('_amt_numeric', 'sum'), '_count': ('_amt_numeric', 'size')}
                    for ec in extra_cols:
                        agg_dict[ec] = (ec, 'first')

                    result_df = work_df.groupby([ack_col, bank_col], sort=False, dropna=False).agg(**agg_dict).reset_index()

                    progress.progress(70, text="Formatting output...")

                    # Round amount
                    result_df[amt_col] = result_df[amt_col].round(2)

                    # Rename count column
                    result_df = result_df.rename(columns={'_count': 'Entry Count'})

                    # Reorder: ack, bank, amount, count, extras
                    output_cols = [ack_col, bank_col, amt_col, 'Entry Count'] + extra_cols
                    result_df = result_df[output_cols]

                    st.session_state.ack_consol_result_df = result_df

                    # Pre-generate Excel
                    progress.progress(90, text="Generating Excel...")
                    st.session_state.ack_consol_excel_bytes = _generate_excel_bytes(result_df)
                    st.session_state.ack_consol_orig_count = len(df)
                    st.session_state.ack_consol_new_count = len(result_df)

                    progress.progress(100, text="Done!")

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.exception(e)

        # ---------- Step 4: Results ----------
        if st.session_state.ack_consol_result_df is not None:
            st.markdown("---")
            st.header("📋 Step 4: Results")

            orig_count = st.session_state.get('ack_consol_orig_count', 0)
            new_count = st.session_state.get('ack_consol_new_count', 0)
            reduction = orig_count - new_count

            st.success("✅ Consolidation complete!")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Original Rows", f"{orig_count:,}")
            m2.metric("Consolidated Rows", f"{new_count:,}")
            m3.metric("Rows Reduced", f"{reduction:,}")
            m4.metric("Reduction %", f"{(reduction/max(orig_count,1)*100):.1f}%")

            df_res = st.session_state.ack_consol_result_df
            with st.expander("Preview Results (First 200)", expanded=True):
                st.dataframe(df_res.head(200), use_container_width=True)

            st.subheader("📥 Download Results")
            st.download_button(
                "📊 Download Consolidated Excel",
                data=st.session_state.ack_consol_excel_bytes,
                file_name=f"ACK_Bank_Consolidated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True, type="primary"
            )

            st.markdown("---")
            if st.button("🔄 Clear & Start Over", use_container_width=True):
                for k in list(st.session_state.keys()):
                    if k.startswith('ack_consol_') or k.startswith('_ack_consol_'):
                        del st.session_state[k]
                st.rerun()
