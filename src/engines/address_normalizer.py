import re
from typing import Optional, Dict

class AddressNormalizer:
    def __init__(self):
        # Mapping of common abbreviations to official state names
        self.state_map = {
            "UP": "Uttar Pradesh",
            "U.P.": "Uttar Pradesh",
            "MH": "Maharashtra",
            "DL": "Delhi",
            "KA": "Karnataka",
            "TN": "Tamil Nadu",
            # Add more as needed
        }

    def normalize(self, address_str: str) -> str:
        if not address_str:
            return ""

        # ADDR-01: Remove duplicate whitespace
        address = " ".join(address_str.split())

        # ADDR-05: Remove special characters except comma, hyphen
        address = re.sub(r'[^\w\s,\-]', '', address)

        # ADDR-02: Capitalize first letter of each word
        address = address.title()

        return address

    def extract_pincode(self, address_str: str) -> Optional[str]:
        # ADDR-04: Validate and format PIN code (6 digits)
        match = re.search(r'\b\d{6}\b', address_str)
        return match.group(0) if match else None

    def standardize_state(self, state_name: str) -> str:
        # ADDR-03: Standardize state names
        if not state_name:
            return ""
        
        clean_state = state_name.strip().upper()
        return self.state_map.get(clean_state, state_name.title())

    def clean_placeholders(self, value: Optional[str]) -> Optional[str]:
        # ADDR-07: Remove null / empty field placeholders
        placeholders = {"N/A", "NA", "NIL", "-", "NONE"}
        if value and value.strip().upper() in placeholders:
            return None
        return value
