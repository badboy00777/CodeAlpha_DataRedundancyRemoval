
import pytest
from app.validators import (
    validate_name, validate_email, validate_phone, validate_city, validate_record,
)


# ---------- NAME ----------
def test_valid_name_passes():
    assert validate_name("Ali Khan") is None


def test_name_with_apostrophe_and_hyphen_passes():
    assert validate_name("Sara O'Neil-Khan") is None


def test_empty_name_rejected():
    assert validate_name("   ") is not None


def test_one_letter_name_rejected():
    assert validate_name("A") is not None


def test_name_with_digits_rejected():
    assert validate_name("Ali123") is not None


# Junk / test data must be caught (case-insensitive)
@pytest.mark.parametrize("junk", ["test", "asdf", "QWERTY", "dummy", "n/a", "aaaa"])
def test_junk_names_rejected(junk):
    assert validate_name(junk) is not None


# ---------- EMAIL ----------
def test_valid_email_passes():
    assert validate_email("ali@example.com") is None


def test_email_with_plus_and_subdomain_passes():
    assert validate_email("ali.khan+news@mail.example.co.uk") is None


def test_empty_email_rejected():
    assert validate_email("") is not None


def test_email_without_at_rejected():
    assert validate_email("ali.example.com") is not None


def test_email_without_domain_dot_rejected():
    assert validate_email("ali@example") is not None


def test_email_with_double_dot_rejected():
    assert validate_email("ali..khan@example.com") is not None


def test_disposable_email_rejected():
    assert validate_email("x@mailinator.com") is not None


# ---------- PHONE ----------
@pytest.mark.parametrize("ok", ["0300-1234567", "+92 300 1234567", "03001234567"])
def test_valid_phone_formats_pass(ok):
    assert validate_phone(ok) is None


def test_too_short_phone_rejected():
    assert validate_phone("12345") is not None


def test_phone_with_letters_rejected():
    assert validate_phone("0300-ABCDEFG") is not None


def test_phone_all_same_digit_rejected():
    assert validate_phone("0000000000") is not None


# ---------- CITY (optional field) ----------
def test_city_is_optional():
    assert validate_city("") is None
    assert validate_city(None) is None


def test_city_with_digits_rejected():
    assert validate_city("Lahore123") is not None


# ---------- WHOLE RECORD ----------
def test_valid_record_has_no_errors():
    rec = {"full_name": "Ali Khan", "email": "ali@example.com",
           "phone": "0300-1234567", "city": "Faisalabad"}
    assert validate_record(rec) == []


def test_record_without_city_is_valid():
    rec = {"full_name": "Ali Khan", "email": "ali@example.com", "phone": "0300-1234567"}
    assert validate_record(rec) == []


def test_record_collects_all_errors():
    rec = {"full_name": "test", "email": "bad", "phone": "1"}
    assert len(validate_record(rec)) == 3     # one error per bad field


def test_empty_record_reports_missing_fields():
    assert len(validate_record({})) == 3      # name, email, phone are required
    


def test_phone_longer_than_30_characters_rejected():
    # The database column is VARCHAR(30): a longer value would crash the insert (500 error)
    assert validate_phone("0300" + " " * 40 + "1234567") is not None