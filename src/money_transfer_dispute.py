"""
Money Transfer Dispute Matcher Module.

Match records from Money Transfer files to Layerwise files based on 3 parameters:
1. Acknowledgement Number
2. Account Number (matching from the right, ignoring text/zeros)
3. Amount

Supports multiple file uploads for both sides. Combines all files then matches.
Adds Disputed Amount from Layerwise to Money Transfer file.
"""

import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import re
import json
from pathlib import Path

# ---------- Persistent mapping ----------
_MAPPING_FILE = Path.home() / '.kiro' / 'money_transfer_dispute_mappings.json'

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

# ---------- Normalization helpers (vectorized) ----------

_CURRENCY_RE = re.compile(r'[₹$]|Rs\.?|INR|USD')
_NON_NUM_RE = re.compile(r'[^\d.\-]')
_NON_DIGIT_RE = re.compile(r'\D')

def _vec_normalize_ack(series: pd.Series) -> pd.Series:
    s = series.fillna('').astype(str).str.strip()
    s = s.where(~s.str.endswith('.0'), s.str[:-2])
    s = s.str.strip().str.upper()
    s = s.where(~s.isin(['NAN', 'NONE', '']), '')
    return s

def _vec_normalize_acc(series: pd.Series) -> pd.Series:
    s = series.fillna('').astype(str).str.strip()
    s = s.where(~s.str.endswith('.0'), s.str[:-2])
    s = s.str.replace(_NON_DIGIT_RE, '', regex=True)
    return s

def _vec_normalize_amt(series: pd.Series) -> pd.Series:
    s = series.fillna('').astype(str).str.strip()
    s = s.where(~s.isin(['NAN', 'NONE', '']), '')
    s = s.str.replace(_CURRENCY_RE, '', regex=True)
    s = s.str.replace(',', '', regex=False).str.replace(' ', '', regex=False)
    s = s.str.replace(_NON_NUM_RE, '', regex=True)
    numeric = pd.to_numeric(s, errors='coerce')
    result = numeric.round(2).astype(str)
    result = result.where(numeric.notna(), '')
    result = result.str.replace(r'\.0$', '.0', regex=True)
    return result

def _generate_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Matched Data')
    return output.getvalue()


def _read_single_file(uploaded_file) -> pd.DataFrame:
    """Read a single uploaded file (Excel or CSV) into a DataFrame."""
    b = uploaded_file.getvalue()
    if uploaded_file.name.endswith('.csv'):
        return pd.read_csv(BytesIO(b), dtype=str)
    else:
        return pd.read_excel(BytesIO(b), dtype=str, engine='openpyxl')


def _compute_files_hash(files) -> str:
    """Create a lightweight hash from file names + sizes to detect changes."""
    parts = sorted(f"{f.name}_{f.size}" for f in files)
    return "|".join(parts)


def _load_multiple_files(files, label: str) -> pd.DataFrame:
    """Read and combine multiple uploaded files with a progress bar."""
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

    # Show breakdown
    with st.expander(f"📋 {total} files combined ({len(combined):,} total records)", expanded=False):
        breakdown = pd.DataFrame([
            {'#': i+1, 'Filename': f.name, 'Records': len(d)}
            for i, (f, d) in enumerate(zip(files, all_dfs))
        ])
        st.dataframe(breakdown, use_container_width=True, hide_index=True)

    return combined


# ---------- Main page ----------

def render_money_transfer_dispute_page():
    st.title("💸 Money Transfer Dispute Matcher")
    st.markdown("""
    Match records between **Money Transfer** and **Layerwise** files based on **3 parameters**:
    1. **Acknowledgement Number**
    2. **Account Number** (Matches from last digits, ignores text like 'Nodal Account')
    3. **Amount**
    
    Supports **multiple file uploads** on both sides (Ctrl+Click). All files are combined automatically.
    """)

    # Load saved mappings ONCE
    if 'mt_disp_saved' not in st.session_state:
        st.session_state.mt_disp_saved = _load_mappings()
    saved = st.session_state.mt_disp_saved

    saved_count = sum(1 for v in saved.values() if v)
    if saved_count > 0:
        st.success(f"✅ {saved_count} column mapping(s) remembered from previous session")

    # Init session state
    for k in ['mt_disp_f1_df', 'mt_disp_f2_df', 'mt_disp_result_df']:
        if k not in st.session_state:
            st.session_state[k] = None

    st.markdown("---")
    st.header("📁 Step 1: Upload Files")

    col1, col2 = st.columns(2)

    # -------- File 1: Money Transfer (multiple) --------
    with col1:
        st.subheader("Money Transfer Files")
        st.caption("Main files — Disputed Amount will be added here. Ctrl+Click for multiple.")
        files1 = st.file_uploader(
            "Upload Money Transfer file(s)",
            type=['xlsx', 'xls', 'csv'],
            key='mt_disp_f1',
            accept_multiple_files=True,
            help="Upload up to 50 Money Transfer files. They will be combined automatically."
        )
        if files1:
            if len(files1) > 50:
                st.error("❌ Maximum 50 files allowed.")
            else:
                fhash = _compute_files_hash(files1)
                if st.session_state.get('_mt_f1_hash') != fhash:
                    st.session_state.mt_disp_f1_df = _load_multiple_files(files1, "Money Transfer")
                    st.session_state['_mt_f1_hash'] = fhash
                if st.session_state.mt_disp_f1_df is not None:
                    st.success(f"✅ {len(st.session_state.mt_disp_f1_df):,} total Money Transfer records")

    # -------- File 2: Layerwise (multiple) --------
    with col2:
        st.subheader("Layerwise Files")
        st.caption("Contains Disputed Amount to be matched. Ctrl+Click for multiple.")
        files2 = st.file_uploader(
            "Upload Layerwise file(s)",
            type=['xlsx', 'xls', 'csv'],
            key='mt_disp_f2',
            accept_multiple_files=True,
            help="Upload up to 50 Layerwise files. They will be combined automatically."
        )
        if files2:
            if len(files2) > 50:
                st.error("❌ Maximum 50 files allowed.")
            else:
                fhash = _compute_files_hash(files2)
                if st.session_state.get('_mt_f2_hash') != fhash:
                    st.session_state.mt_disp_f2_df = _load_multiple_files(files2, "Layerwise")
                    st.session_state['_mt_f2_hash'] = fhash
                if st.session_state.mt_disp_f2_df is not None:
                    st.success(f"✅ {len(st.session_state.mt_disp_f2_df):,} total Layerwise records")

    # ---------- Step 2: Column mapping ----------
    if st.session_state.mt_disp_f1_df is not None and st.session_state.mt_disp_f2_df is not None:
        st.markdown("---")
        st.header("🔧 Step 2: Select Columns for Matching")

        f1_cols = ["-- Select Column --"] + list(st.session_state.mt_disp_f1_df.columns)
        f2_cols = ["-- Select Column --"] + list(st.session_state.mt_disp_f2_df.columns)

        c1, c2 = st.columns(2)

        with c1:
            st.subheader("From Money Transfer:")
            f1_ack = st.selectbox("Acknowledgement No", options=f1_cols, index=_get_saved_index('f1_ack', f1_cols, saved), key='mt_sel_f1_ack')
            f1_acc = st.selectbox("Account No", options=f1_cols, index=_get_saved_index('f1_acc', f1_cols, saved), key='mt_sel_f1_acc')
            f1_amt = st.selectbox("Transaction Amount", options=f1_cols, index=_get_saved_index('f1_amt', f1_cols, saved), key='mt_sel_f1_amt')

        with c2:
            st.subheader("From Layerwise:")
            f2_ack = st.selectbox("Acknowledgement No", options=f2_cols, index=_get_saved_index('f2_ack', f2_cols, saved), key='mt_sel_f2_ack')
            f2_acc = st.selectbox("Account No", options=f2_cols, index=_get_saved_index('f2_acc', f2_cols, saved), key='mt_sel_f2_acc')
            f2_amt = st.selectbox("Transaction Amount", options=f2_cols, index=_get_saved_index('f2_amt', f2_cols, saved), key='mt_sel_f2_amt')
            f2_disp = st.selectbox("Disputed Amount", options=f2_cols, index=_get_saved_index('f2_disp', f2_cols, saved), key='mt_sel_f2_disp')

        # Batch save mappings
        new_map = {
            'f1_ack': f1_ack if f1_ack != "-- Select Column --" else None,
            'f1_acc': f1_acc if f1_acc != "-- Select Column --" else None,
            'f1_amt': f1_amt if f1_amt != "-- Select Column --" else None,
            'f2_ack': f2_ack if f2_ack != "-- Select Column --" else None,
            'f2_acc': f2_acc if f2_acc != "-- Select Column --" else None,
            'f2_amt': f2_amt if f2_amt != "-- Select Column --" else None,
            'f2_disp': f2_disp if f2_disp != "-- Select Column --" else None,
        }
        if new_map != saved:
            st.session_state.mt_disp_saved = new_map
            _save_mappings(new_map)

        all_sel = "-- Select Column --" not in [f1_ack, f1_acc, f1_amt, f2_ack, f2_acc, f2_amt, f2_disp]

        # ---------- Step 3: Match ----------
        st.markdown("---")
        st.header("🔄 Step 3: Match Records")
        if st.button("💰 Match & Add Disputed Amount", type="primary", use_container_width=True, disabled=not all_sel):
            with st.spinner("⚡ Matching records..."):
                try:
                    df1 = st.session_state.mt_disp_f1_df.copy()
                    df2 = st.session_state.mt_disp_f2_df.copy()

                    progress = st.progress(0, text="Normalizing Money Transfer data...")

                    # Vectorized normalization
                    df1['_ack'] = _vec_normalize_ack(df1[f1_ack])
                    df1['_amt'] = _vec_normalize_amt(df1[f1_amt])
                    df1['_acc'] = _vec_normalize_acc(df1[f1_acc])
                    progress.progress(20, text="Normalizing Layerwise data...")

                    df2['_ack'] = _vec_normalize_ack(df2[f2_ack])
                    df2['_amt'] = _vec_normalize_amt(df2[f2_amt])
                    df2['_acc'] = _vec_normalize_acc(df2[f2_acc])
                    progress.progress(40, text="Building lookup index...")

                    # Build dict: (ack, amt) -> list of (acc_digits, disputed_amount)
                    lookup = {}
                    for row_acc, row_ack, row_amt, row_disp in zip(
                        df2['_acc'].values, df2['_ack'].values, df2['_amt'].values, df2[f2_disp].values
                    ):
                        if row_ack and row_amt:
                            key = (row_ack, row_amt)
                            if key not in lookup:
                                lookup[key] = []
                            lookup[key].append((row_acc, row_disp))

                    progress.progress(60, text="Matching account numbers...")

                    acks = df1['_ack'].values
                    amts = df1['_amt'].values
                    accs = df1['_acc'].values
                    n = len(df1)

                    results = [''] * n
                    matched_count = 0

                    for i in range(n):
                        a_ack = acks[i]
                        a_amt = amts[i]
                        a_acc = accs[i]

                        if not a_ack or not a_amt:
                            continue

                        candidates = lookup.get((a_ack, a_amt))
                        if candidates is None:
                            continue

                        for c_acc, c_disp in candidates:
                            if a_acc and c_acc:
                                if a_acc.endswith(c_acc) or c_acc.endswith(a_acc):
                                    results[i] = c_disp if not pd.isna(c_disp) else ''
                                    matched_count += 1
                                    break

                    progress.progress(85, text="Building output...")

                    df1['DISPUTED AMOUNT'] = results

                    # Drop temp columns
                    df1.drop(columns=['_ack', '_amt', '_acc'], inplace=True)

                    # Insert DISPUTED AMOUNT right after amount column
                    cols = list(df1.columns)
                    cols.remove('DISPUTED AMOUNT')
                    insert_idx = cols.index(f1_amt) + 1
                    cols.insert(insert_idx, 'DISPUTED AMOUNT')

                    result_df = df1[cols]
                    st.session_state.mt_disp_result_df = result_df

                    # Pre-generate download
                    progress.progress(95, text="Generating Excel download...")
                    st.session_state.mt_disp_excel_bytes = _generate_excel_bytes(result_df)
                    st.session_state.mt_disp_matched_count = matched_count
                    st.session_state.mt_disp_total_count = n

                    progress.progress(100, text="Done!")

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.exception(e)

        # ---------- Step 4: Results ----------
        if st.session_state.mt_disp_result_df is not None:
            st.markdown("---")
            st.header("📋 Step 4: Results")

            matched_count = st.session_state.get('mt_disp_matched_count', 0)
            total_count = st.session_state.get('mt_disp_total_count', 0)

            st.success("✅ Matching complete!")
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Records", f"{total_count:,}")
            m2.metric("Matched", f"{matched_count:,}")
            m3.metric("Unmatched", f"{total_count - matched_count:,}")

            df_res = st.session_state.mt_disp_result_df
            with st.expander("Preview Results (First 100)", expanded=True):
                st.dataframe(df_res.head(100), use_container_width=True)

            st.subheader("📥 Download Results")
            st.download_button(
                "📊 Download Merged Excel",
                data=st.session_state.mt_disp_excel_bytes,
                file_name=f"MT_Disputed_Match_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True, type="primary"
            )

            st.markdown("---")
            if st.button("🔄 Clear & Start Over", use_container_width=True):
                for k in list(st.session_state.keys()):
                    if k.startswith('mt_disp_') or k.startswith('_mt_f'):
                        del st.session_state[k]
                st.rerun()
