"""Sign-in window shown before the main application opens."""

import httpx
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


from desktop.dialogs.auth_style import AUTH_DIALOG_STYLE
from desktop.dialogs.registration_dialog import RegistrationDialog, SERVER_UNAVAILABLE


INVALID_CREDENTIALS = "Invalid email or password."
MISSING_FIELDS = "Enter your email and password."
SIGN_IN_FAILED = "Sign in failed. Please try again later."


class LoginDialog(QDialog):
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.current_user = None

        self.setWindowTitle("Sign In - Miner Project Hub")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(14)

        heading = QLabel("Miner Project Hub")
        heading.setObjectName("heading")
        layout.addWidget(heading)

        subtitle = QLabel("Sign in with your account")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        form = QFormLayout()

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("you@miners.utep.edu")
        form.addRow("Email:", self.email_input)

        # Password is masked and never stored after a sign-in attempt
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Password:", self.password_input)

        layout.addLayout(form)

        self.error_label = QLabel()
        self.error_label.setObjectName("error")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        self.sign_in_button = QPushButton("Sign In")
        self.sign_in_button.setDefault(True)
        self.sign_in_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sign_in_button.clicked.connect(self.attempt_login)
        layout.addWidget(self.sign_in_button)

        self.create_account_button = QPushButton("Create Account")
        self.create_account_button.setAutoDefault(False)
        self.create_account_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.create_account_button.clicked.connect(self.open_registration)
        layout.addWidget(self.create_account_button)

        self.email_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self.attempt_login)

        self.setStyleSheet(AUTH_DIALOG_STYLE)

    def open_registration(self):
        dialog = RegistrationDialog(self.api_client, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.email_input.setText(dialog.registered_email)
            self.password_input.clear()
            self.error_label.hide()
            self.password_input.setFocus()

    def attempt_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()

        if not email or not password:
            self.show_error(MISSING_FIELDS)
            return

        self.set_busy(True)
        try:
            self.api_client.login(email, password)
            user = self.api_client.get_current_user()
        except httpx.HTTPStatusError as exc:
            self.api_client.clear_session()
            if exc.response.status_code in (401, 422):
                self.show_error(INVALID_CREDENTIALS)
            else:
                self.show_error(SIGN_IN_FAILED)
        except httpx.HTTPError:
            self.api_client.clear_session()
            self.show_error(SERVER_UNAVAILABLE)
        except (KeyError, ValueError):
            self.api_client.clear_session()
            self.show_error(SIGN_IN_FAILED)
        else:
            self.current_user = user
            self.accept()
        finally:
            self.password_input.clear()
            self.set_busy(False)

    def show_error(self, message):
        self.error_label.setText(message)
        self.error_label.show()

    def set_busy(self, busy):
        self.sign_in_button.setEnabled(not busy)
        self.sign_in_button.setText("Signing in..." if busy else "Sign In")
