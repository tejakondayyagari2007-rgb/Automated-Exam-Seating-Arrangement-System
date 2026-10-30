import re


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email):
    return bool(email) and bool(EMAIL_PATTERN.match(email.strip()))


def is_valid_year(year):
    try:
        year_value = int(year)
        return 1 <= year_value <= 8
    except (TypeError, ValueError):
        return False


def normalize_text(value):
    if value is None:
        return ""
    return str(value).strip()
