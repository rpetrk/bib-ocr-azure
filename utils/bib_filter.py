# utils/bib_filter.py

import re

class BibFilter:
    def __init__(self, mode="simple"):
        self.mode = mode.lower()

    def extract_bibs(self, text):
        if self.mode == "simple":
            return self._simple_filter(text)
        elif self.mode == "alphanumeric":
            return self._alphanumeric_filter(text)
        else:
            raise ValueError(f"Unsupported bib filter mode: {self.mode}")

    def _simple_filter(self, text):
        # Allow 1 to 5 digit numbers only (e.g., 7, 88, 105, 1234)
        return sorted(set(
            word for word in text.split()
            if re.match(r"^\d{1,5}$", word)
        ))

    def _alphanumeric_filter(self, text):
        # Allow formats like: B1234, W-5123, A1, Z-88
        return sorted(set(
            word for word in text.split()
            if re.match(r"^[A-Z]?-?\d{1,5}$", word, re.IGNORECASE)
        ))
