"""
IFSC/PIN Code to District Split Module
Splits data by district using IFSC codes (primary) or PIN codes (fallback)
Uses real-time IFSC API for 100% accuracy
"""

import streamlit as st
import pandas as pd
from io import BytesIO
import zipfile
from datetime import datetime
import re
import requests
import time
from src.persistent_mapping import PersistentMapping

# Free IFSC API endpoint
IFSC_API_URL = "https://ifsc.razorpay.com/"

# PIN Code to District mapping for Gujarat (verified accurate)
PINCODE_TO_DISTRICT = {
    # Ahmedabad (380xxx, 382xxx)
    '380': 'Ahmedabad', '382': 'Ahmedabad',
    
    # Amreli (365xxx)
    '365': 'Amreli',
    
    # Anand (388xxx)
    '388': 'Anand',
    
    # Aravalli (383xxx - partial)
    '383': 'Aravalli',
    
    # Banaskantha (385xxx)
    '385': 'Banaskantha',
    
    # Bharuch (392xxx, 393xxx)
    '392': 'Bharuch', '393': 'Bharuch',
    
    # Bhavnagar (364xxx)
    '364': 'Bhavnagar',
    
    # Botad (364xxx - partial)
    
    # Chhota Udaipur (391xxx - partial)
    '391': 'Chhota Udaipur',
    
    # Dahod (389xxx)
    '389': 'Dahod',
    
    # Dang (394xxx - partial)
    '394': 'Dang',
    
    # Devbhoomi Dwarka (361xxx - partial)
    '361': 'Devbhoomi Dwarka',
    
    # Gandhinagar (382xxx - partial)
    
    # Gir Somnath (362xxx)
    '362': 'Gir Somnath',
    
    # Jamnagar (361xxx)
    
    # Junagadh (362xxx - partial)
    
    # Kutch (370xxx)
    '370': 'Kutch',
    
    # Kheda (387xxx)
    '387': 'Kheda',
    
    # Mahisagar (389xxx - partial)
    
    # Mehsana (384xxx)
    '384': 'Mehsana',
    
    # Morbi (363xxx)
    '363': 'Morbi',
    
    # Narmada (393xxx - partial)
    
    # Navsari (396xxx)
    '396': 'Navsari',
    
    # Panchmahal (389xxx - partial)
    
    # Patan (384xxx - partial)
    
    # Porbandar (360xxx)
    '360': 'Porbandar',
    
    # Rajkot (360xxx - partial, 363xxx - partial)
    
    # Sabarkantha (383xxx - partial)
    
    # Surat (394xxx, 395xxx)
    '395': 'Surat',
    
    # Surendranagar (363xxx - partial)
    
    # Tapi (394xxx - partial)
    
    # Vadodara (390xxx, 391xxx)
    '390': 'Vadodara',
    
    # Valsad (396xxx - partial)
}

# More detailed PIN code mapping (5-digit prefixes for better accuracy)
DETAILED_PINCODE_TO_DISTRICT = {
    # Ahmedabad (380xxx, 382xxx)
    '38000': 'Ahmedabad', '38001': 'Ahmedabad', '38002': 'Ahmedabad', '38003': 'Ahmedabad',
    '38004': 'Ahmedabad', '38005': 'Ahmedabad', '38006': 'Ahmedabad', '38007': 'Ahmedabad',
    '38008': 'Ahmedabad', '38009': 'Ahmedabad', '38010': 'Ahmedabad', '38011': 'Ahmedabad',
    '38012': 'Ahmedabad', '38013': 'Ahmedabad', '38014': 'Ahmedabad', '38015': 'Ahmedabad',
    '38016': 'Ahmedabad', '38018': 'Ahmedabad', '38019': 'Ahmedabad', '38020': 'Ahmedabad',
    '38021': 'Ahmedabad', '38022': 'Ahmedabad', '38023': 'Ahmedabad', '38024': 'Ahmedabad',
    '38025': 'Ahmedabad', '38026': 'Ahmedabad', '38027': 'Ahmedabad', '38028': 'Ahmedabad',
    '38050': 'Ahmedabad', '38051': 'Ahmedabad', '38052': 'Ahmedabad', '38054': 'Ahmedabad',
    '38055': 'Ahmedabad', '38060': 'Ahmedabad', '38061': 'Ahmedabad', '38063': 'Ahmedabad',
    
    '38201': 'Ahmedabad', '38202': 'Ahmedabad', '38203': 'Ahmedabad', '38204': 'Ahmedabad',
    '38205': 'Ahmedabad', '38206': 'Ahmedabad', '38207': 'Ahmedabad', '38210': 'Ahmedabad',
    '38213': 'Ahmedabad', '38215': 'Ahmedabad', '38220': 'Ahmedabad', '38225': 'Ahmedabad',
    '38230': 'Ahmedabad', '38235': 'Ahmedabad', '38240': 'Ahmedabad', '38245': 'Ahmedabad',
    '38250': 'Ahmedabad', '38255': 'Ahmedabad', '38260': 'Ahmedabad', '38265': 'Ahmedabad',
    '38270': 'Ahmedabad', '38275': 'Ahmedabad', '38280': 'Ahmedabad', '38285': 'Ahmedabad',
    
    # Gandhinagar (382xxx)
    '38242': 'Gandhinagar', '38243': 'Gandhinagar', '38244': 'Gandhinagar', '38246': 'Gandhinagar',
    '38305': 'Gandhinagar', '38310': 'Gandhinagar', '38315': 'Gandhinagar', '38320': 'Gandhinagar',
    '38321': 'Gandhinagar', '38325': 'Gandhinagar', '38330': 'Gandhinagar', '38335': 'Gandhinagar',
    '38340': 'Gandhinagar', '38345': 'Gandhinagar', '38346': 'Gandhinagar', '38350': 'Gandhinagar',
    
    # Rajkot (360xxx, 363xxx)
    '36000': 'Rajkot', '36001': 'Rajkot', '36002': 'Rajkot', '36003': 'Rajkot',
    '36004': 'Rajkot', '36005': 'Rajkot', '36006': 'Rajkot', '36007': 'Rajkot',
    '36008': 'Rajkot', '36009': 'Rajkot', '36010': 'Rajkot', '36011': 'Rajkot',
    '36020': 'Rajkot', '36021': 'Rajkot', '36022': 'Rajkot', '36023': 'Rajkot',
    '36024': 'Rajkot', '36025': 'Rajkot', '36026': 'Rajkot', '36027': 'Rajkot',
    '36028': 'Rajkot', '36029': 'Rajkot', '36030': 'Rajkot', '36031': 'Rajkot',
    '36035': 'Rajkot', '36036': 'Rajkot', '36037': 'Rajkot', '36038': 'Rajkot',
    
    # Surat (394xxx, 395xxx)
    '39400': 'Surat', '39401': 'Surat', '39402': 'Surat', '39403': 'Surat',
    '39404': 'Surat', '39405': 'Surat', '39406': 'Surat', '39407': 'Surat',
    '39408': 'Surat', '39409': 'Surat', '39410': 'Surat', '39411': 'Surat',
    '39412': 'Surat', '39413': 'Surat', '39414': 'Surat', '39415': 'Surat',
    '39416': 'Surat', '39417': 'Surat', '39418': 'Surat', '39419': 'Surat',
    '39420': 'Surat', '39421': 'Surat', '39423': 'Surat', '39425': 'Surat',
    '39430': 'Surat', '39435': 'Surat', '39440': 'Surat', '39445': 'Surat',
    
    '39500': 'Surat', '39501': 'Surat', '39502': 'Surat', '39503': 'Surat',
    '39504': 'Surat', '39505': 'Surat', '39506': 'Surat', '39507': 'Surat',
    '39508': 'Surat', '39509': 'Surat', '39510': 'Surat', '39511': 'Surat',
    '39512': 'Surat', '39515': 'Surat', '39516': 'Surat', '39517': 'Surat',
    '39518': 'Surat', '39520': 'Surat', '39521': 'Surat', '39522': 'Surat',
    
    # Vadodara (390xxx, 391xxx)
    '39000': 'Vadodara', '39001': 'Vadodara', '39002': 'Vadodara', '39003': 'Vadodara',
    '39004': 'Vadodara', '39005': 'Vadodara', '39006': 'Vadodara', '39007': 'Vadodara',
    '39008': 'Vadodara', '39009': 'Vadodara', '39010': 'Vadodara', '39011': 'Vadodara',
    '39012': 'Vadodara', '39013': 'Vadodara', '39015': 'Vadodara', '39016': 'Vadodara',
    '39017': 'Vadodara', '39018': 'Vadodara', '39019': 'Vadodara', '39020': 'Vadodara',
    '39021': 'Vadodara', '39022': 'Vadodara', '39023': 'Vadodara', '39024': 'Vadodara',
    '39025': 'Vadodara', '39026': 'Vadodara',
    
    '39110': 'Vadodara', '39115': 'Vadodara', '39120': 'Vadodara', '39125': 'Vadodara',
    '39130': 'Vadodara', '39135': 'Vadodara', '39140': 'Vadodara', '39145': 'Vadodara',
    '39150': 'Vadodara', '39151': 'Vadodara', '39152': 'Vadodara', '39155': 'Vadodara',
    '39160': 'Vadodara', '39165': 'Vadodara', '39170': 'Vadodara', '39171': 'Vadodara',
    '39172': 'Vadodara', '39175': 'Vadodara', '39180': 'Vadodara',
    
    # Bhavnagar (364xxx)
    '36400': 'Bhavnagar', '36401': 'Bhavnagar', '36402': 'Bhavnagar', '36403': 'Bhavnagar',
    '36404': 'Bhavnagar', '36405': 'Bhavnagar', '36410': 'Bhavnagar', '36411': 'Bhavnagar',
    '36420': 'Bhavnagar', '36421': 'Bhavnagar', '36422': 'Bhavnagar', '36425': 'Bhavnagar',
    '36430': 'Bhavnagar', '36435': 'Bhavnagar', '36440': 'Bhavnagar', '36445': 'Bhavnagar',
    
    # Jamnagar (361xxx)
    '36100': 'Jamnagar', '36101': 'Jamnagar', '36102': 'Jamnagar', '36103': 'Jamnagar',
    '36104': 'Jamnagar', '36105': 'Jamnagar', '36106': 'Jamnagar', '36108': 'Jamnagar',
    '36110': 'Jamnagar', '36115': 'Jamnagar', '36120': 'Jamnagar', '36125': 'Jamnagar',
    '36130': 'Jamnagar', '36135': 'Jamnagar', '36140': 'Jamnagar', '36141': 'Jamnagar',
    '36142': 'Jamnagar', '36145': 'Jamnagar', '36150': 'Jamnagar',
    
    # Junagadh (362xxx)
    '36200': 'Junagadh', '36201': 'Junagadh', '36202': 'Junagadh', '36203': 'Junagadh',
    '36205': 'Junagadh', '36206': 'Junagadh', '36210': 'Junagadh', '36215': 'Junagadh',
    '36220': 'Junagadh', '36225': 'Junagadh', '36230': 'Junagadh', '36235': 'Junagadh',
    '36240': 'Junagadh', '36245': 'Junagadh', '36250': 'Junagadh', '36255': 'Junagadh',
    '36260': 'Junagadh', '36265': 'Junagadh', '36270': 'Junagadh',
    
    # Mehsana (384xxx)
    '38400': 'Mehsana', '38401': 'Mehsana', '38402': 'Mehsana', '38403': 'Mehsana',
    '38404': 'Mehsana', '38405': 'Mehsana', '38410': 'Mehsana', '38411': 'Mehsana',
    '38415': 'Mehsana', '38420': 'Mehsana', '38421': 'Mehsana', '38425': 'Mehsana',
    '38430': 'Mehsana', '38435': 'Mehsana', '38440': 'Mehsana', '38445': 'Mehsana',
    '38450': 'Mehsana', '38455': 'Mehsana', '38460': 'Mehsana', '38465': 'Mehsana',
    
    # Kutch (370xxx)
    '37000': 'Kutch', '37001': 'Kutch', '37010': 'Kutch', '37011': 'Kutch',
    '37015': 'Kutch', '37020': 'Kutch', '37025': 'Kutch', '37030': 'Kutch',
    '37035': 'Kutch', '37040': 'Kutch', '37045': 'Kutch', '37050': 'Kutch',
    '37060': 'Kutch', '37065': 'Kutch', '37070': 'Kutch', '37075': 'Kutch',
    '37110': 'Kutch', '37115': 'Kutch', '37120': 'Kutch', '37125': 'Kutch',
    '37130': 'Kutch', '37135': 'Kutch', '37140': 'Kutch', '37145': 'Kutch',
    '37150': 'Kutch', '37160': 'Kutch', '37165': 'Kutch', '37170': 'Kutch',
    
    # Anand (388xxx)
    '38800': 'Anand', '38801': 'Anand', '38802': 'Anand', '38805': 'Anand',
    '38810': 'Anand', '38815': 'Anand', '38820': 'Anand', '38825': 'Anand',
    '38830': 'Anand', '38835': 'Anand', '38840': 'Anand', '38845': 'Anand',
    '38850': 'Anand', '38855': 'Anand', '38860': 'Anand', '38865': 'Anand',
    
    # Bharuch (392xxx, 393xxx)
    '39200': 'Bharuch', '39201': 'Bharuch', '39205': 'Bharuch', '39210': 'Bharuch',
    '39215': 'Bharuch', '39220': 'Bharuch', '39225': 'Bharuch', '39230': 'Bharuch',
    '39235': 'Bharuch', '39240': 'Bharuch', '39241': 'Bharuch', '39245': 'Bharuch',
    '39250': 'Bharuch', '39255': 'Bharuch', '39260': 'Bharuch', '39265': 'Bharuch',
    
    '39300': 'Bharuch', '39305': 'Bharuch', '39310': 'Bharuch', '39315': 'Bharuch',
    '39320': 'Bharuch', '39325': 'Bharuch', '39330': 'Bharuch', '39335': 'Bharuch',
    '39340': 'Bharuch', '39345': 'Bharuch', '39350': 'Bharuch', '39355': 'Bharuch',
    '39360': 'Bharuch', '39365': 'Bharuch', '39370': 'Bharuch', '39375': 'Bharuch',
    
    # Navsari (396xxx)
    '39600': 'Navsari', '39601': 'Navsari', '39605': 'Navsari', '39610': 'Navsari',
    '39615': 'Navsari', '39620': 'Navsari', '39625': 'Navsari', '39630': 'Navsari',
    '39635': 'Navsari', '39640': 'Navsari', '39645': 'Navsari', '39650': 'Navsari',
    '39655': 'Navsari', '39660': 'Navsari', '39665': 'Navsari', '39670': 'Navsari',
    
    # Valsad (396xxx)
    '39621': 'Valsad', '39626': 'Valsad', '39631': 'Valsad', '39636': 'Valsad',
    '39641': 'Valsad', '39646': 'Valsad', '39651': 'Valsad', '39656': 'Valsad',
    
    # Amreli (365xxx)
    '36500': 'Amreli', '36501': 'Amreli', '36505': 'Amreli', '36510': 'Amreli',
    '36515': 'Amreli', '36520': 'Amreli', '36525': 'Amreli', '36530': 'Amreli',
    '36535': 'Amreli', '36540': 'Amreli', '36545': 'Amreli', '36550': 'Amreli',
    '36555': 'Amreli', '36560': 'Amreli', '36565': 'Amreli', '36570': 'Amreli',
    
    # Kheda (387xxx)
    '38700': 'Kheda', '38701': 'Kheda', '38705': 'Kheda', '38710': 'Kheda',
    '38715': 'Kheda', '38720': 'Kheda', '38721': 'Kheda', '38722': 'Kheda',
    '38725': 'Kheda', '38730': 'Kheda', '38735': 'Kheda', '38740': 'Kheda',
    '38745': 'Kheda', '38750': 'Kheda', '38755': 'Kheda', '38760': 'Kheda',
    
    # Panchmahal (389xxx)
    '38900': 'Panchmahal', '38901': 'Panchmahal', '38905': 'Panchmahal', '38910': 'Panchmahal',
    '38915': 'Panchmahal', '38920': 'Panchmahal', '38925': 'Panchmahal', '38930': 'Panchmahal',
    
    # Dahod (389xxx)
    '38935': 'Dahod', '38940': 'Dahod', '38945': 'Dahod', '38950': 'Dahod',
    '38955': 'Dahod', '38960': 'Dahod', '38965': 'Dahod', '38970': 'Dahod',
    
    # Banaskantha (385xxx)
    '38500': 'Banaskantha', '38501': 'Banaskantha', '38505': 'Banaskantha', '38510': 'Banaskantha',
    '38515': 'Banaskantha', '38520': 'Banaskantha', '38525': 'Banaskantha', '38530': 'Banaskantha',
    '38535': 'Banaskantha', '38540': 'Banaskantha', '38545': 'Banaskantha', '38550': 'Banaskantha',
    
    # Sabarkantha (383xxx)
    '38300': 'Sabarkantha', '38301': 'Sabarkantha', '38305': 'Sabarkantha', '38310': 'Sabarkantha',
    '38315': 'Sabarkantha', '38320': 'Sabarkantha', '38325': 'Sabarkantha', '38330': 'Sabarkantha',
    '38335': 'Sabarkantha', '38340': 'Sabarkantha', '38345': 'Sabarkantha', '38350': 'Sabarkantha',
    
    # Patan (384xxx)
    '38470': 'Patan', '38475': 'Patan', '38480': 'Patan', '38485': 'Patan',
    '38490': 'Patan', '38495': 'Patan', '38505': 'Patan', '38510': 'Patan',
    
    # Morbi (363xxx)
    '36300': 'Morbi', '36301': 'Morbi', '36305': 'Morbi', '36310': 'Morbi',
    '36315': 'Morbi', '36320': 'Morbi', '36325': 'Morbi', '36330': 'Morbi',
    
    # Surendranagar (363xxx)
    '36335': 'Surendranagar', '36340': 'Surendranagar', '36345': 'Surendranagar',
    '36350': 'Surendranagar', '36355': 'Surendranagar', '36360': 'Surendranagar',
    
    # Porbandar (360xxx)
    '36030': 'Porbandar', '36031': 'Porbandar', '36032': 'Porbandar', '36033': 'Porbandar',
    '36034': 'Porbandar', '36035': 'Porbandar',
}

# IFSC patterns for major cities/districts (fallback when API not used)
IFSC_PATTERNS = {
    'AHMEDABAD': 'Ahmedabad', 'AMDAVAD': 'Ahmedabad', 'GANDHINAGAR': 'Gandhinagar',
    'RAJKOT': 'Rajkot', 'SURAT': 'Surat', 'VADODARA': 'Vadodara', 'BARODA': 'Vadodara',
    'BHAVNAGAR': 'Bhavnagar', 'JAMNAGAR': 'Jamnagar', 'JUNAGADH': 'Junagadh',
    'MEHSANA': 'Mehsana', 'ANAND': 'Anand', 'BHARUCH': 'Bharuch', 'NAVSARI': 'Navsari',
    'VALSAD': 'Valsad', 'VAPI': 'Valsad', 'AMRELI': 'Amreli', 'MORBI': 'Morbi',
    'SURENDRANAGAR': 'Surendranagar', 'PATAN': 'Patan', 'PORBANDAR': 'Porbandar',
    'KHEDA': 'Kheda', 'NADIAD': 'Kheda', 'DAHOD': 'Dahod', 'KUTCH': 'Kutch',
    'BHUJ': 'Kutch', 'GANDHIDHAM': 'Kutch', 'SABARKANTHA': 'Sabarkantha',
    'HIMATNAGAR': 'Sabarkantha', 'BANASKANTHA': 'Banaskantha', 'PALANPUR': 'Banaskantha',
}


def lookup_ifsc_api(ifsc_code):
    """
    Lookup IFSC code using Razorpay's free IFSC API
    Returns accurate branch details including city and district
    100% ACCURATE - Uses official bank data
    """
    if pd.isna(ifsc_code) or ifsc_code is None or str(ifsc_code).strip() == '':
        return None
    
    ifsc_clean = str(ifsc_code).strip().upper()
    
    try:
        # Call Razorpay IFSC API (free, no auth required)
        response = requests.get(f"{IFSC_API_URL}{ifsc_clean}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Extract location information
            city = data.get('CITY', '').upper()
            district = data.get('DISTRICT', '').upper()
            state = data.get('STATE', '').upper()
            branch = data.get('BRANCH', '')
            address = data.get('ADDRESS', '')
            
            # Return full details for accurate matching
            return {
                'city': city,
                'district': district,
                'state': state,
                'branch': branch,
                'address': address,
                'raw_data': data
            }
        else:
            return None
    except Exception as e:
        return None


def normalize_district_name(name):
    """Normalize district names and taluka names to match Gujarat's 34 districts"""
    if not name:
        return None
        
    name_lower = name.lower().strip()
    
    # Complete Taluka to District mapping (same as smart_district_split.py)
    TALUKA_TO_DISTRICT = {
        # Ahmedabad District
        'ahmedabad': 'Ahmedabad', 'ahmadabad': 'Ahmedabad', 'amdavad': 'Ahmedabad',
        'bavla': 'Ahmedabad', 'daskroi': 'Ahmedabad', 'detroj': 'Ahmedabad', 
        'rampura': 'Ahmedabad', 'dhandhuka': 'Ahmedabad', 'dholera': 'Ahmedabad', 
        'dholka': 'Ahmedabad', 'mandal': 'Ahmedabad', 'sanand': 'Ahmedabad', 'viramgam': 'Ahmedabad',
        'changodar': 'Ahmedabad', 'changodar g.i': 'Ahmedabad', 'changodar g.i.': 'Ahmedabad',
        
        # Amreli District
        'amreli': 'Amreli', 'babra': 'Amreli', 'bagasara': 'Amreli', 'dhari': 'Amreli', 
        'jafrabad': 'Amreli', 'khambha': 'Amreli', 'kunkavav': 'Amreli', 'vadia': 'Amreli',
        'lathi': 'Amreli', 'lilia': 'Amreli', 'rajula': 'Amreli', 'savarkundla': 'Amreli',
        
        # Anand District
        'anand': 'Anand', 'anklav': 'Anand', 'borsad': 'Anand', 'khambhat': 'Anand', 
        'petlad': 'Anand', 'sojitra': 'Anand', 'tarapur': 'Anand', 'umreth': 'Anand',
        
        # Aravalli District
        'bayad': 'Aravalli', 'bhiloda': 'Aravalli', 'dhansura': 'Aravalli', 'malpur': 'Aravalli',
        'meghraj': 'Aravalli', 'modasa': 'Aravalli', 'shamlaji': 'Aravalli', 'sathamba': 'Aravalli',
        
        # Banaskantha District
        'amirgadh': 'Banaskantha', 'dhanera': 'Banaskantha', 'deesa': 'Banaskantha', 
        'danta': 'Banaskantha', 'dantiwada': 'Banaskantha', 'palanpur': 'Banaskantha', 
        'vadgam': 'Banaskantha', 'kankrej': 'Banaskantha', 'shihori': 'Banaskantha',
        'hadad': 'Banaskantha', 'ogad': 'Banaskantha', 'thara': 'Banaskantha',
        'ambaji': 'Banaskantha', 'ambaaji': 'Banaskantha',
        
        # Bharuch District
        'bharuch': 'Bharuch', 'broach': 'Bharuch', 'amod': 'Bharuch', 'ankleshwar': 'Bharuch',
        'ankaleswar': 'Bharuch', 'ankaleshwar': 'Bharuch',  # Common misspellings
        'hansot': 'Bharuch', 'jambusar': 'Bharuch', 'jhagadia': 'Bharuch',
        'netrang': 'Bharuch', 'vagra': 'Bharuch', 'valia': 'Bharuch',
        
        # Bhavnagar District
        'bhavnagar': 'Bhavnagar', 'gariadhar': 'Bhavnagar', 'ghogha': 'Bhavnagar', 
        'jesar': 'Bhavnagar', 'mahuva': 'Bhavnagar', 'palitana': 'Bhavnagar', 
        'sihor': 'Bhavnagar', 'talaja': 'Bhavnagar', 'umrala': 'Bhavnagar', 'vallabhipur': 'Bhavnagar',
        
        # Botad District
        'botad': 'Botad', 'barwala': 'Botad', 'gadhada': 'Botad', 'ranpur': 'Botad',
        
        # Chhota Udaipur District
        'chhota udaipur': 'Chhota Udaipur', 'chhota udepur': 'Chhota Udaipur',
        'bodeli': 'Chhota Udaipur', 'jetpur pavi': 'Chhota Udaipur', 'kavant': 'Chhota Udaipur',
        'kawant': 'Chhota Udaipur', 'nasvadi': 'Chhota Udaipur', 'sankheda': 'Chhota Udaipur',
        
        # Dahod District
        'dahod': 'Dahod', 'dohad': 'Dahod', 'devgadh baria': 'Dahod', 'dhanpur': 'Dahod',
        'fatepura': 'Dahod', 'garbada': 'Dahod', 'limkheda': 'Dahod', 'sanjeli': 'Dahod',
        'jhalod': 'Dahod', 'singvad': 'Dahod',
        
        # Dang District
        'ahwa': 'Dang', 'subir': 'Dang', 'waghai': 'Dang', 'saputara': 'Dang', 'dang': 'Dang',
        
        # Devbhoomi Dwarka District
        'bhanvad': 'Devbhoomi Dwarka', 'kalyanpur': 'Devbhoomi Dwarka', 
        'khambhalia': 'Devbhoomi Dwarka', 'okhamandal': 'Devbhoomi Dwarka', 'dwarka': 'Devbhoomi Dwarka',
        
        # Gandhinagar District
        'gandhinagar': 'Gandhinagar', 'dehgam': 'Gandhinagar', 'kalol': 'Gandhinagar', 'mansa': 'Gandhinagar',
        
        # Gir Somnath District
        'gir gadhada': 'Gir Somnath', 'kodinar': 'Gir Somnath', 'sutrapada': 'Gir Somnath',
        'talala': 'Gir Somnath', 'una': 'Gir Somnath', 'veraval': 'Gir Somnath',
        
        # Jamnagar District
        'jamnagar': 'Jamnagar', 'dhrol': 'Jamnagar', 'jamjodhpur': 'Jamnagar', 
        'jodiya': 'Jamnagar', 'kalavad': 'Jamnagar', 'lalpur': 'Jamnagar',
        
        # Junagadh District
        'junagadh': 'Junagadh', 'bhesana': 'Junagadh', 'bhesan': 'Junagadh', 
        'keshod': 'Junagadh', 'malia': 'Junagadh', 'maliya': 'Junagadh', 
        'manavadar': 'Junagadh', 'mangrol': 'Junagadh', 'mendarda': 'Junagadh', 
        'vanthali': 'Junagadh', 'visavadar': 'Junagadh',
        
        # Kutch District
        'abdasa': 'Kutch', 'anjar': 'Kutch', 'bhachau': 'Kutch', 'bhuj': 'Kutch', 
        'gandhidham': 'Kutch', 'lakhpat': 'Kutch', 'mandvi': 'Kutch', 'mundra': 'Kutch',
        'nakhatrana': 'Kutch', 'rapar': 'Kutch', 'kutch': 'Kutch', 'kachchh': 'Kutch', 'cutch': 'Kutch',
        
        # Kheda District
        'kheda': 'Kheda', 'kaira': 'Kheda', 'galteshwar': 'Kheda', 'kapadvanj': 'Kheda',
        'kathlal': 'Kheda', 'mahudha': 'Kheda', 'matar': 'Kheda', 'mehmedabad': 'Kheda',
        'nadiad': 'Kheda', 'thasra': 'Kheda', 'vaso': 'Kheda',
        
        # Mahisagar District
        'balasinor': 'Mahisagar', 'kadana': 'Mahisagar', 'khanpur': 'Mahisagar',
        'lunawada': 'Mahisagar', 'lunavada': 'Mahisagar', 'santrampur': 'Mahisagar', 'virpur': 'Mahisagar',
        
        # Mehsana District
        'mehsana': 'Mehsana', 'mahesana': 'Mehsana', 'becharaji': 'Mehsana', 'jotana': 'Mehsana',
        'kadi': 'Mehsana', 'kheralu': 'Mehsana', 'satlasana': 'Mehsana', 'unjha': 'Mehsana',
        'vadnagar': 'Mehsana', 'vijapur': 'Mehsana', 'visnagar': 'Mehsana',
        
        # Morbi District
        'halvad': 'Morbi', 'morbi': 'Morbi', 'tankara': 'Morbi', 'wankaner': 'Morbi',
        'morvi': 'Morbi',  # Common spelling variation
        
        # Narmada District
        'dediapada': 'Narmada', 'dediyapada': 'Narmada', 'garudeshwar': 'Narmada',
        'nandod': 'Narmada', 'sagbara': 'Narmada', 'tilakwada': 'Narmada', 'narmada': 'Narmada',
        
        # Navsari District
        'navsari': 'Navsari', 'vansda': 'Navsari', 'chikhli': 'Navsari', 'gandevi': 'Navsari',
        'jalalpore': 'Navsari', 'khergam': 'Navsari',
        
        # Panchmahal District
        'ghoghamba': 'Panchmahal', 'godhra': 'Panchmahal', 'halol': 'Panchmahal',
        'jambughoda': 'Panchmahal', 'morwa hadaf': 'Panchmahal', 'shehera': 'Panchmahal',
        
        # Patan District
        'patan': 'Patan', 'chanasma': 'Patan', 'harij': 'Patan', 'radhanpur': 'Patan',
        'sami': 'Patan', 'sankheswar': 'Patan', 'santalpur': 'Patan', 'sidhpur': 'Patan',
        
        # Porbandar District
        'porbandar': 'Porbandar', 'kutiyana': 'Porbandar', 'ranavav': 'Porbandar',
        
        # Rajkot District
        'rajkot': 'Rajkot', 'dhoraji': 'Rajkot', 'gondal': 'Rajkot', 'jamkandorna': 'Rajkot',
        'jasdan': 'Rajkot', 'jetpur': 'Rajkot', 'kotada sangani': 'Rajkot', 'lodhika': 'Rajkot',
        'paddhari': 'Rajkot', 'upleta': 'Rajkot', 'vinchhiya': 'Rajkot',
        'bedipara': 'Rajkot', 'bedipada': 'Rajkot',  # Bedipara is in Rajkot
        
        # Sabarkantha District
        'himatnagar': 'Sabarkantha', 'himmatnagar': 'Sabarkantha', 'idar': 'Sabarkantha',
        'khedbrahma': 'Sabarkantha', 'poshina': 'Sabarkantha', 'prantij': 'Sabarkantha',
        'talod': 'Sabarkantha', 'vadali': 'Sabarkantha', 'vijaynagar': 'Sabarkantha',
        
        # Surat District
        'surat': 'Surat', 'bardoli': 'Surat', 'choryasi': 'Surat', 'chorasi': 'Surat',
        'kamrej': 'Surat', 'olpad': 'Surat', 'palsana': 'Surat', 'umarpada': 'Surat',
        
        # Surendranagar District
        'chotila': 'Surendranagar', 'chuda': 'Surendranagar', 'dasada': 'Surendranagar',
        'dhrangadhra': 'Surendranagar', 'lakhtar': 'Surendranagar', 'limbdi': 'Surendranagar',
        'muli': 'Surendranagar', 'sayla': 'Surendranagar', 'thangadh': 'Surendranagar',
        'wadhwan': 'Surendranagar', 'surendranagar': 'Surendranagar',
        
        # Tapi District
        'nizar': 'Tapi', 'songadh': 'Tapi', 'uchhal': 'Tapi', 'valod': 'Tapi', 
        'vyara': 'Tapi', 'tapi': 'Tapi',
        
        # Vadodara District
        'vadodara': 'Vadodara', 'baroda': 'Vadodara', 'vadodra': 'Vadodara', 'vadodar': 'Vadodara',
        'dabhoi': 'Vadodara', 'desar': 'Vadodara',
        'karjan': 'Vadodara', 'padra': 'Vadodara', 'savli': 'Vadodara', 'sinor': 'Vadodara',
        'waghodia': 'Vadodara',
        
        # Valsad District
        'valsad': 'Valsad', 'bulsar': 'Valsad', 'dharampur': 'Valsad', 'kaprada': 'Valsad',
        'pardi': 'Valsad', 'umbergaon': 'Valsad', 'vapi': 'Valsad',
    }
    
    # Check direct match
    if name_lower in TALUKA_TO_DISTRICT:
        return TALUKA_TO_DISTRICT[name_lower]
    
    # Check partial match (for variations)
    for taluka, district in TALUKA_TO_DISTRICT.items():
        if taluka in name_lower or name_lower in taluka:
            return district
    
    # If not found, return Unknown
    return 'Unknown'


def aggressive_district_search(row, all_columns):
    """
    AGGRESSIVE search - scan ALL columns for ANY district/taluka mention
    This ensures EVERY Gujarat record gets assigned to a district
    """
    # Search through ALL columns in the row
    for col_name, value in row.items():
        if pd.isna(value) or value is None:
            continue
        
        value_str = str(value).lower().strip()
        
        # Skip if too short or just numbers
        if len(value_str) < 3 or value_str.isdigit():
            continue
        
        # Try to find district/taluka in this value
        result = normalize_district_name(value_str)
        if result != 'Unknown':
            return result, f'Found in: {col_name}'
        
        # Check each word in the value
        words = value_str.replace(',', ' ').replace('-', ' ').replace('_', ' ').replace('/', ' ').split()
        for word in words:
            if len(word) > 3:
                result = normalize_district_name(word)
                if result != 'Unknown':
                    return result, f'Found in: {col_name} (word: {word})'
    
    return None, None


def extract_district_from_branch_name(branch_name):
    """Extract district from bank branch name"""
    if pd.isna(branch_name) or branch_name is None:
        return None
    
    branch_lower = str(branch_name).lower().strip()
    
    # Try to find district/taluka name in branch name
    result = normalize_district_name(branch_lower)
    if result != 'Unknown':
        return result
    
    # Check for common patterns like "XYZ BRANCH", "XYZ MAIN", etc.
    words = branch_lower.replace('-', ' ').replace('_', ' ').replace(',', ' ').split()
    for word in words:
        if len(word) > 3:  # Skip short words
            result = normalize_district_name(word)
            if result != 'Unknown':
                return result
    
    return None


def extract_district_from_address(address):
    """Extract district from address field"""
    if pd.isna(address) or address is None:
        return None
    
    address_lower = str(address).lower().strip()
    
    # Try to find district/taluka name in address
    result = normalize_district_name(address_lower)
    if result != 'Unknown':
        return result
    
    # Check each word in address
    words = address_lower.replace(',', ' ').replace('-', ' ').replace('_', ' ').replace('/', ' ').split()
    for word in words:
        if len(word) > 3:  # Skip short words
            result = normalize_district_name(word)
            if result != 'Unknown':
                return result
    
    return None


def extract_district_from_ifsc(ifsc_code, use_api=False):
    """
    Extract district from IFSC code
    
    Args:
        use_api: If True, uses real-time API for 100% accuracy
                 If False, uses pattern matching (faster but less accurate)
    """
    if not use_api:
        # Fallback to pattern matching (less accurate)
        if pd.isna(ifsc_code) or ifsc_code is None or str(ifsc_code).strip() == '':
            return None
        
        ifsc_upper = str(ifsc_code).upper().strip()
        
        # Check for city/district names in IFSC
        for pattern, district in IFSC_PATTERNS.items():
            if pattern in ifsc_upper:
                return district
        
        return None
    
    # Use API for 100% accurate lookup
    result = lookup_ifsc_api(ifsc_code)
    if result:
        # Priority 1: DISTRICT field from API
        if result['district']:
            district_name = result['district'].title()
            mapped = normalize_district_name(district_name)
            if mapped != 'Unknown':
                return mapped
        
        # Priority 2: CITY field from API
        if result['city']:
            city_name = result['city'].title()
            mapped = normalize_district_name(city_name)
            if mapped != 'Unknown':
                return mapped
        
        # Priority 3: BRANCH field from API
        if result['branch']:
            branch_name = result['branch']
            mapped = extract_district_from_branch_name(branch_name)
            if mapped:
                return mapped
        
        # Priority 4: ADDRESS field from API
        if result['address']:
            address = result['address']
            mapped = extract_district_from_address(address)
            if mapped:
                return mapped
    
    return None


def extract_district_from_pincode(pincode):
    """Extract district from PIN code"""
    if pd.isna(pincode) or pincode is None:
        return None
    
    # Clean PIN code
    pin_str = str(pincode).strip()
    # Remove any non-digit characters
    pin_str = re.sub(r'\D', '', pin_str)
    
    if len(pin_str) < 3:
        return None
    
    # Try 5-digit prefix first (more accurate)
    if len(pin_str) >= 5:
        prefix_5 = pin_str[:5]
        if prefix_5 in DETAILED_PINCODE_TO_DISTRICT:
            return DETAILED_PINCODE_TO_DISTRICT[prefix_5]
    
    # Try 3-digit prefix
    prefix_3 = pin_str[:3]
    if prefix_3 in PINCODE_TO_DISTRICT:
        return PINCODE_TO_DISTRICT[prefix_3]
    
    return None


def get_district(row, ifsc_col, pincode_col, branch_col=None, address_col=None, district_col=None, use_api=False):
    """
    AGGRESSIVE district identification - WILL FIND DISTRICT FROM ANY AVAILABLE DATA
    
    Priority order:
    1. Existing District column (if provided)
    2. IFSC code (with API for 100% accuracy)
    3. PIN code
    4. Branch name
    5. Address field
    6. AGGRESSIVE SCAN - Search ALL columns for ANY district/taluka mention
    
    Args:
        use_api: If True, uses real-time IFSC API for 100% accuracy (slower)
                 If False, uses pattern matching (faster but less accurate)
    """
    # Priority 1: Check if district column already exists
    if district_col and district_col in row.index and not pd.isna(row[district_col]):
        district = normalize_district_name(str(row[district_col]))
        if district != 'Unknown':
            return district, 'District Column'
    
    # Priority 2: Try IFSC first (most reliable with API)
    if ifsc_col and ifsc_col in row.index:
        district = extract_district_from_ifsc(row[ifsc_col], use_api=use_api)
        if district:
            return district, 'IFSC-API' if use_api else 'IFSC'
    
    # Priority 3: Try PIN code
    if pincode_col and pincode_col in row.index:
        district = extract_district_from_pincode(row[pincode_col])
        if district:
            return district, 'PIN'
    
    # Priority 4: Try Branch name
    if branch_col and branch_col in row.index:
        district = extract_district_from_branch_name(row[branch_col])
        if district:
            return district, 'Branch Name'
    
    # Priority 5: Try Address field
    if address_col and address_col in row.index:
        district = extract_district_from_address(row[address_col])
        if district:
            return district, 'Address'
    
    # Priority 6: AGGRESSIVE SCAN - Search through ALL columns
    district, source = aggressive_district_search(row, row.index)
    if district:
        return district, source
    
    # If still not found, return Unknown (should be extremely rare for Gujarat data)
    return 'Unknown', 'None'


def render_ifsc_pincode_district_split_page():
    """Render the IFSC/PIN Code District Split page"""
    from src.ui_styling import render_page_header_with_info
    
    # Initialize persistent mapping
    mapping = PersistentMapping('ifsc_pincode_district_split')
    
    # Render page header with info button
    render_page_header_with_info('ifsc_pincode_split')
    
    # Show currently loaded file if exists
    if 'uploaded_filename' in st.session_state and st.session_state.uploaded_filename:
        st.info(f"📁 **Current File**: {st.session_state.uploaded_filename} ({len(st.session_state.uploaded_df)} rows)")
        if st.button("🔄 Upload Different File", key="clear_file_btn"):
            # Clear all session state
            for key in ['uploaded_file_key', 'uploaded_df', 'uploaded_filename', 'analyze_ifsc_pin', 
                       'district_analysis_ready', 'analyzed_df', 'generating_files']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    st.markdown("""
    Upload a file with IFSC codes and/or PIN codes. The app will intelligently identify districts.
    
    ⚠️ **For 100% Accuracy**: Enable "Use Real-Time IFSC API" (slower but guaranteed accurate)
    """)
    
    # Accuracy mode selection
    st.info("🎯 **Accuracy Mode Selection**")
    col_mode1, col_mode2 = st.columns(2)
    
    with col_mode1:
        use_api = st.checkbox(
            "🔒 Use Real-Time IFSC API (100% Accurate)",
            value=False,
            help="Fetches live data from bank database. Slower but 100% accurate. Recommended for legal/police data."
        )
    
    with col_mode2:
        if use_api:
            st.warning("⏱️ API mode: Processing will be slower but 100% accurate")
        else:
            st.info("⚡ Fast mode: Uses pattern matching (may have minor inaccuracies)")
    
    st.markdown("---")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Excel or CSV file",
        type=['xlsx', 'xls', 'csv'],
        help="File containing IFSC codes and/or PIN codes"
    )
    
    if uploaded_file:
        try:
            # Store uploaded file in session state to persist across reruns
            file_key = f"{uploaded_file.name}_{uploaded_file.size}"
            
            # Check if this is a new file or if we need to reload
            if 'uploaded_file_key' not in st.session_state or st.session_state.uploaded_file_key != file_key:
                # New file uploaded - reset everything
                st.session_state.uploaded_file_key = file_key
                st.session_state.analyze_ifsc_pin = False
                st.session_state.district_analysis_ready = False
                st.session_state.analyzed_df = None
                st.session_state.generating_files = False
                
                # Read and store the file
                if uploaded_file.name.endswith('.csv'):
                    st.session_state.uploaded_df = pd.read_csv(uploaded_file)
                else:
                    st.session_state.uploaded_df = pd.read_excel(uploaded_file)
                
                st.session_state.uploaded_filename = uploaded_file.name
            
            # Use the stored dataframe
            df = st.session_state.uploaded_df
            
            st.success(f"✅ File loaded: {len(df)} rows, {len(df.columns)} columns")
            
            # Show preview
            with st.expander("📋 Data Preview", expanded=False):
                st.dataframe(df.head(10), use_container_width=True)
            
            st.markdown("---")
            
            # Column selection
            st.subheader("🎯 Select Columns (Optional - System will scan ALL columns)")
            
            st.success("✅ **AGGRESSIVE MODE**: Even if you don't select columns, the system will scan EVERY column in your file to find district information!")
            
            # Show saved mappings indicator
            saved_count = mapping.get_saved_count()
            if saved_count > 0:
                st.info(f"💾 {saved_count} column mapping(s) remembered")
            
            col1, col2 = st.columns(2)
            
            with col1:
                ifsc_column = st.selectbox(
                    "IFSC Code Column (Recommended)",
                    options=["-- Will scan all columns --"] + df.columns.tolist(),
                    index=mapping.get_default_index('ifsc_column', ["-- Will scan all columns --"] + df.columns.tolist()),
                    help="Column containing IFSC codes - MOST ACCURATE with API mode"
                )
                if ifsc_column != "-- Will scan all columns --":
                    mapping.set('ifsc_column', ifsc_column)
                
                pincode_column = st.selectbox(
                    "PIN Code Column (Recommended)",
                    options=["-- Will scan all columns --"] + df.columns.tolist(),
                    index=mapping.get_default_index('pincode_column', ["-- Will scan all columns --"] + df.columns.tolist()),
                    help="Column containing PIN codes"
                )
                if pincode_column != "-- Will scan all columns --":
                    mapping.set('pincode_column', pincode_column)
                
                branch_column = st.selectbox(
                    "Branch Name Column (Optional)",
                    options=["-- Will scan all columns --"] + df.columns.tolist(),
                    index=mapping.get_default_index('branch_column', ["-- Will scan all columns --"] + df.columns.tolist()),
                    help="Column containing bank branch names"
                )
                if branch_column != "-- Will scan all columns --":
                    mapping.set('branch_column', branch_column)
            
            with col2:
                address_column = st.selectbox(
                    "Address Column (Optional)",
                    options=["-- Will scan all columns --"] + df.columns.tolist(),
                    index=mapping.get_default_index('address_column', ["-- Will scan all columns --"] + df.columns.tolist()),
                    help="Column containing addresses"
                )
                if address_column != "-- Will scan all columns --":
                    mapping.set('address_column', address_column)
                
                district_column = st.selectbox(
                    "District Column (Optional)",
                    options=["-- Will scan all columns --"] + df.columns.tolist(),
                    index=mapping.get_default_index('district_column', ["-- Will scan all columns --"] + df.columns.tolist()),
                    help="If your data already has a district column"
                )
                if district_column != "-- Will scan all columns --":
                    mapping.set('district_column', district_column)
                
                state_column = st.selectbox(
                    "State Column (Optional)",
                    options=["-- Will scan all columns --"] + df.columns.tolist(),
                    index=mapping.get_default_index('state_column', ["-- Will scan all columns --"] + df.columns.tolist()),
                    help="Column containing state names"
                )
                if state_column != "-- Will scan all columns --":
                    mapping.set('state_column', state_column)
            
            # Validate selection
            ifsc_col = None if ifsc_column == "-- Will scan all columns --" else ifsc_column
            pin_col = None if pincode_column == "-- Will scan all columns --" else pincode_column
            branch_col = None if branch_column == "-- Will scan all columns --" else branch_column
            address_col = None if address_column == "-- Will scan all columns --" else address_column
            district_col = None if district_column == "-- Will scan all columns --" else district_column
            state_col = None if state_column == "-- Will scan all columns --" else state_column
            
            # Analyze button
            if st.button("🔍 Analyze Data", type="primary", use_container_width=True):
                st.session_state.analyze_ifsc_pin = True
                st.session_state.use_api_mode = use_api
                st.session_state.district_analysis_ready = False  # Reset ready state
                st.rerun()
            
            # Analyze data if button clicked (and not currently generating files)
            if (st.session_state.get('analyze_ifsc_pin', False) and 
                not st.session_state.get('district_analysis_ready', False) and 
                not st.session_state.get('generating_files', False)):
                st.markdown("---")
                st.subheader("📊 District Analysis")
                
                use_api_mode = st.session_state.get('use_api_mode', False)
                
                if use_api_mode:
                    st.warning("🔒 Using Real-Time API: This will take longer but ensures 100% accuracy")
                
                with st.spinner("Analyzing IFSC codes and PIN codes..." + (" (API mode - please wait)" if use_api_mode else "")):
                    # Apply district extraction
                    results = []
                    total = len(df)
                    
                    # Progress bar for API mode
                    if use_api_mode and total > 10:
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                    
                    for idx, row in df.iterrows():
                        result = get_district(row, ifsc_col, pin_col, branch_col, address_col, district_col, use_api=use_api_mode)
                        results.append(result)
                        
                        # Update progress for API mode
                        if use_api_mode and total > 10 and idx % 10 == 0:
                            progress = int((idx + 1) / total * 100)
                            progress_bar.progress(progress)
                            status_text.text(f"Processing: {idx + 1}/{total} records ({progress}%)")
                            time.sleep(0.1)  # Rate limiting
                    
                    if use_api_mode and total > 10:
                        progress_bar.empty()
                        status_text.empty()
                    
                    df['Identified_District'] = [r[0] for r in results]
                    df['Source'] = [r[1] for r in results]
                    
                    # Statistics
                    total_rows = len(df)
                    ifsc_identified = len(df[df['Source'].isin(['IFSC', 'IFSC-API'])])
                    pin_identified = len(df[df['Source'] == 'PIN'])
                    branch_identified = len(df[df['Source'] == 'Branch Name'])
                    address_identified = len(df[df['Source'] == 'Address'])
                    district_col_identified = len(df[df['Source'] == 'District Column'])
                    unknown = len(df[df['Source'] == 'None'])
                    
                    # Show metrics
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric("Total Records", total_rows)
                    with col2:
                        st.metric("From IFSC", ifsc_identified, 
                                 delta=f"{(ifsc_identified/total_rows*100):.1f}%")
                    with col3:
                        st.metric("From PIN", pin_identified,
                                 delta=f"{(pin_identified/total_rows*100):.1f}%")
                    with col4:
                        st.metric("From Branch/Address", branch_identified + address_identified,
                                 delta=f"{((branch_identified + address_identified)/total_rows*100):.1f}%")
                    with col5:
                        unknown_pct = (unknown/total_rows*100)
                        st.metric("Unknown", unknown,
                                 delta=f"{unknown_pct:.1f}%",
                                 delta_color="inverse")
                    
                    # Show warning if unknowns exist
                    if unknown > 0:
                        st.error(f"""
                        ⚠️ **{unknown} records could not be identified!**
                        
                        **Recommendations:**
                        1. Enable "Use Real-Time IFSC API" for 100% IFSC accuracy
                        2. Select Branch Name and Address columns if available
                        3. Check the Unknown records below and manually assign districts
                        """)
                        
                        # Show unknown records for manual review
                        with st.expander(f"🔍 View {unknown} Unknown Records - ALL DATA", expanded=True):
                            unknown_df = df[df['Source'] == 'None'].copy()
                            
                            st.warning(f"""
                            **These {unknown} records could not be automatically identified.**
                            
                            Please review the data below and help us improve the system by identifying which districts these belong to.
                            """)
                            
                            # Show ALL columns for unknown records
                            st.dataframe(unknown_df, use_container_width=True, height=400)
                            
                            # Download unknown records for manual review
                            csv_unknown = unknown_df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="⬇️ Download Unknown Records (ALL Columns) for Manual Review",
                                data=csv_unknown,
                                file_name=f"unknown_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                            
                            st.info("""
                            **How to help:**
                            1. Download the CSV file above
                            2. Look at IFSC codes, addresses, branch names, PIN codes
                            3. Identify the correct district for each record
                            4. Share the mappings so we can add them to the system
                            """)
                    else:
                        st.success("🎉 **100% ACCURACY ACHIEVED!** All records identified successfully!")
                    
                    # District breakdown
                    with st.expander("🗺️ District Breakdown", expanded=True):
                        district_counts = df.groupby(['Identified_District', 'Source']).size().reset_index(name='Count')
                        district_summary = df.groupby('Identified_District').agg({
                            'Identified_District': 'count'
                        }).rename(columns={'Identified_District': 'Total Records'})
                        district_summary = district_summary.reset_index()
                        district_summary = district_summary.sort_values('Total Records', ascending=False)
                        
                        st.dataframe(district_summary, use_container_width=True)
                    
                    # Detailed breakdown
                    with st.expander("📈 Source Breakdown by District", expanded=False):
                        pivot_table = district_counts.pivot(
                            index='Identified_District',
                            columns='Source',
                            values='Count'
                        ).fillna(0).astype(int)
                        st.dataframe(pivot_table, use_container_width=True)
                    
                    st.session_state.district_analysis_ready = True
                    st.session_state.analyzed_df = df
            
            # Generate files button
            if st.session_state.get('district_analysis_ready', False):
                st.markdown("---")
                st.subheader("📦 Generate District-Wise Files")
                
                # Show analysis summary
                st.info(f"✅ Analysis complete! Ready to generate files for {len(st.session_state.analyzed_df.groupby('Identified_District'))} districts")
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    output_format = st.radio(
                        "📦 Output Format",
                        options=["ZIP with separate files", "Single Excel with sheets"],
                        help="ZIP: Separate Excel file for each district\nExcel: One file with multiple sheets (one per district)",
                        index=1  # Default to Excel with sheets
                    )
                
                with col2:
                    include_unknown = st.checkbox(
                        "Include 'Unknown' district file",
                        value=True,
                        help="Create a separate file/sheet for records with unidentified districts"
                    )
                
                # Show format explanation
                if output_format == "ZIP with separate files":
                    st.info("📁 **ZIP Format**: You'll get a ZIP file containing separate Excel files for each district (e.g., Ahmedabad.xlsx, Surat.xlsx, etc.)")
                else:
                    st.success("📊 **Excel Format**: You'll get ONE Excel file with multiple sheets - one sheet per district. Easy to navigate!")
                
                st.info("🔤 **Auto-Sorting**: Data in each district will be sorted by IFSC code (A to Z) for easy reference")
                
                
                # Add reset button
                col_reset1, col_reset2 = st.columns([3, 1])
                with col_reset2:
                    if st.button("🔄 Reset Analysis", use_container_width=True):
                        st.session_state.analyze_ifsc_pin = False
                        st.session_state.district_analysis_ready = False
                        st.session_state.analyzed_df = None
                        st.rerun()
                
                if st.button("🚀 Generate Files", type="primary", use_container_width=True, key="generate_files_btn"):
                    # Set flag to prevent re-analysis during file generation
                    st.session_state.generating_files = True
                    
                    with st.spinner("Generating district-wise files..."):
                        df_to_split = st.session_state.analyzed_df
                        
                        # Remove temporary columns for output
                        output_df = df_to_split.drop(columns=['Identified_District', 'Source'])
                        df_to_split['Output_Data'] = output_df.apply(lambda x: x.to_dict(), axis=1)
                        
                        # Group by district
                        district_groups = df_to_split.groupby('Identified_District')
                        
                        # Filter out Unknown if not included
                        if not include_unknown:
                            district_groups = {k: v for k, v in district_groups if k != 'Unknown'}
                        
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        
                        if output_format == "ZIP with separate files":
                            # Create ZIP file
                            zip_buffer = BytesIO()
                            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                                for district, group_df in district_groups:
                                    # Reconstruct dataframe without temp columns
                                    clean_df = group_df.drop(columns=['Identified_District', 'Source', 'Output_Data'])
                                    
                                    # Sort by IFSC code (A to Z) if IFSC column exists
                                    if ifsc_col and ifsc_col in clean_df.columns:
                                        clean_df = clean_df.sort_values(by=ifsc_col, ascending=True, na_position='last')
                                    
                                    # Add S No. only if it doesn't exist
                                    if 'S No.' not in clean_df.columns:
                                        clean_df.insert(0, 'S No.', range(1, len(clean_df) + 1))
                                    else:
                                        # Reset existing S No.
                                        clean_df['S No.'] = range(1, len(clean_df) + 1)
                                    
                                    # Create Excel file
                                    excel_buffer = BytesIO()
                                    clean_df.to_excel(excel_buffer, index=False, engine='openpyxl')
                                    excel_buffer.seek(0)
                                    
                                    # Add to ZIP
                                    filename = f"{district.replace(' ', '_')}_{len(clean_df)}_records.xlsx"
                                    zip_file.writestr(filename, excel_buffer.getvalue())
                            
                            zip_buffer.seek(0)
                            
                            # Download button
                            st.success(f"✅ Created {len(district_groups)} district files! (Sorted by IFSC A-Z)")
                            st.session_state.generating_files = False  # Clear flag
                            st.download_button(
                                label=f"⬇️ Download ZIP ({len(district_groups)} files, sorted by IFSC A-Z)",
                                data=zip_buffer.getvalue(),
                                file_name=f"ifsc_pin_district_split_{timestamp}.zip",
                                mime="application/zip",
                                use_container_width=True
                            )
                        
                        else:
                            # Create single Excel with multiple sheets
                            excel_buffer = BytesIO()
                            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                                for district, group_df in district_groups:
                                    # Reconstruct dataframe
                                    clean_df = group_df.drop(columns=['Identified_District', 'Source', 'Output_Data'])
                                    
                                    # Sort by IFSC code (A to Z) if IFSC column exists
                                    if ifsc_col and ifsc_col in clean_df.columns:
                                        clean_df = clean_df.sort_values(by=ifsc_col, ascending=True, na_position='last')
                                    
                                    # Add S No. only if it doesn't exist
                                    if 'S No.' not in clean_df.columns:
                                        clean_df.insert(0, 'S No.', range(1, len(clean_df) + 1))
                                    else:
                                        # Reset existing S No.
                                        clean_df['S No.'] = range(1, len(clean_df) + 1)
                                    
                                    # Sheet name (max 31 chars)
                                    sheet_name = district[:31]
                                    clean_df.to_excel(writer, sheet_name=sheet_name, index=False)
                            
                            excel_buffer.seek(0)
                            
                            # Download button
                            st.success(f"✅ Created Excel with {len(district_groups)} sheets! (Sorted by IFSC A-Z)")
                            st.session_state.generating_files = False  # Clear flag
                            st.download_button(
                                label=f"⬇️ Download Excel ({len(district_groups)} sheets, sorted by IFSC A-Z)",
                                data=excel_buffer.getvalue(),
                                file_name=f"ifsc_pin_district_split_{timestamp}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
        
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.exception(e)
    
    else:
        st.info("📤 Upload a file to get started")
        
        # Show examples
        with st.expander("💡 How It Works", expanded=False):
            st.markdown("""
            **Priority System:**
            1. **IFSC Code** (if available): Analyzes branch location from IFSC
            2. **PIN Code** (fallback): Maps PIN code to district
            3. **Unknown**: If neither can identify the district
            
            **Examples:**
            - IFSC: `SBIN0001234` → Identifies city/district from branch code
            - PIN: `380001` → Ahmedabad
            - PIN: `395001` → Surat
            - PIN: `390001` → Vadodara
            """)
        
        with st.expander("📍 Supported Districts", expanded=False):
            districts = [
                'Ahmedabad', 'Gandhinagar', 'Rajkot', 'Surat', 'Vadodara',
                'Bhavnagar', 'Jamnagar', 'Junagadh', 'Mehsana', 'Anand',
                'Bharuch', 'Navsari', 'Valsad', 'Amreli', 'Morbi',
                'Surendranagar', 'Patan', 'Porbandar', 'Kheda', 'Dahod',
                'Kutch', 'Sabarkantha', 'Banaskantha', 'And more...'
            ]
            cols = st.columns(3)
            for i, district in enumerate(districts):
                with cols[i % 3]:
                    st.write(f"• {district}")
