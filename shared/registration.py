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


def password_requirement_status(value: str) -> tuple[bool, bool, bool]:
    """Return whether the password meets the minimum length, number, and symbol rules."""
    return (
        len(value) >= 8,
        any(char.isdecimal() for char in value),
        any(category(char)[0] in {"P", "S"} for char in value),
    )


def validate_new_password(value: str) -> None:
    if len(value) > 128 or not all(password_requirement_status(value)):
        raise ValueError(PASSWORD_ERROR)
