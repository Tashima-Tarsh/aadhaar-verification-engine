"""
Address normalizer — merged: user's state abbreviation map + placeholder cleaning
                              + mine's full Indian state list + pincode validation.
"""
import re
from typing import Optional, Dict, Any
from dataclasses import dataclass


FULL_STATES = {
    "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
    "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka",
    "kerala", "madhya pradesh", "maharashtra", "manipur", "meghalaya", "mizoram",
    "nagaland", "odisha", "punjab", "rajasthan", "sikkim", "tamil nadu",
    "telangana", "tripura", "uttar pradesh", "uttarakhand", "west bengal",
    "andaman and nicobar islands", "chandigarh", "dadra and nagar haveli",
    "daman and diu", "delhi", "jammu and kashmir", "ladakh", "lakshadweep", "puducherry",
}

STATE_ABBREVIATIONS: Dict[str, str] = {
    "UP": "Uttar Pradesh", "U.P.": "Uttar Pradesh",
    "MH": "Maharashtra",   "MAH": "Maharashtra",
    "DL": "Delhi",         "DEL": "Delhi",
    "KA": "Karnataka",     "KAR": "Karnataka",
    "TN": "Tamil Nadu",    "T.N.": "Tamil Nadu",
    "GJ": "Gujarat",       "GUJ": "Gujarat",
    "RJ": "Rajasthan",     "RAJ": "Rajasthan",
    "PB": "Punjab",
    "HR": "Haryana",
    "HP": "Himachal Pradesh",
    "JK": "Jammu and Kashmir",
    "WB": "West Bengal",
    "OR": "Odisha",        "OD": "Odisha",
    "AP": "Andhra Pradesh",
    "TS": "Telangana",     "TG": "Telangana",
    "KL": "Kerala",
    "MP": "Madhya Pradesh",
    "BR": "Bihar",
    "JH": "Jharkhand",
    "AS": "Assam",
    "UK": "Uttarakhand",   "UA": "Uttarakhand",
    "CG": "Chhattisgarh",  "CT": "Chhattisgarh",
    "GA": "Goa",
    "MN": "Manipur",
    "ML": "Meghalaya",
    "MZ": "Mizoram",
    "NL": "Nagaland",
    "TR": "Tripura",
    "SK": "Sikkim",
    "AR": "Arunachal Pradesh",
}

PLACEHOLDER_VALUES = {"N/A", "NA", "NIL", "-", "NONE", "NULL", "N.A.", "NOT AVAILABLE"}


@dataclass
class NormalizedAddress:
    house: Optional[str]
    street: Optional[str]
    landmark: Optional[str]
    city: Optional[str]
    district: Optional[str]
    state: Optional[str]
    pincode: Optional[str]
    full: Optional[str]
    status: str  # COMPLETE | PARTIAL | UNAVAILABLE


class AddressNormalizer:

    def normalize(self, address_str: Optional[str]) -> str:
        if not address_str:
            return ""
        address = " ".join(address_str.split())
        address = re.sub(r'[^\w\s,\-]', '', address)
        return address.title()

    def standardize_state(self, state_name: Optional[str]) -> Optional[str]:
        if not state_name:
            return None
        clean = state_name.strip().upper()
        # Check abbreviation map first
        if clean in STATE_ABBREVIATIONS:
            return STATE_ABBREVIATIONS[clean]
        # Fuzzy match against full names
        lower = state_name.strip().lower()
        for s in FULL_STATES:
            if s in lower or lower in s:
                return s.title()
        return state_name.strip().title()

    def extract_pincode(self, address_str: Optional[str]) -> Optional[str]:
        if not address_str:
            return None
        match = re.search(r'\b(\d{6})\b', address_str)
        return match.group(1) if match else None

    def clean_placeholder(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        if value.strip().upper() in PLACEHOLDER_VALUES:
            return None
        clean = re.sub(r'\s+', ' ', value.strip())
        clean = re.sub(r'[^\w\s,.\-/]', '', clean)
        return clean if clean else None

    def normalize_full(self, raw: Dict[str, Any]) -> NormalizedAddress:
        house    = self.clean_placeholder(raw.get("house") or raw.get("co"))
        street   = self.clean_placeholder(raw.get("street"))
        landmark = self.clean_placeholder(raw.get("landmark") or raw.get("lm"))
        city     = self.clean_placeholder(raw.get("city") or raw.get("vtc") or raw.get("loc") or raw.get("subdist"))
        district = self.clean_placeholder(raw.get("district") or raw.get("dist"))
        state    = self.standardize_state(raw.get("state"))
        pincode  = raw.get("pincode") or raw.get("pc")
        if pincode:
            pincode = re.sub(r'\D', '', str(pincode))
            pincode = pincode if len(pincode) == 6 else None

        parts = [p for p in [house, street, landmark, city, district, state, pincode] if p]
        full = ", ".join(parts) if parts else None

        required = [city, state, pincode]
        filled = sum(1 for f in required if f)
        status = "COMPLETE" if filled == 3 else ("PARTIAL" if filled > 0 or any([house, street, district]) else "UNAVAILABLE")

        return NormalizedAddress(
            house=house, street=street, landmark=landmark,
            city=city, district=district, state=state,
            pincode=pincode, full=full, status=status,
        )
