from unittest.mock import Mock

import httpx
import pytest
from PySide6.QtWidgets import QDialog, QLineEdit

from desktop.app_window import MainWindow
from desktop.dialogs.login_dialog import (
    INVALID_CREDENTIALS,
    MISSING_FIELDS,
    SERVER_UNAVAILABLE,
    LoginDialog,
)


STUDENT = {"id": 1, "name": "Test Student", "email": "s@example.com",
           "account_role": "Student"}
PROFESSOR = {"id": 2, "name": "Test Professor", "email": "p@example.com",
             "account_role": "Professor"}


def http_status_error(status_code):
    request = httpx.Request("POST", "http://test/auth/login")
    response = httpx.Response(status_code, request=request)
    return httpx.HTTPStatusError("error", request=request, response=response)


def window_api_client():
    api_client = Mock()
    api_client.get_projects.return_value = []
    return api_client


def fill_and_submit(dialog, email, password):
    dialog.email_input.setText(email)
    dialog.password_input.setText(password)
    dialog.sign_in_button.click()


def test_password_field_is_masked(qt_widget):
    dialog = qt_widget(LoginDialog, Mock())
    assert dialog.password_input.echoMode() == QLineEdit.EchoMode.Password


def test_empty_fields_do_not_call_api(qt_widget):
    api_client = Mock()
    dialog = qt_widget(LoginDialog, api_client)

    fill_and_submit(dialog, "  ", "")

    api_client.login.assert_not_called()
    assert dialog.error_label.text() == MISSING_FIELDS
    assert not dialog.error_label.isHidden()


def test_successful_login_accepts_and_stores_user(qt_widget):
    api_client = Mock()
    api_client.get_current_user.return_value = STUDENT
    dialog = qt_widget(LoginDialog, api_client)

    fill_and_submit(dialog, " s@example.com ", "a long enough password")

    api_client.login.assert_called_once_with(
        "s@example.com", "a long enough password"
    )
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert dialog.current_user == STUDENT
    assert dialog.password_input.text() == ""


@pytest.mark.parametrize("status_code", [401, 422])
def test_bad_credentials_show_generic_error(qt_widget, status_code):
    api_client = Mock()
    api_client.login.side_effect = http_status_error(status_code)
    dialog = qt_widget(LoginDialog, api_client)

    fill_and_submit(dialog, "s@example.com", "wrong password")

    assert dialog.result() != QDialog.DialogCode.Accepted
    assert dialog.current_user is None
    assert dialog.error_label.text() == INVALID_CREDENTIALS
    assert dialog.password_input.text() == ""
    assert dialog.sign_in_button.isEnabled()
    api_client.clear_session.assert_called_once()


def test_server_down_shows_connection_error(qt_widget):
    api_client = Mock()
    api_client.login.side_effect = httpx.ConnectError("refused")
    dialog = qt_widget(LoginDialog, api_client)

    fill_and_submit(dialog, "s@example.com", "a long enough password")

    assert dialog.error_label.text() == SERVER_UNAVAILABLE
    assert dialog.current_user is None


@pytest.mark.parametrize(
    "user, expected_title",
    [(STUDENT, "Student Dashboard"), (PROFESSOR, "Professor Dashboard")],
    ids=["student", "professor"],
)
def test_main_window_routes_by_role(qt_widget, user, expected_title):
    window = qt_widget(MainWindow, window_api_client(), user)

    assert window.dashboard_title.text() == expected_title
    assert window.pages.currentIndex() == 0


def test_sign_out_revokes_session(qt_widget):
    api_client = window_api_client()
    window = qt_widget(MainWindow, api_client, STUDENT)
    signals = []
    window.signed_out.connect(lambda: signals.append(True))

    window.sign_out()

    api_client.logout.assert_called_once()
    assert window.sign_out_requested
    assert signals == [True]
