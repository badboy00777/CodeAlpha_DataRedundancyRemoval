import re
import pytest
from app.classifier import (
    normalize_name, normalize_email, normalize_phone, build_normalized,
    fingerprint, name_similarity, find_duplicate, classify,
)

# ---------- normalize_name ----------
def test_name_is_lowercased_and_spaces_collapsed():
    assert normalize_name("  Ali    KHAN ") == "ali khan"

def test_name_none_becomes_empty():
    assert normalize_name(None) == ""

# ---------- normalize_email ----------
def test_email_is_lowercased():
    assert normalize_email("ALI@Example.COM") == "ali@example.com"

def test_gmail_dots_and_plus_tag_removed():
    assert normalize_email("a.li+news@gmail.com") == "ali@gmail.com"

def test_googlemail_treated_as_gmail():
    assert normalize_email("ali@googlemail.com") == "ali@gmail.com"

def test_non_gmail_keeps_dots_and_plus():
    # Assumption: only Gmail ignores dots/plus. Other providers may not.
    assert normalize_email("a.li+x@example.com") == "a.li+x@example.com"

# ---------- normalize_phone ----------
@pytest.mark.parametrize("raw", ["0300-1234567", "+92 300 1234567", "0092 300 1234567", "03001234567"])
def test_pakistani_phone_formats_become_same_number(raw):
    assert normalize_phone(raw) == "923001234567"

def test_international_phone_keeps_digits_only():
    assert normalize_phone("+1 (415) 555-2671") == "14155552671"

# ---------- fingerprint (SHA-256) ----------
def test_fingerprint_is_64_hex_chars():
    fp = fingerprint(build_normalized({"full_name": "Ali Khan", "email": "ali@example.com", "phone": "03001234567"}))
    assert re.fullmatch(r"[0-9a-f]{64}", fp)

def test_fingerprint_same_for_differently_formatted_same_person():
    a = {"full_name": "Ali  Khan", "email": "ALI@example.com", "phone": "0300-1234567"}
    b = {"full_name": "ali khan", "email": "ali@example.com", "phone": "+92 300 1234567"}
    assert fingerprint(build_normalized(a)) == fingerprint(build_normalized(b))

def test_fingerprint_differs_for_different_email():
    a = {"full_name": "Ali Khan", "email": "ali@example.com", "phone": "03001234567"}
    b = {"full_name": "Ali Khan", "email": "other@example.com", "phone": "03001234567"}
    assert fingerprint(build_normalized(a)) != fingerprint(build_normalized(b))

# ---------- name_similarity ----------
def test_identical_names_score_one():
    assert name_similarity("Ali Khan", "ali  khan") == 1.0

def test_small_typo_scores_high():
    assert name_similarity("ali khan", "ali khann") > 0.85

def test_different_names_score_low():
    assert name_similarity("ali khan", "sara ahmed") < 0.5

# ---------- classify: the main decision ----------
# "existing_rows" look like rows read from the records table.
EXISTING = [{"id": 7, "full_name": "Ali Khan", "email_norm": "ali@gmail.com", "phone_norm": "923001234567"}]
GOOD = {"full_name": "Bilal Raza", "email": "bilal@example.com", "phone": "0311-7654321", "city": "Lahore"}

def test_invalid_record_is_false_positive():
    r = classify({"full_name": "test", "email": "bad", "phone": "1"}, EXISTING)
    assert r["verdict"] == "FALSE_POSITIVE"
    assert r["matched_record_id"] is None
    assert "email" in r["reason"]

def test_new_valid_record_is_unique():
    r = classify(GOOD, EXISTING)
    assert r["verdict"] == "UNIQUE"
    assert r["normalized"]["email_norm"] == "bilal@example.com"

def test_unique_when_database_is_empty():
    assert classify(GOOD, [])["verdict"] == "UNIQUE"

def test_same_email_different_case_is_redundant():
    rec = dict(GOOD, email="ALI@GMAIL.COM")
    r = classify(rec, EXISTING)
    assert r["verdict"] == "REDUNDANT" and r["matched_record_id"] == 7
    assert "email" in r["reason"]

def test_gmail_dot_and_plus_trick_is_redundant():
    rec = dict(GOOD, email="a.l.i+offers@gmail.com")
    assert classify(rec, EXISTING)["verdict"] == "REDUNDANT"

def test_same_phone_and_similar_name_is_redundant():
    rec = dict(GOOD, full_name="Ali Khann", email="new@example.com", phone="+92 300 1234567")
    r = classify(rec, EXISTING)
    assert r["verdict"] == "REDUNDANT" and "phone" in r["reason"]

def test_same_phone_but_different_name_is_unique():
    # e.g. two family members sharing one phone: NOT the same person
    rec = dict(GOOD, full_name="Sara Ahmed", email="sara@example.com", phone="0300-1234567")
    assert classify(rec, EXISTING)["verdict"] == "UNIQUE"

def test_threshold_can_be_changed():
    rec = dict(GOOD, full_name="Sara Ahmed", email="sara@example.com", phone="0300-1234567")
    assert classify(rec, EXISTING, threshold=0.0)["verdict"] == "REDUNDANT"

def test_invalid_data_wins_over_duplicate_check():
    # email matches an existing row, but the phone is junk -> rejected first
    rec = {"full_name": "Ali Khan", "email": "ali@gmail.com", "phone": "12"}
    assert classify(rec, EXISTING)["verdict"] == "FALSE_POSITIVE"