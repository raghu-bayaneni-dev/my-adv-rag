import re
from typing import Tuple


class PIISanitizer:
    """
    Regex-based black-box PII sanitizer.
    Redacts Social Security Numbers (SSN), Credit Cards, and sensitive token formats.
    """
    def __init__(self):
        # SSN: ###-##-####
        self.ssn_pattern = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
        # Credit Cards: 13-16 digit numbers with hyphens/spaces
        self.cc_pattern = re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b')

    def sanitize(self, text: str) -> Tuple[str, bool]:
        """
        Redacts detected PII patterns and returns (sanitized_text, pii_was_found).
        """
        pii_found = False
        sanitized = text

        if self.ssn_pattern.search(sanitized):
            sanitized = self.ssn_pattern.sub("[REDACTED_SSN]", sanitized)
            pii_found = True

        if self.cc_pattern.search(sanitized):
            sanitized = self.cc_pattern.sub("[REDACTED_CARD]", sanitized)
            pii_found = True

        return sanitized, pii_found
