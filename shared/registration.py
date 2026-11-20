"""Account creation rules shared by the desktop client and the API."""

from unicodedata import category

from email_validator import EmailNotValidError, validate_email


EMAIL_FORMAT_ERROR = "Enter a valid university email address."
EMAIL_DOMAIN_ERROR = "Use an @miners.utep.edu or @utep.edu email address."
PASSWORD_ERROR = "Use 8–128 characters with at least one number and one special character."
ALLOWED_DOMAINS = {"miners.utep.edu", "utep.edu"}


def normalize_university_email(value: str) -> str:
    value = value.strip()
    try:
        email = validate_email(value, check_deliverability=False)
    except EmailNotValidError:
        raise ValueError(EMAIL_FORMAT_ERROR) from None
    if value.rsplit("@", 1)[-1].lower() not in ALLOWED_DOMAINS:
        raise ValueError(EMAIL_DOMAIN_ERROR)
    return email.normalized.lower()


def validate_new_password(value: str) -> None:
    if (
        not 8 <= len(value) <= 128
        or not any(char.isdecimal() for char in value)
        or not any(category(char)[0] in {"P", "S"} for char in value)
    ):
        raise ValueError(PASSWORD_ERROR)
