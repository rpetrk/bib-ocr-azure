# tests/test_bib_filter.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.bib_filter import BibFilter

def test_simple_mode():
    bf = BibFilter(mode="simple")
    text = "7 88 123 99999 00001 ABCD"
    assert bf.extract_bibs(text) == ['00001', '123', '7', '88', '99999']

def test_alphanumeric_mode():
    bf = BibFilter(mode="alphanumeric")
    text = "A12 B1234 99999 Z-9 notabib 12 8"
    assert bf.extract_bibs(text) == ['12', '8', '99999', 'A12', 'B1234', 'Z-9']
