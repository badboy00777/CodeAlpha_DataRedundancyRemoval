import hashlib
import re
from difflib import SequenceMatcher

from app.validators import validate_record, _s   # _s = safe "to stripped string"

GMAIL_DOMAINS = {"gmail.com", "googlemail.com"}


def normalize_name(value):
    # lowercase + collapse many spaces into one: "  Ali   KHAN " -> "ali khan"
    return " ".join(_s(value).lower().split())


def normalize_email(value):
    email = _s(value).lower()
    if "@" not in email:
        return email
    local, domain = email.rsplit("@", 1)
    # Gmail ignores dots and "+tag", so a.li+x@gmail.com is really ali@gmail.com.
    # We do this ONLY for Gmail: other providers may treat dots/plus differently.
    if domain in GMAIL_DOMAINS:
        local = local.split("+", 1)[0].replace(".", "")
        domain = "gmail.com"
    return f"{local}@{domain}"


def normalize_phone(value):
    digits = re.sub(r"\D", "", _s(value))      # keep digits only
    if digits.startswith("00"):                # 0092300... -> 92300...
        digits = digits[2:]
    if digits.startswith("0") and len(digits) == 11:   # Pakistani 03001234567 -> 923001234567
        digits = "92" + digits[1:]
    return digits


def build_normalized(record):
    """Turn a raw form record into its clean (normalized) version."""
    return {
        "full_name_norm": normalize_name(record.get("full_name")),
        "email_norm": normalize_email(record.get("email")),
        "phone_norm": normalize_phone(record.get("phone")),
    }


def fingerprint(norm):
    # SHA-256 of the clean record. Same person (any formatting) = same fingerprint.
    text = "|".join([norm["full_name_norm"], norm["email_norm"], norm["phone_norm"]])
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def name_similarity(a, b):
    # 0.0 (nothing alike) to 1.0 (identical), using Python's built-in difflib
    return SequenceMatcher(None, normalize_name(a), normalize_name(b)).ratio()


def find_duplicate(norm, existing_rows, threshold=0.85):
    """Return (existing_id, reason) if this person already exists, else None."""
    # Rule 1: same normalized email = same person
    for row in existing_rows:
        if row["email_norm"] == norm["email_norm"]:
            return row["id"], "email already exists"
    # Rule 2: same phone AND a very similar name = same person
    # (same phone but a different name could be a family member, so it is allowed)
    for row in existing_rows:
        if row["phone_norm"] == norm["phone_norm"]:
            if name_similarity(row["full_name"], norm["full_name_norm"]) >= threshold:
                return row["id"], "same phone number and a very similar name"
    return None


def classify(record, existing_rows, threshold=0.85):
    """Main decision. Returns a dict with verdict, reason, matched_record_id, normalized."""
    errors = validate_record(record)
    norm = build_normalized(record)

    # Step 1: invalid data is rejected BEFORE any duplicate check
    if errors:
        return {"verdict": "FALSE_POSITIVE", "reason": "; ".join(errors),
                "matched_record_id": None, "normalized": norm}

    # Step 2: compare with what is already stored
    hit = find_duplicate(norm, existing_rows, threshold)
    if hit:
        return {"verdict": "REDUNDANT", "reason": hit[1],
                "matched_record_id": hit[0], "normalized": norm}

    # Step 3: nothing matched -> new verified record
    return {"verdict": "UNIQUE", "reason": "new verified record",
            "matched_record_id": None, "normalized": norm}