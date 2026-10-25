import re

# Common placeholder / test values people type to get past a form
JUNK_NAMES = {
    "test", "testing", "asdf", "asdfgh", "qwerty", "dummy", "fake", "sample",
    "n/a", "na", "none", "null", "abc", "xyz", "unknown", "name",
}

# Throw-away email services: valid-looking but not a real, verified person
DISPOSABLE_DOMAINS = {
    "mailinator.com", "10minutemail.com", "guerrillamail.com",
    "tempmail.com", "yopmail.com", "trashmail.com", "throwawaymail.com",
}

# Letters (any language), joined by space . ' or -   e.g. "Sara O'Neil-Khan"
_WORDS_RE = re.compile(r"^[^\W\d_]+(?:[ .'\-]+[^\W\d_]+)*\.?$")
# local@domain.tld  (simple, practical pattern; not the full RFC)
_EMAIL_RE = re.compile(
    r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}$"
)
# digits, spaces, dashes, brackets, optional leading +
_PHONE_CHARS_RE = re.compile(r"^\+?[\d\s\-()]+$")


def _s(value):
    """Turn None / numbers into a stripped string, so checks never crash."""
    return "" if value is None else str(value).strip()


def validate_name(value):
    name = _s(value)
    if not name:
        return "name is required"
    if len(name) < 2:
        return "name is too short"
    if len(name) > 100:
        return "name is too long"
    letters = re.sub(r"[^a-z]", "", name.lower())
    # junk list, or one letter repeated like "aaaa"
    if name.lower() in JUNK_NAMES or (len(letters) >= 3 and len(set(letters)) == 1):
        return "name looks like placeholder/test data"
    if not _WORDS_RE.match(name):
        return "name may contain only letters, spaces, . ' and -"
    return None


def validate_email(value):
    email = _s(value)
    if not email:
        return "email is required"
    if len(email) > 254:
        return "email is too long"
    if ".." in email:
        return "email has consecutive dots"
    if not _EMAIL_RE.match(email):
        return "email format is invalid"
    local, domain = email.rsplit("@", 1)
    if local.startswith(".") or local.endswith("."):
        return "email has a dot at the start/end of the name part"
    if domain.lower() in DISPOSABLE_DOMAINS:
        return "disposable email domains are not accepted"
    return None


def validate_phone(value):
    phone = _s(value)
    if not phone:
        return "phone is required"
    if len(phone) > 30:                        # must fit the VARCHAR(30) database column
        return "phone is too long"
    if not _PHONE_CHARS_RE.match(phone):
        return "phone may contain only digits, spaces, - ( ) and a leading +"
    digits = re.sub(r"\D", "", phone)          # keep digits only
    if not 10 <= len(digits) <= 15:            # 15 = international maximum (E.164)
        return "phone must have 10 to 15 digits"
    if len(set(digits)) == 1:
        return "phone looks fake (same digit repeated)"
    return None

def validate_city(value):
    city = _s(value)
    if not city:                               # city is optional
        return None
    if len(city) > 80:
        return "city is too long"
    if not _WORDS_RE.match(city):
        return "city may contain only letters, spaces, . ' and -"
    return None


def validate_record(record):
    """Check a whole record. Returns a list of 'field: reason' (empty = valid)."""
    checks = (
        ("full_name", validate_name),
        ("email", validate_email),
        ("phone", validate_phone),
        ("city", validate_city),
    )
    errors = []
    for field, check in checks:
        problem = check(record.get(field))
        if problem:
            errors.append(f"{field}: {problem}")
    return errors

