"""
Smart District-Wise Split Module
Splits data by district, intelligently mapping talukas to their parent districts
"""

import streamlit as st
import pandas as pd
from io import BytesIO
import zipfile
from datetime import datetime
from src.persistent_mapping import PersistentMapping

# Complete Taluka to District mapping for Gujarat (267 talukas → 34 districts)
TALUKA_TO_DISTRICT = {
    # Ahmedabad District
    'ahmedabad': 'Ahmedabad', 'ahmadabad': 'Ahmedabad', 'bavla': 'Ahmedabad', 'daskroi': 'Ahmedabad',
    'detroj': 'Ahmedabad', 'rampura': 'Ahmedabad', 'detroj-rampura': 'Ahmedabad', 'dhandhuka': 'Ahmedabad',
    'dholera': 'Ahmedabad', 'dholka': 'Ahmedabad', 'mandal': 'Ahmedabad', 'sanand': 'Ahmedabad',
    'viramgam': 'Ahmedabad',
    
    # Amreli District
    'amreli': 'Amreli', 'babra': 'Amreli', 'bagasara': 'Amreli', 'dhari': 'Amreli', 'jafrabad': 'Amreli',
    'khambha': 'Amreli', 'kunkavav': 'Amreli', 'vadia': 'Amreli', 'kunkavav vadia': 'Amreli',
    'lathi': 'Amreli', 'lilia': 'Amreli', 'rajula': 'Amreli', 'savarkundla': 'Amreli',
    
    # Anand District
    'anand': 'Anand', 'anklav': 'Anand', 'borsad': 'Anand', 'khambhat': 'Anand', 'petlad': 'Anand',
    'sojitra': 'Anand', 'tarapur': 'Anand', 'umreth': 'Anand',
    
    # Aravalli District
    'bayad': 'Aravalli', 'bhiloda': 'Aravalli', 'dhansura': 'Aravalli', 'malpur': 'Aravalli',
    'meghraj': 'Aravalli', 'modasa': 'Aravalli', 'shamlaji': 'Aravalli', 'sathamba': 'Aravalli',
    
    # Banaskantha District
    'amirgadh': 'Banaskantha', 'dhanera': 'Banaskantha', 'deesa': 'Banaskantha', 'danta': 'Banaskantha',
    'dantiwada': 'Banaskantha', 'palanpur': 'Banaskantha', 'vadgam': 'Banaskantha', 'kankrej': 'Banaskantha',
    'shihori': 'Banaskantha', 'hadad': 'Banaskantha', 'ogad': 'Banaskantha', 'thara': 'Banaskantha',
    
    # Bharuch District
    'bharuch': 'Bharuch', 'amod': 'Bharuch', 'ankleshwar': 'Bharuch', 'hansot': 'Bharuch',
    'jambusar': 'Bharuch', 'jhagadia': 'Bharuch', 'netrang': 'Bharuch', 'vagra': 'Bharuch',
    'valia': 'Bharuch',
    
    # Bhavnagar District
    'bhavnagar': 'Bhavnagar', 'gariadhar': 'Bhavnagar', 'ghogha': 'Bhavnagar', 'jesar': 'Bhavnagar',
    'mahuva': 'Bhavnagar', 'palitana': 'Bhavnagar', 'sihor': 'Bhavnagar', 'talaja': 'Bhavnagar',
    'umrala': 'Bhavnagar', 'vallabhipur': 'Bhavnagar',
    
    # Botad District
    'botad': 'Botad', 'barwala': 'Botad', 'gadhada': 'Botad', 'ranpur': 'Botad',
    
    # Chhota Udaipur District
    'chhota udaipur': 'Chhota Udaipur', 'bodeli': 'Chhota Udaipur', 'jetpur pavi': 'Chhota Udaipur',
    'kavant': 'Chhota Udaipur', 'kawant': 'Chhota Udaipur', 'nasvadi': 'Chhota Udaipur',
    'sankheda': 'Chhota Udaipur', 'kadwal': 'Chhota Udaipur',
    
    # Dahod District
    'dahod': 'Dahod', 'devgadh baria': 'Dahod', 'dhanpur': 'Dahod', 'fatepura': 'Dahod',
    'garbada': 'Dahod', 'limkheda': 'Dahod', 'sanjeli': 'Dahod', 'jhalod': 'Dahod',
    'singvad': 'Dahod', 'sukhsar': 'Dahod', 'guru govind limdi': 'Dahod', 'govind guru limdi': 'Dahod',
    
    # Dang District
    'ahwa': 'Dang', 'subir': 'Dang', 'waghai': 'Dang', 'saputara': 'Dang',
    
    # Devbhoomi Dwarka District
    'bhanvad': 'Devbhoomi Dwarka', 'kalyanpur': 'Devbhoomi Dwarka', 'khambhalia': 'Devbhoomi Dwarka',
    'okhamandal': 'Devbhoomi Dwarka', 'dwarka': 'Devbhoomi Dwarka',
    
    # Gandhinagar District
    'gandhinagar': 'Gandhinagar', 'dehgam': 'Gandhinagar', 'kalol': 'Gandhinagar', 'mansa': 'Gandhinagar',
    
    # Gir Somnath District
    'gir-gadhada': 'Gir Somnath', 'gir gadhada': 'Gir Somnath', 'kodinar': 'Gir Somnath',
    'sutrapada': 'Gir Somnath', 'talala': 'Gir Somnath', 'una': 'Gir Somnath', 'veraval': 'Gir Somnath',
    
    # Jamnagar District
    'jamnagar': 'Jamnagar', 'dhrol': 'Jamnagar', 'jamjodhpur': 'Jamnagar', 'jodiya': 'Jamnagar',
    'kalavad': 'Jamnagar', 'lalpur': 'Jamnagar', 'jhadeshwar': 'Jamnagar',
    
    # Junagadh District
    'junagadh': 'Junagadh', 'bhesana': 'Junagadh', 'bhesan': 'Junagadh', 'keshod': 'Junagadh',
    'malia': 'Junagadh', 'maliya': 'Junagadh', 'manavadar': 'Junagadh', 'mangrol': 'Junagadh',
    'mendarda': 'Junagadh', 'vanthali': 'Junagadh', 'visavadar': 'Junagadh',
    
    # Kutch District
    'abdasa': 'Kutch', 'anjar': 'Kutch', 'bhachau': 'Kutch', 'bhuj': 'Kutch', 'gandhidham': 'Kutch',
    'lakhpat': 'Kutch', 'mandvi': 'Kutch', 'mundra': 'Kutch', 'nakhatrana': 'Kutch', 'rapar': 'Kutch',
    'kachchh': 'Kutch', 'kachch': 'Kutch', 'cutch': 'Kutch',
    
    # Kheda District
    'kheda': 'Kheda', 'galteshwar': 'Kheda', 'kapadvanj': 'Kheda', 'kathlal': 'Kheda',
    'mahudha': 'Kheda', 'matar': 'Kheda', 'mehmedabad': 'Kheda', 'nadiad': 'Kheda',
    'thasra': 'Kheda', 'vaso': 'Kheda', 'fagvel': 'Kheda',
    
    # Mahisagar District
    'balasinor': 'Mahisagar', 'kadana': 'Mahisagar', 'khanpur': 'Mahisagar', 'lunawada': 'Mahisagar',
    'lunavada': 'Mahisagar', 'santrampur': 'Mahisagar', 'virpur': 'Mahisagar', 'kothamba': 'Mahisagar',
    'godhar': 'Mahisagar',
    
    # Mehsana District
    'mehsana': 'Mehsana', 'becharaji': 'Mehsana', 'jotana': 'Mehsana', 'kadi': 'Mehsana',
    'kheralu': 'Mehsana', 'satlasana': 'Mehsana', 'unjha': 'Mehsana', 'vadnagar': 'Mehsana',
    'vijapur': 'Mehsana', 'visnagar': 'Mehsana',
    
    # Morbi District
    'halvad': 'Morbi', 'maliya': 'Morbi', 'morbi': 'Morbi', 'tankara': 'Morbi', 'wankaner': 'Morbi',
    
    # Narmada District
    'dediapada': 'Narmada', 'dediyapada': 'Narmada', 'garudeshwar': 'Narmada', 'nandod': 'Narmada',
    'sagbara': 'Narmada', 'tilakwada': 'Narmada', 'chikda': 'Narmada',
    
    # Navsari District
    'navsari': 'Navsari', 'vansda': 'Navsari', 'chikhli': 'Navsari', 'gandevi': 'Navsari',
    'jalalpore': 'Navsari', 'khergam': 'Navsari',
    
    # Panchmahal District
    'ghoghamba': 'Panchmahal', 'godhra': 'Panchmahal', 'halol': 'Panchmahal', 'jambughoda': 'Panchmahal',
    'morwa hadaf': 'Panchmahal', 'shehera': 'Panchmahal',
    
    # Patan District
    'patan': 'Patan', 'chanasma': 'Patan', 'harij': 'Patan', 'radhanpur': 'Patan', 'sami': 'Patan',
    'sankheswar': 'Patan', 'santalpur': 'Patan', 'sarasvati': 'Patan', 'saraswati': 'Patan',
    'sidhpur': 'Patan', 'shankeshwar': 'Patan',
    
    # Porbandar District
    'porbandar': 'Porbandar', 'kutiyana': 'Porbandar', 'ranavav': 'Porbandar',
    
    # Rajkot District
    'rajkot': 'Rajkot', 'dhoraji': 'Rajkot', 'gondal': 'Rajkot', 'jamkandorna': 'Rajkot',
    'jasdan': 'Rajkot', 'jetpur': 'Rajkot', 'kotada sangani': 'Rajkot', 'kotda sangani': 'Rajkot',
    'lodhika': 'Rajkot', 'paddhari': 'Rajkot', 'upleta': 'Rajkot', 'vinchchiya': 'Rajkot',
    'vinchhiya': 'Rajkot',
    
    # Sabarkantha District
    'himatnagar': 'Sabarkantha', 'himmatnagar': 'Sabarkantha', 'idar': 'Sabarkantha',
    'khedbrahma': 'Sabarkantha', 'poshina': 'Sabarkantha', 'prantij': 'Sabarkantha',
    'talod': 'Sabarkantha', 'vadali': 'Sabarkantha', 'vijaynagar': 'Sabarkantha',
    
    # Surat District
    'surat': 'Surat', 'bardoli': 'Surat', 'choryasi': 'Surat', 'chorasi': 'Surat',
    'kamrej': 'Surat', 'mandvi': 'Surat', 'olpad': 'Surat', 'palsana': 'Surat',
    'umarpada': 'Surat', 'areth': 'Surat', 'ambika': 'Surat', 'mangrol': 'Surat',
    
    # Surendranagar District
    'chotila': 'Surendranagar', 'chuda': 'Surendranagar', 'dasada': 'Surendranagar',
    'dhrangadhra': 'Surendranagar', 'lakhtar': 'Surendranagar', 'limbdi': 'Surendranagar',
    'muli': 'Surendranagar', 'sayla': 'Surendranagar', 'thangadh': 'Surendranagar',
    'wadhwan': 'Surendranagar',
    
    # Tapi District
    'nizar': 'Tapi', 'songadh': 'Tapi', 'uchhal': 'Tapi', 'valod': 'Tapi', 'vyara': 'Tapi',
    'kukarmunda': 'Tapi', 'dolvan': 'Tapi', 'ukai': 'Tapi',
    
    # Vadodara District
    'vadodara': 'Vadodara', 'baroda': 'Vadodara', 'dabhoi': 'Vadodara', 'desar': 'Vadodara',
    'karjan': 'Vadodara', 'padra': 'Vadodara', 'savli': 'Vadodara', 'sinor': 'Vadodara',
    'waghodia': 'Vadodara',
    
    # Valsad District
    'valsad': 'Valsad', 'dharampur': 'Valsad', 'kaprada': 'Valsad', 'pardi': 'Valsad',
    'umbergaon': 'Valsad', 'vapi': 'Valsad', 'nana pondha': 'Valsad',
    
    # Vav-Tharad District (New district)
    'bhabhar': 'Vav-Tharad', 'deodar': 'Vav-Tharad', 'dharnidhar': 'Vav-Tharad', 'rah': 'Vav-Tharad',
    'lakhani': 'Vav-Tharad', 'suigam': 'Vav-Tharad', 'tharad': 'Vav-Tharad', 'vav': 'Vav-Tharad',
}

# 34 Districts of Gujarat
GUJARAT_DISTRICTS = [
    'Ahmedabad', 'Amreli', 'Anand', 'Aravalli', 'Banaskantha', 'Bharuch', 'Bhavnagar', 'Botad',
    'Chhota Udaipur', 'Dahod', 'Dang', 'Devbhoomi Dwarka', 'Gandhinagar', 'Gir Somnath',
    'Jamnagar', 'Junagadh', 'Kutch', 'Kheda', 'Mahisagar', 'Mehsana', 'Morbi', 'Narmada',
    'Navsari', 'Panchmahal', 'Patan', 'Porbandar', 'Rajkot', 'Sabarkantha', 'Surat',
    'Surendranagar', 'Tapi', 'Vadodara', 'Valsad', 'Vav-Tharad'
]


def normalize_text(text):
    """Normalize text for matching (lowercase, strip, remove extra spaces)"""
    if pd.isna(text) or text is None:
        return ''
    return str(text).lower().strip().replace('  ', ' ')


def map_to_district(location_value):
    """
    Smart mapping: Maps taluka names to their parent district
    If already a district name, returns as-is
    If a taluka name, returns the parent district
    """
    if pd.isna(location_value) or location_value is None or location_value == '':
        return 'Unknown'
    
    normalized = normalize_text(location_value)
    
    # Check if it's already a district name
    for district in GUJARAT_DISTRICTS:
        if normalized == normalize_text(district):
            return district
    
    # Check if it's a taluka name
    if normalized in TALUKA_TO_DISTRICT:
        return TALUKA_TO_DISTRICT[normalized]
    
    # Partial matching for talukas (in case of variations)
    for taluka, district in TALUKA_TO_DISTRICT.items():
        if taluka in normalized or normalized in taluka:
            return district
    
    # If not found, return original value
    return location_value


def render_smart_district_split_page():
    """Render the Smart District-Wise Split page"""
    from src.ui_styling import render_page_header_with_info
    
    # Initialize persistent mapping
    mapping = PersistentMapping('smart_district_split')
    
    # Render page header with info button
    render_page_header_with_info('smart_district_split')
    
    st.markdown("""
    Upload a file and select the column containing district/taluka names. 
    The app will intelligently map talukas to their parent districts and split the data into 34 district-wise files.
    """)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Excel or CSV file",
        type=['xlsx', 'xls', 'csv'],
        help="File containing district or taluka names"
    )
    
    if uploaded_file:
        try:
            # Read file
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.success(f"✅ File loaded: {len(df)} rows, {len(df.columns)} columns")
            
            # Show preview
            with st.expander("📋 Data Preview", expanded=False):
                st.dataframe(df.head(10), use_container_width=True)
            
            st.markdown("---")
            
            # Column selection
            st.subheader("🎯 Select District/Taluka Column")
            
            # Show saved mappings indicator
            saved_count = mapping.get_saved_count()
            if saved_count > 0:
                st.success(f"✅ {saved_count} column mapping(s) remembered")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                district_column = st.selectbox(
                    "Column containing District or Taluka names",
                    options=df.columns.tolist(),
                    index=mapping.get_default_index('district_column', df.columns.tolist(), include_select_option=False),
                    help="Select the column that contains district or taluka names"
                )
                if district_column:
                    mapping.set('district_column', district_column)
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔍 Analyze Column", type="primary", use_container_width=True):
                    st.session_state.analyze_district_col = True
            
            # Analyze column if button clicked
            if st.session_state.get('analyze_district_col', False):
                st.markdown("---")
                st.subheader("📊 Column Analysis")
                
                # Get unique values
                unique_values = df[district_column].dropna().unique()
                
                # Map to districts
                mapped_districts = {}
                for val in unique_values:
                    district = map_to_district(val)
                    if district not in mapped_districts:
                        mapped_districts[district] = []
                    mapped_districts[district].append(val)
                
                # Show mapping
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Unique Values", len(unique_values))
                with col2:
                    st.metric("Mapped to Districts", len(mapped_districts))
                with col3:
                    recognized = sum(1 for d in mapped_districts.keys() if d in GUJARAT_DISTRICTS)
                    st.metric("Recognized Districts", recognized)
                
                # Show detailed mapping
                with st.expander("🗺️ Detailed Mapping", expanded=True):
                    mapping_data = []
                    for district, values in sorted(mapped_districts.items()):
                        mapping_data.append({
                            'District': district,
                            'Original Values': ', '.join(sorted(set(values))),
                            'Count': len([v for v in df[district_column] if map_to_district(v) == district])
                        })
                    
                    mapping_df = pd.DataFrame(mapping_data)
                    st.dataframe(mapping_df, use_container_width=True)
                
                st.session_state.district_mapping_ready = True
            
            # Split button
            if st.session_state.get('district_mapping_ready', False):
                st.markdown("---")
                st.subheader("📦 Generate District-Wise Files")
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    output_format = st.radio(
                        "Output Format",
                        options=["ZIP with separate files", "Single Excel with sheets"],
                        help="Choose how to organize the output"
                    )
                
                with col2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🚀 Generate Files", type="primary", use_container_width=True):
                        with st.spinner("Processing..."):
                            # Add mapped district column
                            df['Mapped_District'] = df[district_column].apply(map_to_district)
                            
                            # Group by mapped district
                            district_groups = df.groupby('Mapped_District')
                            
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            
                            if output_format == "ZIP with separate files":
                                # Create ZIP file
                                zip_buffer = BytesIO()
                                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                                    for district, group_df in district_groups:
                                        # Remove the temporary column
                                        output_df = group_df.drop(columns=['Mapped_District'])
                                        
                                        # Add S No.
                                        output_df.insert(0, 'S No.', range(1, len(output_df) + 1))
                                        
                                        # Create Excel file in memory
                                        excel_buffer = BytesIO()
                                        output_df.to_excel(excel_buffer, index=False, engine='openpyxl')
                                        excel_buffer.seek(0)
                                        
                                        # Add to ZIP
                                        filename = f"{district.replace(' ', '_')}_{len(output_df)}_records.xlsx"
                                        zip_file.writestr(filename, excel_buffer.getvalue())
                                
                                zip_buffer.seek(0)
                                
                                # Download button
                                st.success(f"✅ Created {len(district_groups)} district files!")
                                st.download_button(
                                    label=f"⬇️ Download ZIP ({len(district_groups)} files)",
                                    data=zip_buffer.getvalue(),
                                    file_name=f"district_wise_split_{timestamp}.zip",
                                    mime="application/zip",
                                    use_container_width=True
                                )
                            
                            else:
                                # Create single Excel with multiple sheets
                                excel_buffer = BytesIO()
                                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                                    for district, group_df in district_groups:
                                        # Remove the temporary column
                                        output_df = group_df.drop(columns=['Mapped_District'])
                                        
                                        # Add S No.
                                        output_df.insert(0, 'S No.', range(1, len(output_df) + 1))
                                        
                                        # Sheet name (max 31 chars for Excel)
                                        sheet_name = district[:31]
                                        output_df.to_excel(writer, sheet_name=sheet_name, index=False)
                                
                                excel_buffer.seek(0)
                                
                                # Download button
                                st.success(f"✅ Created Excel with {len(district_groups)} sheets!")
                                st.download_button(
                                    label=f"⬇️ Download Excel ({len(district_groups)} sheets)",
                                    data=excel_buffer.getvalue(),
                                    file_name=f"district_wise_split_{timestamp}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    use_container_width=True
                                )
                            
                            # Show summary
                            st.markdown("---")
                            st.subheader("📊 Split Summary")
                            
                            summary_data = []
                            for district, group_df in district_groups:
                                summary_data.append({
                                    'District': district,
                                    'Records': len(group_df),
                                    'Percentage': f"{(len(group_df) / len(df) * 100):.1f}%"
                                })
                            
                            summary_df = pd.DataFrame(summary_data).sort_values('Records', ascending=False)
                            st.dataframe(summary_df, use_container_width=True)
        
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.exception(e)
    
    else:
        st.info("📤 Upload a file to get started")
        
        # Show supported districts
        with st.expander("📍 Supported Districts (34)", expanded=False):
            cols = st.columns(3)
            for i, district in enumerate(sorted(GUJARAT_DISTRICTS)):
                with cols[i % 3]:
                    st.write(f"• {district}")
        
        # Show sample talukas
        with st.expander("🗺️ Sample Taluka Mappings", expanded=False):
            sample_mappings = [
                ('Ahmedabad', 'Bavla, Daskroi, Dholka, Sanand, Viramgam'),
                ('Rajkot', 'Dhoraji, Gondal, Jasdan, Jetpur, Upleta'),
                ('Surat', 'Bardoli, Kamrej, Mandvi, Olpad, Palsana'),
                ('Vadodara', 'Dabhoi, Karjan, Padra, Savli, Waghodia'),
                ('Mehsana', 'Kadi, Unjha, Visnagar, Vijapur, Becharaji'),
            ]
            
            for district, talukas in sample_mappings:
                st.markdown(f"**{district}**: {talukas}")
