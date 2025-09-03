import re
from typing import List, Tuple

# Precompiled regexes for Indian PII
PATTERNS = {
    "AADHAAR": re.compile(r"\b(?:\d[\s-]?){12}\b"),
    "PAN": re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),
    "PHONE": re.compile(r"\b(?:\+?91[\s-]?)?[6-9]\d{9}\b"),
    "EMAIL": re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    "DATE": re.compile(r"\b(?:0?[1-9]|[12][0-9]|3[01])[-/](?:0?[1-9]|1[0-2])[-/](?:19|20)\d\d\b"),
    "ADDRESS": re.compile(r"\b(?:[A-Za-z0-9]{3,},?\s?)+\b"),  # Basic address pattern, extend as needed
    "NAME": re.compile(r"\b[A-Z][a-z]+(?: [A-Z][a-z]+)+\b"),  # Simple full name pattern (improvable)
}

def get_rules(selected_fields: List[str]) -> List[Tuple[str, re.Pattern]]:
    return [(label, PATTERNS[label]) for label in selected_fields if label in PATTERNS]
