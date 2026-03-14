"""
Persistent Column Mapping Module
Centralized system for remembering column selections across all pages forever.
"""

import json
from pathlib import Path
import streamlit as st


class PersistentMapping:
    """Manages persistent column mappings for a specific page."""
    
    def __init__(self, page_name):
        """
        Initialize persistent mapping for a page.
        
        Args:
            page_name: Unique identifier for the page (e.g., 'transaction_matcher', 'disputed_amount')
        """
        self.page_name = page_name
        self.mappings_file = Path.home() / '.kiro' / f'{page_name}_mappings.json'
        self.session_key = f'{page_name}_saved_mappings'
        
        # Initialize session state if not exists
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = self.load()
    
    def load(self):
        """Load saved column mappings from file."""
        try:
            if self.mappings_file.exists():
                with open(self.mappings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            st.warning(f"Could not load saved mappings: {e}")
        
        return {}
    
    def save(self, mappings=None):
        """
        Save column mappings to file.
        
        Args:
            mappings: Dictionary of mappings to save. If None, uses session state.
        """
        try:
            # Create directory if it doesn't exist
            self.mappings_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Use provided mappings or get from session state
            data = mappings if mappings is not None else st.session_state.get(self.session_key, {})
            
            with open(self.mappings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            st.warning(f"Could not save mappings: {e}")
    
    def get(self, key, default=None):
        """Get a saved mapping value."""
        return st.session_state.get(self.session_key, {}).get(key, default)
    
    def set(self, key, value):
        """Set a mapping value and save immediately."""
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {}
        
        st.session_state[self.session_key][key] = value
        self.save()
    
    def get_saved_count(self):
        """Get count of saved mappings."""
        return sum(1 for v in st.session_state.get(self.session_key, {}).values() if v is not None and v != '')
    
    def clear(self):
        """Clear all saved mappings."""
        st.session_state[self.session_key] = {}
        self.save({})
    
    def get_default_index(self, column_name, available_columns, include_select_option=True):
        """
        Get the default index for a selectbox based on saved mapping.
        
        Args:
            column_name: Key for the saved mapping
            available_columns: List of available column options
            include_select_option: Whether the list includes "-- Select Column --" at index 0
        
        Returns:
            Index to use as default in selectbox
        """
        saved_value = self.get(column_name)
        
        if saved_value and saved_value in available_columns:
            return available_columns.index(saved_value)
        
        return 0  # Default to first option (usually "-- Select Column --")
