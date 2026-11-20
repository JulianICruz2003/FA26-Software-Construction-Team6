"""Student account registration from the sign-in window."""

import httpx
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from desktop.dialogs.auth_style import AUTH_DIALOG_STYLE
from shared.registration import (
    EMAIL_DOMAIN_ERROR,
    PASSWORD_ERROR,
    normalize_university_email,
    password_requirement_status,
    validate_new_password,
)


MISSING_FIELDS = "Complete all four fields."
CONFIRMATION_MISMATCH = "Passwords do not match"
PASSWORD_MISMATCH = f"{CONFIRMATION_MISMATCH}."
NAME_ERROR = "Enter a full name of 120 characters or fewer."
DUPLICATE_EMAIL = "An account with this email already exists."
SERVER_UNAVAILABLE = "Could not reach the server. Make sure the API is running."
REGISTRATION_FAILED = "Account creation failed. Please try again later."


PASSWORD_REQUIREMENTS = (
    "At least 8 characters",
    "At least one number",
    "At least one special character",
)


def set_validation_feedback(label, message, satisfied):
    icon, color = ("✓", "#187044") if satisfied else ("✕", "#b42318")
    label.setText(f"{icon}  {message}")
    label.setStyleSheet(f"color: {color};")


class RegistrationDialog(QDialog):
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.registered_email = None
        self.setWindowTitle("Create Account - Miner Project Hub")
        self.setMinimumWidth(460)
        self.setStyleSheet(AUTH_DIALOG_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(14)
        heading = QLabel("Create your student account")
        heading.setObjectName("heading")
        layout.addWidget(heading)

        form = QFormLayout()
        self.name_input = QLineEdit()
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("you@miners.utep.edu")
        self.password_input = QLineEdit()
        self.confirm_password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("&Full Name:", self.name_input)
        form.addRow("&University Email:", self.email_input)
        form.addRow("&Password:", self.password_input)
        checklist = QVBoxLayout()
        checklist.setSpacing(3)
        self.password_requirement_labels = [QLabel() for _ in PASSWORD_REQUIREMENTS]
        for label in self.password_requirement_labels:
            checklist.addWidget(label)
        form.addRow("", checklist)

        form.addRow("C&onfirm Password:", self.confirm_password_input)
        self.confirmation_feedback = QLabel()
        # Reserve a line for feedback so the fields and buttons stay in place.
        self.confirmation_feedback.setMinimumHeight(self.confirmation_feedback.fontMetrics().height())
        form.addRow("", self.confirmation_feedback)
        layout.addLayout(form)

        self.password_input.textChanged.connect(self.update_password_requirements)
        self.password_input.textChanged.connect(self.update_confirmation_feedback)
        self.confirm_password_input.textChanged.connect(self.update_confirmation_feedback)
        self.update_password_requirements()
        self.update_confirmation_feedback()

        self.error_label = QLabel()
        self.error_label.setObjectName("error")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        self.create_account_button = QPushButton("Create Account")
        self.create_account_button.setDefault(True)
        self.create_account_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.create_account_button.clicked.connect(self.attempt_registration)
        layout.addWidget(self.create_account_button)

        self.back_button = QPushButton("Back to Sign In")
        self.back_button.setAutoDefault(False)
        self.back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_button.clicked.connect(self.reject)
        layout.addWidget(self.back_button)
        self.name_input.setFocus()

    def update_password_requirements(self):
        statuses = password_requirement_status(self.password_input.text())
        for label, message, satisfied in zip(
            self.password_requirement_labels, PASSWORD_REQUIREMENTS, statuses, strict=True
        ):
            set_validation_feedback(label, message, satisfied)

    def update_confirmation_feedback(self):
        confirmation = self.confirm_password_input.text()
        if not confirmation:
            self.confirmation_feedback.clear()
            return
        matches = confirmation == self.password_input.text()
        message = "Passwords match" if matches else CONFIRMATION_MISMATCH
        set_validation_feedback(self.confirmation_feedback, message, matches)

    def attempt_registration(self):
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirmation = self.confirm_password_input.text()
        if not all((name, email, password, confirmation)):
            self.show_error(MISSING_FIELDS)
            return
        if len(name) > 120:
            self.show_error(NAME_ERROR)
            return
        try:
            email = normalize_university_email(email)
            validate_new_password(password)
        except ValueError as error:
            self.show_error(str(error))
            return
        if password != confirmation:
            self.show_error(PASSWORD_MISMATCH)
            return

        self.error_label.hide()
        self.create_account_button.setEnabled(False)
        try:
            self.api_client.register(name, email, password)
        except httpx.HTTPStatusError as error:
            self.show_error(registration_error(error.response))
        except httpx.HTTPError:
            self.show_error(SERVER_UNAVAILABLE)
        else:
            self.registered_email = email
            QMessageBox.information(self, "Account Created", "Your account is ready. Sign in to continue.")
            self.accept()
        finally:
            self.password_input.clear()
            self.confirm_password_input.clear()
            self.create_account_button.setEnabled(True)

    def show_error(self, message):
        self.error_label.setText(message)
        self.error_label.show()


def registration_error(response):
    if response.status_code == 409:
        return DUPLICATE_EMAIL
    if response.status_code == 422:
        messages = {"email": EMAIL_DOMAIN_ERROR, "password": PASSWORD_ERROR, "name": NAME_ERROR}
        try:
            for error in response.json()["detail"]:
                if error["type"] == "missing":
                    return MISSING_FIELDS
                field = error["loc"][-1]
                if field in messages:
                    return messages[field]
        except (ValueError, TypeError, AttributeError, KeyError, IndexError):
            pass
    return REGISTRATION_FAILED
