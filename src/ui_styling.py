"""
UI Styling and Theme Configuration for Fraud Analysis Tool
Hyper-Premium Midnight Theme with Ultra Smooth Animations
"""

import streamlit as st

# Color Scheme - Hyper-Premium Midnight Theme
COLORS = {
    # Primary - Midnight Slate & Neon
    'deep_ocean': '#060608',       # Dark midnight background
    'ocean_blue': '#0D0E15',       # Darker slate
    'water_blue': '#8B5CF6',       # Vibrant Neon Purple
    'sky_blue': '#00F5FF',         # Electric Cyan
    'light_aqua': '#D946EF',       # Neon Magenta
    'foam_white': '#FFFFFF',       # Bright white
    
    # Accent - Holographic
    'coral': '#EC4899',            # Pink
    'teal': '#10B981',             # Emerald green
    'mint': '#6EE7B7',             # Light Mint
    'seafoam': '#A78BFA',          # Soft bright indigo
    
    # Background
    'background': '#020203',       # Absolute black
    'background_card': 'rgba(15, 15, 20, 0.65)', # Sleek dark card
    'text_primary': '#F3F4F6',     # Off White
    'text_secondary': '#00F5FF',   # Cyan text
    'text_muted': '#9CA3AF',       # Gray text
    
    # Status colors
    'success': '#10B981',          # Emerald
    'warning': '#F59E0B',          # Amber
    'error': '#EF4444',            # Red
    'info': '#3B82F6',             # Blue
    
    # Glass effect
    'glass_bg': 'rgba(255, 255, 255, 0.03)',
    'glass_border': 'rgba(255, 255, 255, 0.08)',
    
    # Additional
    'border': '#1F2937',
    'hover': 'rgba(255, 150, 255, 0.5)',
    'shadow': 'rgba(0, 245, 255, 0.2)'
}

PAGE_INFO = {
    'upload': {
        'title': '📤 Upload Transaction Files',
        'description': 'Upload Excel or CSV files containing fraud transaction data.',
        'details': '''
        **What this page does:**
        - Accepts Excel (.xlsx, .xls) and CSV files
        - Supports uploading 1-50 files at once
        - Automatically combines multiple files
        '''
    },
    'mapping': {
        'title': '🔗 Column Mapping',
        'description': 'Map your file columns to required fields.',
        'details': '''
        **What this page does:**
        - Auto-detects column mappings
        - Allows manual column selection
        '''
    },
    'processing': {
        'title': '⚙️ Data Processing',
        'description': 'Process and validate uploaded data.',
        'details': '''
        **What this page does:**
        - Data cleaning and validation
        - Aggregation by account number
        '''
    },
    'results': {
        'title': '📊 Results Dashboard',
        'description': 'View processed results with statistics.',
        'details': '''
        **Features:**
        - Summary statistics
        - Search and filter
        - Download reports
        '''
    },
    'district_download': {
        'title': '📍 District Data Download',
        'description': 'Download data filtered by district.',
        'details': '''
        **What this page does:**
        - Filter by district
        - Download district-specific data
        '''
    },
    'districtwise': {
        'title': '📊 Split Data by Column',
        'description': 'Split your data into separate files based on column values.',
        'details': '''
        **What this page does:**
        - Split by any column
        - Create separate files or sheets
        '''
    },
    'smart_district_split': {
        'title': '🗺️ Smart District Split',
        'description': 'Intelligently split data by Gujarat districts.',
        'details': '''
        **What this page does:**
        - Maps talukas to districts
        - Handles spelling variations
        '''
    },
    'ifsc_pincode_split': {
        'title': '🏦 IFSC/PIN District Split',
        'description': '100% accurate district identification using IFSC and PIN codes.',
        'details': '''
        **What this page does:**
        - IFSC code lookup (real-time API)
        - PIN code mapping
        - 6-layer identification system
        '''
    },
    'filter_by_entry_count': {
        'title': '🔢 Filter by Entry Count',
        'description': 'Filter data to show only entries that appear a minimum number of times.',
        'details': '''
        **What this page does:**
        - Groups data by selected column
        - Filters by minimum entry count
        '''
    },
    'filter_by_unique_ack': {
        'title': '🏦 Filter Banks by Unique ACK',
        'description': 'Filter banks based on unique ACK count.',
        'details': '''
        **What this page does:**
        - Count unique ACKs per bank
        - Filter banks with minimum unique ACKs
        - Output all records including duplicates
        '''
    },
    'non_gujarat_filter': {
        'title': '🗺️ Non-Gujarat Filter',
        'description': 'Filter out Gujarat state data.',
        'details': '''
        **What this page does:**
        - Removes Gujarat entries
        - Keeps only Non-Gujarat states
        '''
    },
    'amount_matcher': {
        'title': '💰 Amount Matcher',
        'description': 'Match transactions by amount.',
        'details': '''
        **What this page does:**
        - Match records by amount
        - Find duplicate amounts
        '''
    },
    'bank_ack_pivot': {
        'title': '🏦 Bank ACK Pivot',
        'description': 'Create pivot table of banks and ACK numbers.',
        'details': '''
        **What this page does:**
        - Pivot by bank and ACK
        - Summary statistics
        '''
    },
    'ack_list_pivot': {
        'title': '📋 ACK List Pivot',
        'description': 'Create pivot table of ACK numbers.',
        'details': '''
        **What this page does:**
        - Pivot by ACK number
        - Detailed breakdown
        '''
    },
    'automated_workflow': {
        'title': '🔄 Automated Workflow',
        'description': 'Automated processing workflow.',
        'details': '''
        **What this page does:**
        - End-to-end automation
        - Batch processing
        '''
    },
    'column_selector': {
        'title': '📋 Column Selector',
        'description': 'Select and reorder columns.',
        'details': '''
        **What this page does:**
        - Choose columns to keep
        - Reorder columns
        '''
    },
    'excel_merger': {
        'title': '📎 Merge Excel Files',
        'description': 'Merge multiple Excel files into one.',
        'details': '''
        **What this page does:**
        - Combine multiple files
        - Preserve all data
        '''
    },
    'call_notice_merge': {
        'title': '📞 Call Notice Data Merge',
        'description': 'Merge call notice data.',
        'details': '''
        **What this page does:**
        - Merge call and notice data
        - Match by key fields
        '''
    },
    'transaction_matcher': {
        'title': '🔄 Transaction Matcher',
        'description': 'Match transactions by Transaction ID.',
        'details': '''
        **What this page does:**
        - Match by Transaction ID
        - Add account and date info
        '''
    },
    'disputed_amount_matcher': {
        'title': '💰 Disputed Amount Matcher',
        'description': 'Match disputed amounts.',
        'details': '''
        **What this page does:**
        - Match disputed amounts
        - Multi-parameter matching
        '''
    },
    'money_transfer_dispute': {
        'title': '💸 Money Transfer Dispute Matcher',
        'description': 'Add Disputed Amount to Money Transfer files.',
        'details': '''
        **What this page does:**
        - Match by Ack No, Account No, and Amount
        - Uses backward matching for account numbers
        '''
    },
    'ack_bank_consolidator': {
        'title': '📊 ACK + Bank Consolidator',
        'description': 'Consolidate rows by ACK Number + Bank Name.',
        'details': '''
        **What this page does:**
        - Groups rows by ACK Number + Bank Name
        - Sums transaction amounts per group
        - Reduces multiple entries to one per bank per ACK
        '''
    },
    'bulk_mysql_import': {
        'title': '📊 Bulk MySQL Import',
        'description': 'Import all Excel files from a folder into MySQL database.',
        'details': '''
        **What this page does:**
        - Scan folder for Excel files
        - Automatically create MySQL tables
        - Import all data in batches
        - Handle large files efficiently
        
        **Features:**
        - Batch import (1000 rows at a time)
        - Auto table name sanitization
        - Data type detection
        - Progress tracking
        - Error handling
        '''
    },
    'mysql_database_viewer': {
        'title': '🗄️ MySQL Database Viewer',
        'description': 'Browse, search, filter, and download data from MySQL tables.',
        'details': '''
        **What this page does:**
        - Connect to MySQL database
        - View all tables with row counts
        - Browse table data with pagination
        - Search and filter records
        - Download data in Excel/CSV
        
        **Features:**
        - Table browser with statistics
        - Search across all columns
        - Sort and filter data
        - Column selection
        - Download current view or entire table
        - Data statistics and insights
        '''
    },
    'ai_sql_assistant': {
        'title': '🤖 AI SQL Assistant',
        'description': 'Ask questions in natural language and get SQL queries automatically.',
        'details': '''
        **What this page does:**
        - Convert natural language to SQL
        - Auto-generate queries from questions
        - Execute queries and show results
        - Download query results
        
        **Features:**
        - Natural language processing
        - Supports counting, aggregation, searching
        - Query editing and history
        - Quick question buttons
        - Excel/CSV export
        - No SQL knowledge required
        '''
    },
    'report_generator': {
        'title': '📊 Account & Hold Amount Report Generator',
        'description': 'Generate professional reports with Account, Hold Amount, and Unattended data',
        'details': '''
        **Report Generator Features:**
        - Three comprehensive sheets in one Excel file
        - PUT ON HOLD: Bank-wise hold amounts with grand total
        - ACCOUNT: Bank-wise account count (distinct ACK numbers)
        - Complaint Un Attended: Bank/Wallet/Merchant-wise unattended complaints
        
        **Professional Formatting:**
        - Sky blue title rows
        - Light yellow headers
        - Table format with borders
        - Grand total rows in bold with sky blue background
        
        **Data Processing:**
        - Automatic bank name filtering
        - Removal of "other/others/othar" entries
        - Zero value filtering
        - Distinct count calculations
        - Bank-wise aggregations
        '''
    }
}

def apply_custom_css():
    """Apply custom CSS styling to the Streamlit app - Hyper-Premium Midnight Theme"""
    st.markdown(f"""
    <style>
    /* Import Modern Fonts - Ultra Premium Typography */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@200;300;400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap');
    
    /* Global Styles */
    * {{
        font-family: 'Outfit', sans-serif;
        scroll-behavior: smooth !important;
    }}
    
    /* Remove White Gap at Top */
    header[data-testid="stHeader"] {{
        background: transparent !important;
        height: 0px !important;
        padding: 0 !important;
    }}
    
    /* Ensure no white spots appear */
    .stApp > header {{
        background-color: transparent !important;
    }}
    
    [data-testid="stAppViewContainer"] {{
        background-color: transparent !important;
    }}
    
    /* Main Background - Liquid Dark Gradient */
    .stApp {{
        background: radial-gradient(circle at 50% 10%, {COLORS['ocean_blue']} 0%, {COLORS['deep_ocean']} 60%, {COLORS['background']} 100%) !important;
        background-attachment: fixed !important;
        color: {COLORS['text_primary']};
    }}
    
    /* Main Container Glass Scrolling Effect - Like sliding on glass */
    [data-testid="stAppViewBlockContainer"] {{
        background: rgba(10, 10, 14, 0.5) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(0, 245, 255, 0.15) !important;
        border-radius: 24px !important;
        padding: 3rem !important;
        margin-top: 3rem !important;
        margin-bottom: 3rem !important;
        box-shadow: 0 25px 50px rgba(0,0,0,0.6), inset 0 2px 0 rgba(255,255,255,0.1) !important;
        max-width: 95% !important;
        transition: all 0.4s ease;
    }}
    
    /* Smooth Scrollbar for entire app */
    ::-webkit-scrollbar {{
        width: 10px;
        height: 10px;
    }}
    ::-webkit-scrollbar-track {{
        background: {COLORS['background']};
        border-radius: 8px;
    }}
    ::-webkit-scrollbar-thumb {{
        background: linear-gradient(180deg, {COLORS['sky_blue']} 0%, {COLORS['water_blue']} 100%);
        border-radius: 8px;
        border: 2px solid {COLORS['background']};
        transition: background 0.5s cubic-bezier(0.2, 0.8, 0.2, 1);
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: linear-gradient(180deg, {COLORS['teal']} 0%, {COLORS['seafoam']} 100%);
        box-shadow: 0 0 15px {COLORS['teal']};
    }}
    
    /* Liquid Glow Animation */
    @keyframes liquidGlow {{
        0% {{ box-shadow: 0 0 10px rgba(0, 245, 255, 0.2), inset 0 0 15px rgba(0, 245, 255, 0.1); }}
        50% {{ box-shadow: 0 0 25px rgba(0, 245, 255, 0.5), inset 0 0 20px rgba(0, 245, 255, 0.3); }}
        100% {{ box-shadow: 0 0 10px rgba(0, 245, 255, 0.2), inset 0 0 15px rgba(0, 245, 255, 0.1); }}
    }}
    
    @keyframes floatingDrops {{
        0% {{ transform: translateY(0px) scale(1); opacity: 0.1; }}
        50% {{ transform: translateY(-30px) scale(1.1); opacity: 0.3; }}
        100% {{ transform: translateY(0px) scale(1); opacity: 0.1; }}
    }}
    
    /* Sidebar - Glass Container */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, rgba(4, 4, 6, 0.95) 0%, rgba(10, 10, 14, 0.98) 100%) !important;
        backdrop-filter: blur(30px) saturate(200%) !important;
        -webkit-backdrop-filter: blur(30px) saturate(200%) !important;
        border-right: 2px solid rgba(0, 245, 255, 0.5) !important;
        box-shadow: 10px 0 40px rgba(0, 0, 0, 0.8), 2px 0 15px rgba(0, 245, 255, 0.2) !important;
        position: relative;
        overflow: hidden;
    }}
    
    /* Adding the sliding glass look to sidebar header */
    [data-testid="stSidebarNav"] {{
        background: transparent !important;
    }}
    
    [data-testid="stSidebar"]::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(circle at 10% 20%, {COLORS['seafoam']} 0%, transparent 8%),
            radial-gradient(circle at 80% 60%, {COLORS['sky_blue']} 0%, transparent 5%),
            radial-gradient(circle at 40% 90%, {COLORS['teal']} 0%, transparent 6%);
        filter: blur(20px);
        opacity: 0.2;
        animation: floatingDrops 12s infinite alternate ease-in-out;
        pointer-events: none;
        z-index: 0;
    }}
    
    [data-testid="stSidebar"] > div {{ position: relative; z-index: 1; }}
    
    /* Sidebar Navigation Buttons - Holographic Water Effect */
    [data-testid="stSidebar"] .stButton button {{
        background: padding-box linear-gradient(rgba(22, 22, 26, 0.4), rgba(22, 22, 26, 0.4)),
                    border-box linear-gradient(135deg, {COLORS['glass_border']}, transparent, {COLORS['glass_border']});
        color: {COLORS['light_aqua']};
        border: 1px solid transparent;
        border-radius: 12px;
        font-weight: 500;
        font-size: 0.95rem;
        padding: 14px 22px;
        transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        backdrop-filter: blur(10px);
        box-shadow: inset 0 0 10px rgba(0, 245, 255, 0.05);
        position: relative;
        overflow: hidden;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    /* Liquid Hover Ripple Effect */
    [data-testid="stSidebar"] .stButton button::before {{
        content: '';
        position: absolute;
        bottom: 0; left: 0; right: 0;
        height: 0%;
        background: linear-gradient(180deg, rgba(0, 245, 255, 0), rgba(0, 245, 255, 0.4));
        transition: height 0.4s ease-out;
        z-index: 0;
        border-radius: 10px;
    }}
    
    [data-testid="stSidebar"] .stButton button:hover::before {{ height: 100%; }}
    
    [data-testid="stSidebar"] .stButton button:hover {{
        color: {COLORS['deep_ocean']};
        background: linear-gradient(135deg, {COLORS['sky_blue']} 0%, {COLORS['teal']} 100%);
        border-color: {COLORS['seafoam']};
        transform: translateY(-3px) scale(1.02);
        box-shadow: 
            0 10px 25px rgba(0, 245, 255, 0.4),
            0 0 15px rgba(0, 255, 170, 0.5),
            inset 0 0 5px rgba(255, 255, 255, 0.8);
        font-weight: 600;
        text-shadow: none;
    }}
    
    [data-testid="stSidebar"] .stButton button:active {{
        transform: translateY(1px) scale(0.98);
        box-shadow: 0 2px 10px rgba(0, 245, 255, 0.4);
    }}
    
    /* Sidebar Typography */
    [data-testid="stSidebar"] h1 {{
        color: {COLORS['foam_white']};
        font-weight: 800;
        font-size: 1.8rem;
        text-shadow: 0 0 15px rgba(0, 245, 255, 0.8), 2px 2px 5px rgba(0,0,0,0.8);
        letter-spacing: 2px;
        margin-bottom: 0.5rem;
    }}
    
    [data-testid="stSidebar"] .stMarkdown {{ color: {COLORS['light_aqua']}; }}
    [data-testid="stSidebar"] hr {{
        border-color: {COLORS['glass_border']};
        opacity: 0.5;
        margin: 1.5rem 0;
        box-shadow: 0 0 5px {COLORS['sky_blue']};
    }}
    
    /* Primary Buttons - Glowing Neon Wave */
    .stButton button[kind="primary"] {{
        background: linear-gradient(135deg, {COLORS['water_blue']} 0%, {COLORS['sky_blue']} 100%);
        color: {COLORS['deep_ocean']} !important;
        border: none;
        border-radius: 12px;
        padding: 14px 28px;
        font-weight: 700;
        font-size: 1rem;
        box-shadow: 0 0 20px rgba(0, 245, 255, 0.5), inset 0 2px 0 rgba(255, 255, 255, 0.4);
        transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        text-transform: uppercase;
        letter-spacing: 1px;
        position: relative;
        overflow: hidden;
        animation: liquidGlow 4s infinite alternate;
    }}
    
    .stButton button[kind="primary"]:hover {{
        background: linear-gradient(135deg, {COLORS['sky_blue']} 0%, {COLORS['seafoam']} 100%);
        transform: translateY(-5px) scale(1.05);
        box-shadow: 0 15px 35px rgba(0, 245, 255, 0.6), 0 0 25px rgba(0, 255, 170, 0.6);
    }}
    
    /* Secondary Buttons - Deep Glass */
    .stButton button {{
        background: rgba(22, 22, 26, 0.5);
        color: {COLORS['light_aqua']} !important;
        border: 1px solid {COLORS['sky_blue']};
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 500;
        transition: all 0.4s ease;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }}
    
    .stButton button:hover {{
        background: rgba(139, 92, 246, 0.7);
        border-color: {COLORS['teal']};
        color: {COLORS['foam_white']} !important;
        box-shadow: 0 8px 25px rgba(0, 245, 255, 0.3);
        transform: translateY(-3px);
    }}
    
    /* Metrics - Hologram Text */
    [data-testid="stMetricValue"] {{
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, {COLORS['sky_blue']} 0%, {COLORS['teal']} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 0 0 30px rgba(0, 245, 255, 0.4);
        font-family: 'JetBrains Mono', monospace;
    }}
    
    [data-testid="stMetricLabel"] {{
        color: {COLORS['text_secondary']};
        font-weight: 600;
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }}
    
    /* Cards and Expanders - Frosted Abyss Glass */
    .stExpander {{
        background: rgba(22, 22, 26, 0.3);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid {COLORS['glass_border']};
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.1);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Expander content text visibility */
    .stExpander p, .stExpander div, .stExpander span, .stExpander li {{
        color: {COLORS['text_primary']} !important;
    }}
    
    .stExpander [data-testid="stMarkdownContainer"] {{
        color: {COLORS['text_primary']} !important;
    }}
    
    .stExpander:hover {{
        box-shadow: 0 15px 40px rgba(0, 245, 255, 0.2), inset 0 1px 0 rgba(255,255,255,0.2);
        transform: translateY(-5px);
        border-color: rgba(0, 245, 255, 0.6);
    }}
    
    /* DataFrames / Tables - Deep Sea Interface */
    .stDataFrame {{
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 8px 30px rgba(0,0,0,0.5), 0 0 15px rgba(0, 245, 255, 0.1);
        border: 1px solid {COLORS['glass_border']};
        background: rgba(10, 10, 14, 0.6) !important;
    }}
    
    table {{
        border-collapse: separate;
        border-spacing: 0;
        background: transparent !important;
        color: {COLORS['text_primary']} !important;
    }}
    
    thead tr {{
        background: linear-gradient(135deg, rgba(22, 22, 26, 0.9) 0%, rgba(139, 92, 246, 0.7) 100%) !important;
        color: {COLORS['foam_white']} !important;
        border-bottom: 2px solid {COLORS['sky_blue']} !important;
    }}
    
    thead th {{
        color: {COLORS['foam_white']} !important;
    }}
    
    tbody tr:nth-child(even) {{ background-color: rgba(22, 22, 26, 0.4) !important; }}
    tbody tr:nth-child(odd) {{ background-color: rgba(10, 10, 14, 0.6) !important; }}
    
    tbody tr:hover {{
        background-color: rgba(0, 245, 255, 0.15) !important;
        transition: background-color 0.3s ease;
        box-shadow: inset 0 0 10px rgba(0, 245, 255, 0.2);
    }}
    
    tbody td {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Success/Warning/Error Messages - Glowing Elements */
    .stSuccess {{
        background: linear-gradient(135deg, rgba(0, 255, 170, 0.05) 0%, rgba(0, 255, 170, 0.15) 100%);
        border: 1px solid rgba(0, 255, 170, 0.4);
        border-left: 6px solid {COLORS['success']};
        border-radius: 12px;
        color: {COLORS['text_primary']};
        box-shadow: 0 0 20px rgba(0, 255, 170, 0.15);
        backdrop-filter: blur(15px);
    }}
    .stWarning {{
        background: linear-gradient(135deg, rgba(255, 187, 0, 0.05) 0%, rgba(255, 187, 0, 0.15) 100%);
        border: 1px solid rgba(255, 187, 0, 0.4);
        border-left: 6px solid {COLORS['warning']};
        border-radius: 12px;
        color: {COLORS['text_primary']};
        box-shadow: 0 0 20px rgba(255, 187, 0, 0.15);
        backdrop-filter: blur(15px);
    }}
    .stError {{
        background: linear-gradient(135deg, rgba(255, 0, 85, 0.05) 0%, rgba(255, 0, 85, 0.15) 100%);
        border: 1px solid rgba(255, 0, 85, 0.4);
        border-left: 6px solid {COLORS['error']};
        border-radius: 12px;
        color: {COLORS['text_primary']};
        box-shadow: 0 0 20px rgba(255, 0, 85, 0.15);
        backdrop-filter: blur(15px);
    }}
    .stInfo {{
        background: linear-gradient(135deg, rgba(0, 245, 255, 0.05) 0%, rgba(0, 245, 255, 0.15) 100%);
        border: 1px solid rgba(0, 245, 255, 0.4);
        border-left: 6px solid {COLORS['info']};
        border-radius: 12px;
        color: {COLORS['text_primary']} !important;
        box-shadow: 0 0 20px rgba(0, 245, 255, 0.15);
        backdrop-filter: blur(15px);
    }}
    
    /* Fix container text visibility */
    .stInfo p, .stInfo div, .stInfo span, .stInfo li {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Fix all alert/message boxes */
    [data-testid="stNotification"], [data-testid="stAlert"] {{
        background: rgba(22, 22, 26, 0.8) !important;
        color: {COLORS['text_primary']} !important;
        border-radius: 12px;
    }}
    
    [data-testid="stNotification"] p, [data-testid="stAlert"] p,
    [data-testid="stNotification"] div, [data-testid="stAlert"] div {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Fix container backgrounds */
    div[data-testid="stVerticalBlock"] > div[style*="background"] {{
        background: rgba(22, 22, 26, 0.5) !important;
        border-radius: 12px;
        padding: 20px;
    }}
    
    /* Ensure all text in containers is visible */
    .element-container p, .element-container div, .element-container span {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Input Fields - Translucent Neon Bounds */
    .stTextInput input, .stNumberInput input, .stTextArea textarea {{
        background: rgba(10, 10, 14, 0.5) !important;
        color: {COLORS['text_primary']} !important;
        border: 1px solid {COLORS['glass_border']} !important;
        border-radius: 12px;
        padding: 14px;
        font-size: 1rem;
        transition: all 0.4s ease;
        box-shadow: inset 0 2px 5px rgba(0,0,0,0.5);
    }}
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {{
        border-color: {COLORS['sky_blue']} !important;
        box-shadow: 0 0 15px rgba(0, 245, 255, 0.4), inset 0 0 5px rgba(0, 245, 255, 0.2) !important;
        outline: none;
        background: rgba(22, 22, 26, 0.7) !important;
    }}
    
    /* Fix Selectbox and Multiselect Backgrounds */
    div[data-baseweb="select"] > div {{
        background-color: rgba(10, 10, 14, 0.8) !important;
        color: {COLORS['text_primary']} !important;
        border: 1px solid {COLORS['glass_border']} !important;
        border-radius: 12px !important;
        transition: all 0.4s ease;
    }}
    div[data-baseweb="select"] > div:hover {{
        border-color: {COLORS['sky_blue']} !important;
        box-shadow: 0 0 10px rgba(0, 245, 255, 0.2) !important;
    }}
    div[data-baseweb="select"] span, div[data-baseweb="select"] div {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Dropdown Menus */
    div[data-baseweb="popover"] ul {{
        background-color: rgba(10, 10, 14, 0.95) !important;
        border: 1px solid {COLORS['sky_blue']} !important;
        border-radius: 8px !important;
    }}
    div[data-baseweb="popover"] li {{
        color: {COLORS['text_primary']} !important;
    }}
    div[data-baseweb="popover"] li:hover {{
        background-color: rgba(0, 245, 255, 0.15) !important;
    }}
    
    /* FIX: Make the BROWSE FILES button text completely visible and properly positioned */
    [data-testid="stFileUploader"] section > button {{
        color: {COLORS['deep_ocean']} !important;
        background: linear-gradient(135deg, {COLORS['sky_blue']} 0%, {COLORS['light_aqua']} 100%) !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 10px 24px !important;
        z-index: 10 !important;
        position: relative !important;
        box-shadow: 0 4px 15px rgba(0, 245, 255, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.6) !important;
        opacity: 1 !important;
        visibility: visible !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }}
    
    [data-testid="stFileUploader"] section > button:hover {{
        background: linear-gradient(135deg, {COLORS['light_aqua']} 0%, {COLORS['seafoam']} 100%) !important;
        box-shadow: 0 10px 25px rgba(0, 245, 255, 0.6) !important;
        transform: translateY(-2px) !important;
    }}
    
    /* File Uploader Container Fixes */
    [data-testid="stFileUploader"] {{
        background: linear-gradient(180deg, rgba(22, 22, 26, 0.2), rgba(10, 10, 14, 0.6)) !important;
        border: 2px dashed {COLORS['sky_blue']} !important;
        border-radius: 20px !important;
        padding: 2rem !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        backdrop-filter: blur(15px) !important;
        -webkit-backdrop-filter: blur(15px) !important;
    }}
    [data-testid="stFileUploader"]:hover {{
        border-color: {COLORS['teal']} !important;
        background: linear-gradient(180deg, rgba(139, 92, 246, 0.2), rgba(22, 22, 26, 0.4)) !important;
        box-shadow: 0 10px 40px rgba(0, 245, 255, 0.2), inset 0 0 30px rgba(0, 255, 170, 0.1) !important;
        transform: scale(1.02) !important;
    }}
    
    /* File Uploader Dropzone Text Override */
    [data-testid="stFileUploaderDropzoneInstructions"] > div > span {{
        color: {COLORS['foam_white']} !important;
        font-weight: 700 !important;
        text-shadow: 0 0 10px rgba(0, 245, 255, 0.3) !important;
        font-size: 1.2rem !important;
        display: block !important;
        margin-bottom: 0.5rem !important;
    }}
    [data-testid="stFileUploaderDropzoneInstructions"] > div > small {{
        color: {COLORS['light_aqua']} !important;
        font-size: 0.95rem !important;
        opacity: 0.8 !important;
    }}
    
    /* Fix inside standard Uploader inner layout */
    section[data-testid="stFileUploaderDropzone"] {{
        background-color: transparent !important;
    }}
    
    /* Progress Bar - Flowing Neon Stream */
    .stProgress > div > div {{
        background: linear-gradient(90deg, {COLORS['water_blue']} 0%, {COLORS['sky_blue']} 50%, {COLORS['teal']} 100%);
        background-size: 200% 100%;
        animation: flowWater 1.5s linear infinite;
        border-radius: 10px;
        box-shadow: 0 0 15px {COLORS['sky_blue']};
    }}
    @keyframes flowWater {{
        0% {{ background-position: 100% 0%; }}
        100% {{ background-position: -100% 0%; }}
    }}
    
    /* Tabs - Floating Neon Labels */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 12px;
        background: rgba(22, 22, 26, 0.3);
        padding: 10px;
        border-radius: 16px;
        backdrop-filter: blur(20px);
        border: 1px solid {COLORS['glass_border']};
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.4s ease;
        color: {COLORS['text_muted']};
    }}
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, {COLORS['ocean_blue']} 0%, {COLORS['water_blue']} 100%);
        color: {COLORS['text_primary']} !important;
        box-shadow: 0 5px 20px rgba(139, 92, 246, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.2);
        border: 1px solid {COLORS['sky_blue']};
    }}
    
    /* Download Button - Bioluminescent Warning Gradient */
    .stDownloadButton button {{
        background: linear-gradient(135deg, {COLORS['warning']} 0%, {COLORS['coral']} 100%) !important;
        color: {COLORS['deep_ocean']} !important;
        border: none;
        border-radius: 12px;
        padding: 14px 28px;
        font-weight: 800;
        box-shadow: 0 0 20px rgba(255, 0, 85, 0.4) !important;
        transition: all 0.4s ease !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }}
    .stDownloadButton button:hover {{
        transform: translateY(-5px) scale(1.03) !important;
        box-shadow: 0 10px 30px rgba(255, 187, 0, 0.6), 0 0 15px rgba(255, 0, 85, 0.6) !important;
    }}
    
    /* Headings - Glowing Text */
    h1, h2, h3 {{
        font-weight: 800;
        letter-spacing: -0.5px;
        text-transform: uppercase;
        color: {COLORS['foam_white']} !important;
    }}
    
    h1 {{
        font-size: 3rem;
        background: linear-gradient(135deg, {COLORS['light_aqua']} 0%, {COLORS['seafoam']} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 0 0 30px rgba(0, 245, 255, 0.3);
    }}
    h2 {{
        font-size: 2.2rem;
        color: {COLORS['sky_blue']} !important;
        text-shadow: 0 0 15px rgba(0, 245, 255, 0.2);
    }}
    h3 {{
        font-size: 1.5rem;
        color: {COLORS['teal']} !important;
    }}
    
    /* Smooth Pop In Animation */
    @keyframes deepPopIn {{
        0% {{ opacity: 0; transform: translateY(40px) scale(0.95); filter: blur(5px); }}
        100% {{ opacity: 1; transform: translateY(0) scale(1); filter: blur(0px); }}
    }}
    .element-container {{
        animation: deepPopIn 0.8s cubic-bezier(0.19, 1, 0.22, 1) forwards;
    }}
    
    /* Multiselect - Glowing Capsules */
    .stMultiSelect [data-baseweb="tag"] {{
        background: linear-gradient(135deg, {COLORS['water_blue']} 0%, {COLORS['sky_blue']} 100%);
        color: {COLORS['deep_ocean']};
        border-radius: 20px;
        padding: 6px 14px;
        font-weight: 700;
        box-shadow: 0 0 10px rgba(0, 245, 255, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.3);
    }}
    
    /* Text improvements for dark mode */
    p, li, span, div {{
        font-size: 1.05rem;
        line-height: 1.7;
    }}
    
    .stMarkdown p, .stMarkdown li, .stMarkdown span {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Global text visibility fix - ensure all text is visible */
    p, span, div, li, label, td, th {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Force all text elements to be visible - aggressive fix */
    * {{
        color: {COLORS['text_primary']};
    }}
    
    /* But keep specific elements with their intended colors */
    h1, h2, h3 {{
        color: {COLORS['sky_blue']} !important;
    }}
    
    button {{
        color: {COLORS['deep_ocean']} !important;
    }}
    
    /* Specific fixes for common containers */
    [data-testid="stVerticalBlock"] p,
    [data-testid="stVerticalBlock"] span,
    [data-testid="stVerticalBlock"] div,
    [data-testid="stVerticalBlock"] label {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Fix for code blocks and pre elements */
    code, pre {{
        color: {COLORS['sky_blue']} !important;
        background: rgba(10, 10, 14, 0.8) !important;
    }}
    
    /* Subtexts */
    small, .stCaption {{
        color: {COLORS['text_muted']} !important;
    }}
    
    strong {{
        color: {COLORS['light_aqua']} !important;
        font-weight: 700;
        text-shadow: 0 0 10px rgba(0, 245, 255, 0.2);
    }}
    
    label {{
        color: {COLORS['text_primary']} !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
        font-size: 1rem !important;
    }}
    
    /* Specific fixes for form field labels */
    .stSelectbox label, .stTextInput label, .stNumberInput label, 
    .stTextArea label, .stDateInput label, .stTimeInput label {{
        color: {COLORS['text_primary']} !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        margin-bottom: 8px !important;
        display: block !important;
    }}
    
    /* Fix for column headers and section titles */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, 
    .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Fix for any remaining invisible text */
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] span,
    [data-testid="stMarkdownContainer"] div {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Ensure selection color is vibrant */
    ::selection {{
        background: {COLORS['sky_blue']};
        color: {COLORS['deep_ocean']};
    }}
    
    @media (max-width: 768px) {{
        h1 {{ font-size: 2.2rem; }}
        .stButton button {{ padding: 12px 20px; font-size: 0.9rem; }}
        [data-testid="stAppViewBlockContainer"] {{ padding: 1.5rem !important; margin-top: 1.5rem !important; }}
    }}
    </style>
    """, unsafe_allow_html=True)

    # Sidebar drag-to-resize JS
    st.markdown("""
    <style>
    /* Resize handle on sidebar right edge */
    #sidebar-resizer {
        position: fixed;
        top: 0;
        width: 6px;
        height: 100vh;
        cursor: col-resize;
        z-index: 999999;
        background: transparent;
        transition: background 0.2s;
    }
    #sidebar-resizer:hover,
    #sidebar-resizer.active {
        background: linear-gradient(180deg, rgba(0,245,255,0.7), rgba(139,92,246,0.7));
        box-shadow: 0 0 12px rgba(0,245,255,0.6);
    }
    </style>
    <div id="sidebar-resizer"></div>
    <script>
    (function() {
        const MIN_W = 200, MAX_W = 600;
        const resizer = document.getElementById('sidebar-resizer');
        if (!resizer || resizer.dataset.init) return;
        resizer.dataset.init = '1';

        function getSidebar() {
            return document.querySelector('[data-testid="stSidebar"]');
        }

        function positionResizer() {
            const sb = getSidebar();
            if (!sb) return;
            const r = sb.getBoundingClientRect();
            resizer.style.left = (r.right - 3) + 'px';
        }

        // Restore saved width
        const saved = localStorage.getItem('st_sidebar_w');
        if (saved) {
            const sb = getSidebar();
            if (sb) {
                sb.style.width = saved + 'px';
                sb.style.minWidth = saved + 'px';
                sb.style.maxWidth = saved + 'px';
            }
        }
        positionResizer();

        let dragging = false;
        resizer.addEventListener('mousedown', function(e) {
            dragging = true;
            resizer.classList.add('active');
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
            e.preventDefault();
        });
        document.addEventListener('mousemove', function(e) {
            if (!dragging) return;
            const sb = getSidebar();
            if (!sb) return;
            let w = Math.min(MAX_W, Math.max(MIN_W, e.clientX));
            sb.style.width = w + 'px';
            sb.style.minWidth = w + 'px';
            sb.style.maxWidth = w + 'px';
            resizer.style.left = (w - 3) + 'px';
        });
        document.addEventListener('mouseup', function() {
            if (!dragging) return;
            dragging = false;
            resizer.classList.remove('active');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            const sb = getSidebar();
            if (sb) localStorage.setItem('st_sidebar_w', parseInt(sb.style.width));
        });

        // Reposition on interval (handles Streamlit reruns)
        setInterval(positionResizer, 500);
    })();
    </script>
    """, unsafe_allow_html=True)


def render_page_header_with_info(page_key):
    """Render page header with information button"""
    if page_key not in PAGE_INFO:
        return
    
    info = PAGE_INFO[page_key]
    
    # Create header with info button
    col1, col2 = st.columns([0.95, 0.05])
    
    with col1:
        st.title(info['title'])
        st.markdown(f"*{info['description']}*")
    
    with col2:
        # Info button
        if st.button("ℹ️", key=f"info_btn_{page_key}", help="Click for detailed information"):
            st.session_state[f'show_info_{page_key}'] = not st.session_state.get(f'show_info_{page_key}', False)
    
    # Show detailed info if button clicked
    if st.session_state.get(f'show_info_{page_key}', False):
        with st.expander("📖 Detailed Information", expanded=True):
            st.markdown(info['details'])
            if st.button("✖️ Close", key=f"close_info_{page_key}"):
                st.session_state[f'show_info_{page_key}'] = False
                st.rerun()
    
    st.markdown("---")


def render_feature_card(title, description, icon="📊"):
    """Render a feature card with icon"""
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(22, 22, 26, 0.6) 0%, rgba(10, 10, 14, 0.8) 100%); 
                border-radius: 16px; padding: 24px; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.1); 
                margin-bottom: 24px;
                backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px); border: 1px solid {COLORS['glass_border']};
                transition: all 0.4s ease;
                cursor: pointer;"
         onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 15px 40px rgba(0, 245, 255, 0.3), inset 0 1px 0 rgba(255,255,255,0.2)'; this.style.borderColor='{COLORS['teal']}';"
         onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 10px 30px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.1)'; this.style.borderColor='{COLORS['glass_border']}';">
        <h3 style="color: {COLORS['light_aqua']}; font-size: 1.4rem; margin-bottom: 12px; text-shadow: 0 0 10px rgba(0, 245, 255, 0.4);">{icon} {title}</h3>
        <p style="color: {COLORS['text_muted']}; font-size: 1.05rem; line-height: 1.6; margin: 0;">{description}</p>
    </div>
    """, unsafe_allow_html=True)
