"""
District Data Download Module - OPTIMIZED FOR LARGE DATA (Millions of rows)

Features:
- Victim Data: Upload victim file, select from Gujarat 33 districts
- Suspect Data: Upload suspect file, select State -> District or search
- Match Victim & Suspect: Upload both files, match by ACK number

Performance optimizations:
- Vectorized pandas operations instead of row-by-row loops
- Efficient merge operations for matching
- Caching for repeated operations
"""
import streamlit as st
import pandas as pd
from io import BytesIO
from typing import List, Tuple
import time
from src.persistent_mapping import PersistentMapping

# Gujarat Districts (33 districts)
GUJARAT_DISTRICTS = [
    "Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha", "Bharuch",
    "Bhavnagar", "Botad", "Chhota Udaipur", "Dahod", "Dang", "Devbhoomi Dwarka",
    "Gandhinagar", "Gir Somnath", "Jamnagar", "Junagadh", "Kheda", "Kutch",
    "Mahisagar", "Mehsana", "Morbi", "Narmada", "Navsari", "Panchmahal",
    "Patan", "Porbandar", "Rajkot", "Sabarkantha", "Surat", "Surendranagar",
    "Tapi", "Vadodara", "Valsad"
]

# All India Districts by State/UT
INDIA_STATES_DISTRICTS = {
    "Andhra Pradesh": ["Anantapur", "Chittoor", "East Godavari", "Guntur", "Krishna", "Kurnool", "Nellore", "Prakasam", "Srikakulam", "Visakhapatnam", "Vizianagaram", "West Godavari", "YSR Kadapa", "Alluri Sitharama Raju", "Anakapalli", "Annamayya", "Bapatla", "Eluru", "Kakinada", "Konaseema", "Nandyal", "NTR", "Palnadu", "Parvathipuram Manyam", "Sri Sathya Sai", "Tirupati"],
    "Arunachal Pradesh": ["Anjaw", "Changlang", "Dibang Valley", "East Kameng", "East Siang", "Kamle", "Kra Daadi", "Kurung Kumey", "Lepa Rada", "Lohit", "Longding", "Lower Dibang Valley", "Lower Siang", "Lower Subansiri", "Namsai", "Pakke Kessang", "Papum Pare", "Shi Yomi", "Siang", "Tawang", "Tirap", "Upper Siang", "Upper Subansiri", "West Kameng", "West Siang"],
    "Assam": ["Baksa", "Barpeta", "Biswanath", "Bongaigaon", "Cachar", "Charaideo", "Chirang", "Darrang", "Dhemaji", "Dhubri", "Dibrugarh", "Dima Hasao", "Goalpara", "Golaghat", "Hailakandi", "Hojai", "Jorhat", "Kamrup", "Kamrup Metropolitan", "Karbi Anglong", "Karimganj", "Kokrajhar", "Lakhimpur", "Majuli", "Morigaon", "Nagaon", "Nalbari", "Sivasagar", "Sonitpur", "South Salmara-Mankachar", "Tinsukia", "Udalguri", "West Karbi Anglong"],
    "Bihar": ["Araria", "Arwal", "Aurangabad", "Banka", "Begusarai", "Bhagalpur", "Bhojpur", "Buxar", "Darbhanga", "East Champaran", "Gaya", "Gopalganj", "Jamui", "Jehanabad", "Kaimur", "Katihar", "Khagaria", "Kishanganj", "Lakhisarai", "Madhepura", "Madhubani", "Munger", "Muzaffarpur", "Nalanda", "Nawada", "Patna", "Purnia", "Rohtas", "Saharsa", "Samastipur", "Saran", "Sheikhpura", "Sheohar", "Sitamarhi", "Siwan", "Supaul", "Vaishali", "West Champaran"],
    "Chhattisgarh": ["Balod", "Baloda Bazar", "Balrampur", "Bastar", "Bemetara", "Bijapur", "Bilaspur", "Dantewada", "Dhamtari", "Durg", "Gariaband", "Gaurela-Pendra-Marwahi", "Janjgir-Champa", "Jashpur", "Kabirdham", "Kanker", "Kondagaon", "Korba", "Koriya", "Mahasamund", "Mungeli", "Narayanpur", "Raigarh", "Raipur", "Rajnandgaon", "Sukma", "Surajpur", "Surguja"],
    "Goa": ["North Goa", "South Goa"],
    "Gujarat": GUJARAT_DISTRICTS,
    "Haryana": ["Ambala", "Bhiwani", "Charkhi Dadri", "Faridabad", "Fatehabad", "Gurugram", "Hisar", "Jhajjar", "Jind", "Kaithal", "Karnal", "Kurukshetra", "Mahendragarh", "Nuh", "Palwal", "Panchkula", "Panipat", "Rewari", "Rohtak", "Sirsa", "Sonipat", "Yamunanagar"],
    "Himachal Pradesh": ["Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kinnaur", "Kullu", "Lahaul and Spiti", "Mandi", "Shimla", "Sirmaur", "Solan", "Una"],
    "Jharkhand": ["Bokaro", "Chatra", "Deoghar", "Dhanbad", "Dumka", "East Singhbhum", "Garhwa", "Giridih", "Godda", "Gumla", "Hazaribagh", "Jamtara", "Khunti", "Koderma", "Latehar", "Lohardaga", "Pakur", "Palamu", "Ramgarh", "Ranchi", "Sahebganj", "Seraikela Kharsawan", "Simdega", "West Singhbhum"],
    "Karnataka": ["Bagalkot", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban", "Bidar", "Chamarajanagar", "Chikkaballapur", "Chikkamagaluru", "Chitradurga", "Dakshina Kannada", "Davanagere", "Dharwad", "Gadag", "Hassan", "Haveri", "Kalaburagi", "Kodagu", "Kolar", "Koppal", "Mandya", "Mysuru", "Raichur", "Ramanagara", "Shivamogga", "Tumakuru", "Udupi", "Uttara Kannada", "Vijayanagara", "Vijayapura", "Yadgir"],
    "Kerala": ["Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod", "Kollam", "Kottayam", "Kozhikode", "Malappuram", "Palakkad", "Pathanamthitta", "Thiruvananthapuram", "Thrissur", "Wayanad"],
    "Madhya Pradesh": ["Agar Malwa", "Alirajpur", "Anuppur", "Ashoknagar", "Balaghat", "Barwani", "Betul", "Bhind", "Bhopal", "Burhanpur", "Chhatarpur", "Chhindwara", "Damoh", "Datia", "Dewas", "Dhar", "Dindori", "Guna", "Gwalior", "Harda", "Hoshangabad", "Indore", "Jabalpur", "Jhabua", "Katni", "Khandwa", "Khargone", "Mandla", "Mandsaur", "Morena", "Narsinghpur", "Neemuch", "Niwari", "Panna", "Raisen", "Rajgarh", "Ratlam", "Rewa", "Sagar", "Satna", "Sehore", "Seoni", "Shahdol", "Shajapur", "Sheopur", "Shivpuri", "Sidhi", "Singrauli", "Tikamgarh", "Ujjain", "Umaria", "Vidisha"],
    "Maharashtra": ["Ahmednagar", "Akola", "Amravati", "Aurangabad", "Beed", "Bhandara", "Buldhana", "Chandrapur", "Dhule", "Gadchiroli", "Gondia", "Hingoli", "Jalgaon", "Jalna", "Kolhapur", "Latur", "Mumbai City", "Mumbai Suburban", "Nagpur", "Nanded", "Nandurbar", "Nashik", "Osmanabad", "Palghar", "Parbhani", "Pune", "Raigad", "Ratnagiri", "Sangli", "Satara", "Sindhudurg", "Solapur", "Thane", "Wardha", "Washim", "Yavatmal"],
    "Manipur": ["Bishnupur", "Chandel", "Churachandpur", "Imphal East", "Imphal West", "Jiribam", "Kakching", "Kamjong", "Kangpokpi", "Noney", "Pherzawl", "Senapati", "Tamenglong", "Tengnoupal", "Thoubal", "Ukhrul"],
    "Meghalaya": ["East Garo Hills", "East Jaintia Hills", "East Khasi Hills", "North Garo Hills", "Ri Bhoi", "South Garo Hills", "South West Garo Hills", "South West Khasi Hills", "West Garo Hills", "West Jaintia Hills", "West Khasi Hills"],
    "Mizoram": ["Aizawl", "Champhai", "Hnahthial", "Khawzawl", "Kolasib", "Lawngtlai", "Lunglei", "Mamit", "Saiha", "Saitual", "Serchhip"],
    "Nagaland": ["Chumoukedima", "Dimapur", "Kiphire", "Kohima", "Longleng", "Mokokchung", "Mon", "Niuland", "Noklak", "Peren", "Phek", "Shamator", "Tuensang", "Wokha", "Zunheboto"],
    "Odisha": ["Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak", "Boudh", "Cuttack", "Deogarh", "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur", "Jajpur", "Jharsuguda", "Kalahandi", "Kandhamal", "Kendrapara", "Kendujhar", "Khordha", "Koraput", "Malkangiri", "Mayurbhanj", "Nabarangpur", "Nayagarh", "Nuapada", "Puri", "Rayagada", "Sambalpur", "Subarnapur", "Sundargarh"],
    "Punjab": ["Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib", "Fazilka", "Ferozepur", "Gurdaspur", "Hoshiarpur", "Jalandhar", "Kapurthala", "Ludhiana", "Malerkotla", "Mansa", "Moga", "Mohali", "Muktsar", "Pathankot", "Patiala", "Rupnagar", "Sangrur", "Shaheed Bhagat Singh Nagar", "Tarn Taran"],
    "Rajasthan": ["Ajmer", "Alwar", "Banswara", "Baran", "Barmer", "Bharatpur", "Bhilwara", "Bikaner", "Bundi", "Chittorgarh", "Churu", "Dausa", "Dholpur", "Dungarpur", "Hanumangarh", "Jaipur", "Jaisalmer", "Jalore", "Jhalawar", "Jhunjhunu", "Jodhpur", "Karauli", "Kota", "Nagaur", "Pali", "Pratapgarh", "Rajsamand", "Sawai Madhopur", "Sikar", "Sirohi", "Sri Ganganagar", "Tonk", "Udaipur"],
    "Sikkim": ["East Sikkim", "North Sikkim", "South Sikkim", "West Sikkim"],
    "Tamil Nadu": ["Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri", "Dindigul", "Erode", "Kallakurichi", "Kancheepuram", "Karur", "Krishnagiri", "Madurai", "Mayiladuthurai", "Nagapattinam", "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai", "Ramanathapuram", "Ranipet", "Salem", "Sivaganga", "Tenkasi", "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli", "Tirupathur", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore", "Viluppuram", "Virudhunagar"],
    "Telangana": ["Adilabad", "Bhadradri Kothagudem", "Hyderabad", "Jagtial", "Jangaon", "Jayashankar Bhupalpally", "Jogulamba Gadwal", "Kamareddy", "Karimnagar", "Khammam", "Komaram Bheem", "Mahabubabad", "Mahabubnagar", "Mancherial", "Medak", "Medchal-Malkajgiri", "Mulugu", "Nagarkurnool", "Nalgonda", "Narayanpet", "Nirmal", "Nizamabad", "Peddapalli", "Rajanna Sircilla", "Rangareddy", "Sangareddy", "Siddipet", "Suryapet", "Vikarabad", "Wanaparthy", "Warangal Rural", "Warangal Urban", "Yadadri Bhuvanagiri"],
    "Tripura": ["Dhalai", "Gomati", "Khowai", "North Tripura", "Sepahijala", "South Tripura", "Unakoti", "West Tripura"],
    "Uttar Pradesh": ["Agra", "Aligarh", "Ambedkar Nagar", "Amethi", "Amroha", "Auraiya", "Ayodhya", "Azamgarh", "Baghpat", "Bahraich", "Ballia", "Balrampur", "Banda", "Barabanki", "Bareilly", "Basti", "Bhadohi", "Bijnor", "Budaun", "Bulandshahr", "Chandauli", "Chitrakoot", "Deoria", "Etah", "Etawah", "Farrukhabad", "Fatehpur", "Firozabad", "Gautam Buddha Nagar", "Ghaziabad", "Ghazipur", "Gonda", "Gorakhpur", "Hamirpur", "Hapur", "Hardoi", "Hathras", "Jalaun", "Jaunpur", "Jhansi", "Kannauj", "Kanpur Dehat", "Kanpur Nagar", "Kasganj", "Kaushambi", "Kushinagar", "Lakhimpur Kheri", "Lalitpur", "Lucknow", "Maharajganj", "Mahoba", "Mainpuri", "Mathura", "Mau", "Meerut", "Mirzapur", "Moradabad", "Muzaffarnagar", "Pilibhit", "Pratapgarh", "Prayagraj", "Raebareli", "Rampur", "Saharanpur", "Sambhal", "Sant Kabir Nagar", "Shahjahanpur", "Shamli", "Shravasti", "Siddharthnagar", "Sitapur", "Sonbhadra", "Sultanpur", "Unnao", "Varanasi"],
    "Uttarakhand": ["Almora", "Bageshwar", "Chamoli", "Champawat", "Dehradun", "Haridwar", "Nainital", "Pauri Garhwal", "Pithoragarh", "Rudraprayag", "Tehri Garhwal", "Udham Singh Nagar", "Uttarkashi"],
    "West Bengal": ["Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur", "Darjeeling", "Hooghly", "Howrah", "Jalpaiguri", "Jhargram", "Kalimpong", "Kolkata", "Malda", "Murshidabad", "Nadia", "North 24 Parganas", "Paschim Bardhaman", "Paschim Medinipur", "Purba Bardhaman", "Purba Medinipur", "Purulia", "South 24 Parganas", "Uttar Dinajpur"],
    "Andaman and Nicobar Islands": ["Nicobar", "North and Middle Andaman", "South Andaman"],
    "Chandigarh": ["Chandigarh"],
    "Dadra and Nagar Haveli and Daman and Diu": ["Dadra and Nagar Haveli", "Daman", "Diu"],
    "Delhi": ["Central Delhi", "East Delhi", "New Delhi", "North Delhi", "North East Delhi", "North West Delhi", "Shahdara", "South Delhi", "South East Delhi", "South West Delhi", "West Delhi"],
    "Jammu and Kashmir": ["Anantnag", "Bandipora", "Baramulla", "Budgam", "Doda", "Ganderbal", "Jammu", "Kathua", "Kishtwar", "Kulgam", "Kupwara", "Poonch", "Pulwama", "Rajouri", "Ramban", "Reasi", "Samba", "Shopian", "Srinagar", "Udhampur"],
    "Ladakh": ["Kargil", "Leh"],
    "Lakshadweep": ["Lakshadweep"],
    "Puducherry": ["Karaikal", "Mahe", "Puducherry", "Yanam"]
}

# Flat list for search
ALL_DISTRICTS_FLAT = []
for state, districts in INDIA_STATES_DISTRICTS.items():
    for district in districts:
        ALL_DISTRICTS_FLAT.append({"state": state, "district": district})


# ============== OPTIMIZED HELPER FUNCTIONS ==============

@st.cache_data(show_spinner=False)
def read_file_cached(file_content: bytes, filename: str) -> pd.DataFrame:
    """Read file with caching for performance."""
    buffer = BytesIO(file_content)
    if filename.lower().endswith('.csv'):
        return pd.read_csv(buffer, low_memory=False, dtype=str)
    else:
        return pd.read_excel(buffer, dtype=str)


def generate_excel_bytes(df: pd.DataFrame) -> bytes:
    """Generate Excel file bytes from DataFrame."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='District Data')
    return output.getvalue()


def filter_by_column(df: pd.DataFrame, column: str, value: str) -> pd.DataFrame:
    """Fast vectorized filtering by single column."""
    mask = df[column].astype(str).str.lower().str.strip() == value.lower().strip()
    return df.loc[mask].copy()


def filter_by_two_columns(df: pd.DataFrame, col1: str, val1: str, col2: str, val2: str) -> pd.DataFrame:
    """Fast vectorized filtering by two columns."""
    mask1 = df[col1].astype(str).str.lower().str.strip() == val1.lower().strip()
    mask2 = df[col2].astype(str).str.lower().str.strip() == val2.lower().strip()
    return df.loc[mask1 & mask2].copy()


def get_unique_states(df: pd.DataFrame, state_col: str) -> List[str]:
    """Get unique states from file."""
    states = df[state_col].dropna().astype(str).str.strip().unique().tolist()
    return sorted([s for s in states if s and s.lower() != 'nan'])


def get_unique_districts(df: pd.DataFrame, district_col: str, state_col: str = None, state: str = None) -> List[str]:
    """Get unique districts, optionally filtered by state."""
    if state_col and state:
        df = filter_by_column(df, state_col, state)
    districts = df[district_col].dropna().astype(str).str.strip().unique().tolist()
    return sorted([d for d in districts if d and d.lower() != 'nan'])


def match_files_fast(suspect_df: pd.DataFrame, victim_df: pd.DataFrame,
                     suspect_ack_col: str, victim_ack_col: str,
                     victim_district_col: str, victim_state_col: str,
                     victim_amount_col: str) -> Tuple[pd.DataFrame, int]:
    """
    OPTIMIZED matching using pandas merge (100x faster than loops).
    Reorders columns to put Victim data after ACK Number.
    """
    suspect_df = suspect_df.copy()
    victim_df = victim_df.copy()
    
    # Normalize ACK for matching
    suspect_df['_ack_key'] = suspect_df[suspect_ack_col].astype(str).str.strip().str.upper()
    victim_df['_ack_key'] = victim_df[victim_ack_col].astype(str).str.strip().str.upper()
    
    # Prepare victim columns for merge
    victim_merge = victim_df[['_ack_key', victim_district_col, victim_state_col, victim_amount_col]].copy()
    victim_merge.columns = ['_ack_key', 'Victim District', 'Victim State', 'Reported Amount (Victim)']
    victim_merge = victim_merge.drop_duplicates(subset=['_ack_key'], keep='first')
    
    # Merge
    result_df = suspect_df.merge(victim_merge, on='_ack_key', how='left')
    match_count = result_df['Victim District'].notna().sum()
    
    # Fill blanks
    result_df['Victim District'] = result_df['Victim District'].fillna('')
    result_df['Victim State'] = result_df['Victim State'].fillna('')
    result_df['Reported Amount (Victim)'] = result_df['Reported Amount (Victim)'].fillna('')
    
    # Cleanup temp column
    result_df = result_df.drop(columns=['_ack_key'])
    
    # REORDER COLUMNS: Put Victim columns right after ACK Number
    original_cols = list(suspect_df.columns)
    original_cols.remove('_ack_key')  # Remove temp column from list
    
    # Find position of ACK column
    ack_position = original_cols.index(suspect_ack_col) + 1
    
    # Build new column order
    new_order = original_cols[:ack_position]  # Columns up to and including ACK
    new_order.extend(['Victim District', 'Victim State', 'Reported Amount (Victim)'])  # Add victim columns
    new_order.extend(original_cols[ack_position:])  # Rest of the columns
    
    result_df = result_df[new_order]
    
    return result_df, int(match_count)


# ============== MAIN PAGE ==============

def render_district_download_page():
    """Render the district data download page with four tabs."""
    st.title("📍 Download District Wise Data")
    st.caption("⚡ Optimized for large datasets (millions of rows)")
    
    main_tab1, main_tab2, main_tab3, main_tab4 = st.tabs([
        "🏠 Victim Data (Gujarat)", 
        "🔍 Suspect Data (All India)",
        "🔗 Match Victim & Suspect",
        "🔄 Remove Duplicates by ACK"
    ])
    
    with main_tab1:
        render_victim_tab()
    
    with main_tab2:
        render_suspect_tab()
    
    with main_tab3:
        render_match_tab()
    
    with main_tab4:
        render_remove_duplicates_tab()


# ============== TAB 1: VICTIM DATA (GUJARAT) ==============

def render_victim_tab():
    """Render victim data tab - Gujarat districts only."""
    
    # Initialize persistent mapping
    mapping = PersistentMapping('district_data_victim')
    
    st.subheader("📤 Upload Victim Data File")
    
    uploaded_file = st.file_uploader(
        "Upload Victim Data File (Excel/CSV)",
        type=['xlsx', 'xls', 'csv'],
        key="victim_file_upload_tab1",
        help="Upload file containing victim data with district information"
    )
    
    if uploaded_file is None:
        st.info("📤 Please upload a victim data file to continue")
        return
    
    # Read file
    start_time = time.time()
    with st.spinner("Loading file..."):
        df = read_file_cached(uploaded_file.getvalue(), uploaded_file.name)
    load_time = time.time() - start_time
    
    st.success(f"✅ File loaded: **{len(df):,}** rows, **{len(df.columns)}** columns ({load_time:.2f}s)")
    
    with st.expander("📋 Preview Data (First 5 rows)", expanded=False):
        st.dataframe(df.head(), use_container_width=True)
    
    st.markdown("---")
    
    # Select district column
    st.subheader("🔧 Select District Column")
    
    # Show saved mappings indicator
    saved_count = mapping.get_saved_count()
    if saved_count > 0:
        st.success(f"✅ {saved_count} column mapping(s) remembered")
    
    columns = ["-- Select Column --"] + list(df.columns)
    district_col = st.selectbox(
        "Which column contains District names?",
        options=columns,
        index=mapping.get_default_index('district_col', columns),
        key="victim_district_col_tab1"
    )
    if district_col != "-- Select Column --":
        mapping.set('district_col', district_col)
    
    if district_col == "-- Select Column --":
        st.warning("⚠️ Please select the district column")
        return
    
    st.markdown("---")
    
    # Select Gujarat District
    st.subheader("📍 Select Gujarat District")
    st.caption("Select from 33 districts of Gujarat")
    
    selected_district = st.selectbox(
        "Select District",
        options=["-- Select District --"] + GUJARAT_DISTRICTS,
        key="victim_district_select_tab1"
    )
    
    if selected_district == "-- Select District --":
        return
    
    # Filter
    with st.spinner(f"Filtering {len(df):,} rows..."):
        start_time = time.time()
        filtered_df = filter_by_column(df, district_col, selected_district)
        filter_time = time.time() - start_time
    
    if len(filtered_df) > 0:
        st.success(f"✅ Found **{len(filtered_df):,} records** for {selected_district} ({filter_time:.2f}s)")
        
        with st.expander(f"Preview {selected_district} Data", expanded=False):
            st.dataframe(filtered_df.head(10), use_container_width=True)
        
        excel_bytes = generate_excel_bytes(filtered_df)
        st.download_button(
            label=f"⬇️ Download {selected_district} Victim Data ({len(filtered_df):,} records)",
            data=excel_bytes,
            file_name=f"victim_{selected_district.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary"
        )
    else:
        st.warning(f"⚠️ No records found for {selected_district}")


# ============== TAB 2: SUSPECT DATA (ALL INDIA) ==============

def render_suspect_tab():
    """Render suspect data tab - All India with state filtering and search."""
    
    # Initialize persistent mapping
    mapping = PersistentMapping('district_data_suspect')
    
    st.subheader("📤 Upload Suspect Data File")
    
    uploaded_file = st.file_uploader(
        "Upload Suspect Data File (Excel/CSV)",
        type=['xlsx', 'xls', 'csv'],
        key="suspect_file_upload_tab2",
        help="Upload file containing suspect data with district and state information"
    )
    
    if uploaded_file is None:
        st.info("📤 Please upload a suspect data file to continue")
        return
    
    # Read file
    start_time = time.time()
    with st.spinner("Loading file..."):
        df = read_file_cached(uploaded_file.getvalue(), uploaded_file.name)
    load_time = time.time() - start_time
    
    st.success(f"✅ File loaded: **{len(df):,}** rows, **{len(df.columns)}** columns ({load_time:.2f}s)")
    
    with st.expander("📋 Preview Data (First 5 rows)", expanded=False):
        st.dataframe(df.head(), use_container_width=True)
    
    st.markdown("---")
    
    # Select columns
    st.subheader("🔧 Select Columns")
    
    # Show saved mappings indicator
    saved_count = mapping.get_saved_count()
    if saved_count > 0:
        st.success(f"✅ {saved_count} column mapping(s) remembered")
    
    columns = ["-- Select Column --"] + list(df.columns)
    
    col1, col2 = st.columns(2)
    with col1:
        district_col = st.selectbox(
            "Select District Column",
            options=columns,
            index=mapping.get_default_index('district_col', columns),
            key="suspect_district_col_tab2"
        )
        if district_col != "-- Select Column --":
            mapping.set('district_col', district_col)
    with col2:
        state_col = st.selectbox(
            "Select State Column",
            options=columns,
            index=mapping.get_default_index('state_col', columns),
            key="suspect_state_col_tab2",
            help="Required to filter data accurately by state"
        )
        if state_col != "-- Select Column --":
            mapping.set('state_col', state_col)
    
    if district_col == "-- Select Column --" or state_col == "-- Select Column --":
        st.warning("⚠️ Please select both District and State columns")
        return
    
    st.markdown("---")
    
    # Sub-tabs for browse and search
    browse_tab, search_tab = st.tabs(["📂 Browse by State", "🔍 Search District"])
    
    with browse_tab:
        render_suspect_browse_section(df, district_col, state_col)
    
    with search_tab:
        render_suspect_search_section(df, district_col)


def render_suspect_browse_section(df: pd.DataFrame, district_col: str, state_col: str):
    """Render browse by state section."""
    st.markdown("### Select State → District")
    
    # Get states from FILE (not predefined list)
    available_states = get_unique_states(df, state_col)
    
    if not available_states:
        st.warning("No states found in the file")
        return
    
    st.info(f"Found **{len(available_states)}** states in your file")
    
    selected_state = st.selectbox(
        "Select State/UT",
        options=["-- Select State --"] + available_states,
        key="suspect_state_select_tab2"
    )
    
    if selected_state == "-- Select State --":
        return
    
    # Mass download for entire state
    st.markdown("---")
    st.markdown(f"#### 📦 Download All {selected_state} Data")
    
    with st.spinner("Filtering by state..."):
        all_state_data = filter_by_column(df, state_col, selected_state)
    
    if len(all_state_data) > 0:
        st.success(f"✅ Found **{len(all_state_data):,} total records** for {selected_state}")
        excel_bytes = generate_excel_bytes(all_state_data)
        st.download_button(
            label=f"⬇️ Download ALL {selected_state} Data ({len(all_state_data):,} records)",
            data=excel_bytes,
            file_name=f"suspect_{selected_state.replace(' ', '_')}_ALL.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.warning(f"No records found for {selected_state}")
    
    st.markdown("---")
    st.markdown(f"#### 📍 Or Select Specific District in {selected_state}")
    
    # Get districts from FILE for selected state
    available_districts = get_unique_districts(df, district_col, state_col, selected_state)
    
    if not available_districts:
        st.warning(f"No districts found for {selected_state}")
        return
    
    st.info(f"Found **{len(available_districts)}** districts in {selected_state}")
    
    selected_district = st.selectbox(
        f"Select District in {selected_state}",
        options=["-- Select District --"] + available_districts,
        key="suspect_district_select_tab2"
    )
    
    if selected_district == "-- Select District --":
        return
    
    # Filter by BOTH state and district
    with st.spinner("Filtering..."):
        filtered_df = filter_by_two_columns(df, state_col, selected_state, district_col, selected_district)
    
    if len(filtered_df) > 0:
        st.success(f"✅ Found **{len(filtered_df):,} records** for {selected_district}, {selected_state}")
        
        with st.expander(f"Preview {selected_district} Data", expanded=False):
            st.dataframe(filtered_df.head(10), use_container_width=True)
        
        excel_bytes = generate_excel_bytes(filtered_df)
        st.download_button(
            label=f"⬇️ Download {selected_district} ({selected_state}) Data ({len(filtered_df):,} records)",
            data=excel_bytes,
            file_name=f"suspect_{selected_state.replace(' ', '_')}_{selected_district.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary"
        )
    else:
        st.warning(f"⚠️ No records found for {selected_district} in {selected_state}")


def render_suspect_search_section(df: pd.DataFrame, district_col: str):
    """Render search district section."""
    st.markdown("### Search Any District")
    
    # Get all unique districts from file
    all_districts_in_file = get_unique_districts(df, district_col)
    
    st.info(f"**{len(all_districts_in_file)}** unique districts in your file")
    
    search_query = st.text_input(
        "Type district name to search",
        placeholder="e.g., Mumbai, Patna, Jaipur...",
        key="suspect_search_tab2"
    )
    
    if not search_query or len(search_query) < 2:
        st.caption("Type at least 2 characters to search")
        return
    
    # Search only in districts that exist in file
    matching = [d for d in all_districts_in_file if search_query.lower() in d.lower()]
    
    if not matching:
        st.warning(f"No districts found matching '{search_query}' in your file")
        return
    
    st.success(f"Found **{len(matching)}** matching districts in your file")
    
    selected_district = st.selectbox(
        "Select District",
        options=["-- Select --"] + matching,
        key="suspect_search_result_tab2"
    )
    
    if selected_district == "-- Select --":
        return
    
    # Filter by district
    with st.spinner("Filtering..."):
        filtered_df = filter_by_column(df, district_col, selected_district)
    
    if len(filtered_df) > 0:
        st.success(f"✅ Found **{len(filtered_df):,} records** for {selected_district}")
        
        with st.expander(f"Preview {selected_district} Data", expanded=False):
            st.dataframe(filtered_df.head(10), use_container_width=True)
        
        excel_bytes = generate_excel_bytes(filtered_df)
        st.download_button(
            label=f"⬇️ Download {selected_district} Data ({len(filtered_df):,} records)",
            data=excel_bytes,
            file_name=f"suspect_{selected_district.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary"
        )
    else:
        st.warning(f"⚠️ No records found for {selected_district}")


# ============== TAB 3: MATCH VICTIM & SUSPECT ==============

def render_match_tab():
    """Render Match Victim & Suspect tab - combines both files by ACK number."""
    
    # Initialize persistent mapping
    mapping = PersistentMapping('district_data_match')
    
    st.subheader("🔗 Match Victim & Suspect Data")
    st.markdown("""
    Upload both files to match records by **Acknowledgement Number (ACK)**.
    The output will contain all suspect data + Victim District, Victim State, and Reported Amount from victim file.
    """)
    
    st.markdown("---")
    
    # Upload both files
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📁 File 1: Suspect Data")
        suspect_file = st.file_uploader(
            "Upload Suspect Data File",
            type=['xlsx', 'xls', 'csv'],
            key="match_suspect_file",
            help="File with suspect details (District, State, ACK Number, etc.)"
        )
    
    with col2:
        st.markdown("#### 📁 File 2: Victim Data")
        victim_file = st.file_uploader(
            "Upload Victim Data File",
            type=['xlsx', 'xls', 'csv'],
            key="match_victim_file",
            help="File with victim details (District, State, ACK Number, Reported Amount)"
        )
    
    if suspect_file is None or victim_file is None:
        st.info("📤 Please upload both files to continue")
        return
    
    # Read both files
    with st.spinner("Loading suspect file..."):
        suspect_df = read_file_cached(suspect_file.getvalue(), suspect_file.name)
    st.success(f"✅ Suspect file loaded: **{len(suspect_df):,}** rows")
    
    with st.spinner("Loading victim file..."):
        victim_df = read_file_cached(victim_file.getvalue(), victim_file.name)
    st.success(f"✅ Victim file loaded: **{len(victim_df):,}** rows")
    
    # Preview both files
    with st.expander("📋 Preview Suspect Data", expanded=False):
        st.dataframe(suspect_df.head(), use_container_width=True)
    
    with st.expander("📋 Preview Victim Data", expanded=False):
        st.dataframe(victim_df.head(), use_container_width=True)
    
    st.markdown("---")
    st.subheader("Step 2: Map Columns")
    
    # Show saved mappings indicator
    saved_count = mapping.get_saved_count()
    if saved_count > 0:
        st.success(f"✅ {saved_count} column mapping(s) remembered")
    
    # Column mapping for Suspect file
    st.markdown("#### Suspect File Columns")
    suspect_cols = ["-- Select Column --"] + list(suspect_df.columns)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        suspect_ack_col = st.selectbox(
            "ACK Number Column (Suspect)",
            options=suspect_cols,
            index=mapping.get_default_index('suspect_ack_col', suspect_cols),
            key="match_suspect_ack"
        )
        if suspect_ack_col != "-- Select Column --":
            mapping.set('suspect_ack_col', suspect_ack_col)
    with col2:
        suspect_district_col = st.selectbox(
            "District Column (Suspect)",
            options=suspect_cols,
            index=mapping.get_default_index('suspect_district_col', suspect_cols),
            key="match_suspect_district"
        )
        if suspect_district_col != "-- Select Column --":
            mapping.set('suspect_district_col', suspect_district_col)
    with col3:
        suspect_state_col = st.selectbox(
            "State Column (Suspect)",
            options=suspect_cols,
            index=mapping.get_default_index('suspect_state_col', suspect_cols),
            key="match_suspect_state"
        )
        if suspect_state_col != "-- Select Column --":
            mapping.set('suspect_state_col', suspect_state_col)
    
    # Column mapping for Victim file
    st.markdown("#### Victim File Columns")
    victim_cols = ["-- Select Column --"] + list(victim_df.columns)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        victim_ack_col = st.selectbox(
            "ACK Number Column",
            options=victim_cols,
            index=mapping.get_default_index('victim_ack_col', victim_cols),
            key="match_victim_ack"
        )
        if victim_ack_col != "-- Select Column --":
            mapping.set('victim_ack_col', victim_ack_col)
    with col2:
        victim_district_col = st.selectbox(
            "District Column",
            options=victim_cols,
            index=mapping.get_default_index('victim_district_col', victim_cols),
            key="match_victim_district"
        )
        if victim_district_col != "-- Select Column --":
            mapping.set('victim_district_col', victim_district_col)
    with col3:
        victim_state_col = st.selectbox(
            "State Column",
            options=victim_cols,
            index=mapping.get_default_index('victim_state_col', victim_cols),
            key="match_victim_state"
        )
        if victim_state_col != "-- Select Column --":
            mapping.set('victim_state_col', victim_state_col)
    with col4:
        victim_amount_col = st.selectbox(
            "Reported Amount Column",
            options=victim_cols,
            index=mapping.get_default_index('victim_amount_col', victim_cols),
            key="match_victim_amount"
        )
        if victim_amount_col != "-- Select Column --":
            mapping.set('victim_amount_col', victim_amount_col)
    
    # Validate all columns selected
    required_cols = [
        suspect_ack_col, suspect_district_col, suspect_state_col,
        victim_ack_col, victim_district_col, victim_state_col, victim_amount_col
    ]
    
    if any(col == "-- Select Column --" for col in required_cols):
        st.warning("⚠️ Please select all required columns from both files")
        return
    
    st.markdown("---")
    st.subheader("Step 3: Match & Download")
    
    if st.button("🔗 Match Files by ACK Number", type="primary", use_container_width=True):
        start_time = time.time()
        
        with st.spinner(f"Matching {len(suspect_df):,} suspect records with {len(victim_df):,} victim records..."):
            result_df, match_count = match_files_fast(
                suspect_df, victim_df,
                suspect_ack_col, victim_ack_col,
                victim_district_col, victim_state_col, victim_amount_col
            )
        
        match_time = time.time() - start_time
        
        # Store in session state
        st.session_state['matched_df'] = result_df
        st.session_state['matched_suspect_district_col'] = suspect_district_col
        st.session_state['matched_suspect_state_col'] = suspect_state_col
        
        match_pct = (match_count / len(suspect_df) * 100) if len(suspect_df) > 0 else 0
        st.success(f"✅ Matching complete! **{match_count:,}** out of **{len(suspect_df):,}** records matched ({match_pct:.1f}%) in **{match_time:.2f}s**")
        
        if match_count < len(suspect_df):
            st.info(f"ℹ️ {len(suspect_df) - match_count:,} records did not have matching ACK numbers (Victim columns left blank)")
    
    # Show results and download options if matching is done
    if 'matched_df' in st.session_state:
        render_match_results()


def render_match_results():
    """Render the results section after matching."""
    result_df = st.session_state['matched_df']
    suspect_district_col = st.session_state['matched_suspect_district_col']
    suspect_state_col = st.session_state['matched_suspect_state_col']
    
    st.markdown("---")
    st.subheader("Step 4: Download District Wise Data")
    
    with st.expander("📋 Preview Matched Data", expanded=False):
        st.dataframe(result_df.head(10), use_container_width=True)
    
    # Amount Filter
    st.markdown("#### � Filnter by Reported Amount")
    min_amount = st.number_input(
        "Minimum Reported Amount (₹)",
        min_value=0,
        value=0,
        step=100000,
        help="Show only records where Reported Amount is above this value"
    )
    
    # Apply amount filter if specified
    if min_amount > 0:
        # Convert to numeric for comparison
        filtered_df = result_df.copy()
        filtered_df['_amount_numeric'] = pd.to_numeric(
            filtered_df['Reported Amount (Victim)'].astype(str).str.replace(',', '').str.strip(),
            errors='coerce'
        ).fillna(0)
        filtered_df = filtered_df[filtered_df['_amount_numeric'] >= min_amount]
        filtered_df = filtered_df.drop(columns=['_amount_numeric'])
        
        st.info(f"Filtered: **{len(filtered_df):,}** records with Reported Amount ≥ ₹{min_amount:,}")
    else:
        filtered_df = result_df
    
    # Download all matched data
    st.markdown("#### 📦 Download All Matched Data")
    excel_bytes = generate_excel_bytes(filtered_df)
    st.download_button(
        label=f"⬇️ Download All Matched Data ({len(filtered_df):,} records)",
        data=excel_bytes,
        file_name="matched_victim_suspect_all.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
    
    st.markdown("---")
    st.markdown("#### 📍 Or Download by Suspect District/State")
    
    # Show which columns are being used
    st.caption(f"Using State column: **{suspect_state_col}** | District column: **{suspect_district_col}**")
    
    # Get available states from filtered data
    available_states = get_unique_states(filtered_df, suspect_state_col)
    
    if not available_states:
        st.warning("No states found in matched data")
        return
    
    st.info(f"Found **{len(available_states)}** states in matched data")
    
    selected_state = st.selectbox(
        "Select Suspect State",
        options=["-- Select State --"] + available_states,
        key="match_filter_state"
    )
    
    if selected_state == "-- Select State --":
        return
    
    # Download all state data
    state_data = filter_by_column(filtered_df, suspect_state_col, selected_state)
    
    if len(state_data) > 0:
        st.success(f"Found **{len(state_data):,} records** for {selected_state}")
        
        excel_bytes = generate_excel_bytes(state_data)
        st.download_button(
            label=f"⬇️ Download ALL {selected_state} Matched Data ({len(state_data):,} records)",
            data=excel_bytes,
            file_name=f"matched_{selected_state.replace(' ', '_')}_ALL.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        # District selection
        st.markdown("---")
        available_districts = get_unique_districts(filtered_df, suspect_district_col, suspect_state_col, selected_state)
        
        if available_districts:
            st.info(f"Found **{len(available_districts)}** districts in {selected_state}")
            
            selected_district = st.selectbox(
                f"Select District in {selected_state}",
                options=["-- Select District --"] + available_districts,
                key="match_filter_district"
            )
            
            if selected_district != "-- Select District --":
                district_data = filter_by_two_columns(
                    filtered_df, suspect_state_col, selected_state,
                    suspect_district_col, selected_district
                )
                
                if len(district_data) > 0:
                    st.success(f"Found **{len(district_data):,} records** for {selected_district}, {selected_state}")
                    
                    with st.expander(f"Preview {selected_district} Data", expanded=False):
                        st.dataframe(district_data.head(10), use_container_width=True)
                    
                    excel_bytes = generate_excel_bytes(district_data)
                    st.download_button(
                        label=f"⬇️ Download {selected_district} ({selected_state}) Matched Data ({len(district_data):,} records)",
                        data=excel_bytes,
                        file_name=f"matched_{selected_state.replace(' ', '_')}_{selected_district.replace(' ', '_')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        type="primary"
                    )
                else:
                    st.warning(f"No records found for {selected_district}")
    else:
        st.warning(f"No records found for {selected_state}")



# ============== TAB 4: REMOVE DUPLICATES BY ACK ==============

def render_remove_duplicates_tab():
    """Render Remove Duplicates by ACK tab - keeps first entry per ACK number."""
    
    # Initialize persistent mapping
    mapping = PersistentMapping('district_data_dedup')
    
    st.subheader("🔄 Remove Duplicates by ACK Number")
    st.markdown("""
    Upload a file and remove duplicate entries based on **Acknowledgement Number (ACK)**.
    - Keeps only the **first occurrence** of each ACK number
    - Select up to **5 columns** for output (ACK is required, others optional)
    """)
    
    st.markdown("---")
    
    # Upload file
    uploaded_file = st.file_uploader(
        "Upload Data File (Excel/CSV)",
        type=['xlsx', 'xls', 'csv'],
        key="dedup_file_upload",
        help="Upload file containing data with ACK numbers"
    )
    
    if uploaded_file is None:
        st.info("📤 Please upload a file to continue")
        return
    
    # Read file
    with st.spinner("Loading file..."):
        df = read_file_cached(uploaded_file.getvalue(), uploaded_file.name)
    
    st.success(f"✅ File loaded: **{len(df):,}** rows, **{len(df.columns)}** columns")
    
    with st.expander("📋 Preview Data (First 5 rows)", expanded=False):
        st.dataframe(df.head(), use_container_width=True)
    
    st.markdown("---")
    st.subheader("🔧 Select Columns")
    
    # Show saved mappings indicator
    saved_count = mapping.get_saved_count()
    if saved_count > 0:
        st.success(f"✅ {saved_count} column mapping(s) remembered")
    
    columns = list(df.columns)
    columns_with_none = ["-- Not Selected --"] + columns
    
    # ACK Column (Required)
    st.markdown("#### Required Column")
    ack_col = st.selectbox(
        "ACK Number Column (Required) *",
        options=["-- Select Column --"] + columns,
        index=mapping.get_default_index('ack_col', ["-- Select Column --"] + columns),
        key="dedup_ack_col",
        help="This column will be used to identify and remove duplicates"
    )
    if ack_col != "-- Select Column --":
        mapping.set('ack_col', ack_col)
    
    if ack_col == "-- Select Column --":
        st.warning("⚠️ Please select the ACK Number column")
        return
    
    # Optional Columns (up to 4 more)
    st.markdown("#### Optional Columns (Select up to 4 more)")
    st.caption("These columns will be included in the output along with ACK Number")
    
    col1, col2 = st.columns(2)
    
    with col1:
        col2_select = st.selectbox(
            "Column 2 (Optional)",
            options=columns_with_none,
            key="dedup_col2"
        )
        col3_select = st.selectbox(
            "Column 3 (Optional)",
            options=columns_with_none,
            key="dedup_col3"
        )
    
    with col2:
        col4_select = st.selectbox(
            "Column 4 (Optional)",
            options=columns_with_none,
            key="dedup_col4"
        )
        col5_select = st.selectbox(
            "Column 5 (Optional)",
            options=columns_with_none,
            key="dedup_col5"
        )
    
    # Build selected columns list
    selected_cols = [ack_col]
    for col in [col2_select, col3_select, col4_select, col5_select]:
        if col != "-- Not Selected --" and col not in selected_cols:
            selected_cols.append(col)
    
    st.info(f"**Selected columns:** {', '.join(selected_cols)}")
    
    st.markdown("---")
    st.subheader("🚀 Process & Download")
    
    if st.button("🔄 Remove Duplicates", type="primary", use_container_width=True, key="dedup_process_btn"):
        with st.spinner("Removing duplicates..."):
            # Get only selected columns
            result_df = df[selected_cols].copy()
            
            # Count before
            total_before = len(result_df)
            
            # Remove duplicates - keep first occurrence
            result_df = result_df.drop_duplicates(subset=[ack_col], keep='first')
            
            # Count after
            total_after = len(result_df)
            duplicates_removed = total_before - total_after
            
            # Add Sr. No. column at the beginning
            result_df = result_df.reset_index(drop=True)
            result_df.insert(0, 'Sr. No.', range(1, len(result_df) + 1))
            
            # Store in session state
            st.session_state['dedup_result_df'] = result_df
            st.session_state['dedup_stats'] = {
                'before': total_before,
                'after': total_after,
                'removed': duplicates_removed
            }
        
        st.success(f"✅ Duplicates removed successfully!")
    
    # Show results if available
    if 'dedup_result_df' in st.session_state:
        result_df = st.session_state['dedup_result_df']
        stats = st.session_state['dedup_stats']
        
        # Show statistics
        st.markdown("---")
        st.subheader("📊 Results")
        
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        with stat_col1:
            st.metric("Total Records (Before)", f"{stats['before']:,}")
        with stat_col2:
            st.metric("Unique ACK Records (After)", f"{stats['after']:,}")
        with stat_col3:
            st.metric("Duplicates Removed", f"{stats['removed']:,}")
        
        # Preview
        with st.expander("📋 Preview Deduplicated Data", expanded=True):
            st.dataframe(result_df.head(20), use_container_width=True)
        
        # Download
        st.markdown("---")
        st.subheader("📥 Download")
        
        download_col1, download_col2 = st.columns(2)
        
        with download_col1:
            excel_bytes = generate_excel_bytes(result_df)
            st.download_button(
                label=f"⬇️ Download Excel ({stats['after']:,} records)",
                data=excel_bytes,
                file_name=f"deduplicated_by_ack_{stats['after']}_records.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary"
            )
        
        with download_col2:
            csv_bytes = result_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"⬇️ Download CSV ({stats['after']:,} records)",
                data=csv_bytes,
                file_name=f"deduplicated_by_ack_{stats['after']}_records.csv",
                mime="text/csv",
                use_container_width=True
            )
