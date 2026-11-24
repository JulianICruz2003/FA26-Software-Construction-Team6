import json
from unittest.mock import Mock

import httpx
import pytest
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QDialog, QLineEdit, QMessageBox

from desktop.dialogs.login_dialog import LoginDialog
from desktop.dialogs.registration_dialog import (
    DUPLICATE_EMAIL,
    MISSING_FIELDS,
    PASSWORD_MISMATCH,
    REGISTRATION_FAILED,
    SERVER_UNAVAILABLE,
    RegistrationDialog,
)
from desktop.services.api_client import ApiClient
from shared.registration import EMAIL_DOMAIN_ERROR, PASSWORD_ERROR


PASSWORD = "miners123!"
EMAIL = "student@miners.utep.edu"


def fill_form(dialog, *, name="Test Student", email=EMAIL, password=PASSWORD, confirmation=PASSWORD):
    dialog.name_input.setText(name)
    dialog.email_input.setText(email)
    dialog.password_input.setText(password)
    dialog.confirm_password_input.setText(confirmation)


def assert_checklist(dialog, expected):
    labels = dialog.password_requirement_labels
    messages = ("At least 8 characters", "At least one number", "At least one special character")
    assert len(labels) == len(messages)
    for label, message, satisfied in zip(labels, messages, expected, strict=True):
        assert label.text() == f"{'✓' if satisfied else '✕'}  {message}"
        assert label.styleSheet() == ("color: #187044;" if satisfied else "color: #b42318;")


def test_password_checklist_updates_with_typing_deleting_and_pasting(qt_app, qt_widget):
    dialog = qt_widget(RegistrationDialog, Mock())
    password = dialog.password_input

    assert_checklist(dialog, (False, False, False))
    QTest.keyClicks(password, "password")
    assert_checklist(dialog, (True, False, False))
    QTest.keyClicks(password, "1")
    assert_checklist(dialog, (True, True, False))
    QTest.keyClicks(password, "!")
    assert_checklist(dialog, (True, True, True))

    QTest.keyClick(password, Qt.Key.Key_Backspace)
    assert_checklist(dialog, (True, True, False))
    QTest.keyClick(password, Qt.Key.Key_Backspace)
    assert_checklist(dialog, (True, False, False))
    QTest.keyClick(password, Qt.Key.Key_Backspace)
    assert_checklist(dialog, (False, False, False))

    clipboard = qt_app.clipboard()
    try:
        clipboard.setText(PASSWORD)
        password.selectAll()
        password.paste()
        assert_checklist(dialog, (True, True, True))
        assert dialog.confirmation_feedback.text() == ""
    finally:
        clipboard.clear()


def test_confirmation_feedback_updates_from_either_field(qt_app, qt_widget):
    dialog = qt_widget(RegistrationDialog, Mock())
    feedback = dialog.confirmation_feedback
    dialog.show()
    qt_app.processEvents()
    button_position = dialog.create_account_button.pos()

    assert dialog.password_input.x() == dialog.password_requirement_labels[0].x()
    assert dialog.confirm_password_input.x() == feedback.x()
    assert feedback.text() == ""
    dialog.password_input.setText(PASSWORD)
    dialog.confirm_password_input.setText("different123!")
    assert feedback.text() == "✕  Passwords do not match"
    assert feedback.styleSheet() == "color: #b42318;"

    dialog.confirm_password_input.setText(PASSWORD)
    assert feedback.text() == "✓  Passwords match"
    assert feedback.styleSheet() == "color: #187044;"
    qt_app.processEvents()
    assert dialog.create_account_button.pos() == button_position

    dialog.password_input.setText("different123!")
    assert feedback.text() == "✕  Passwords do not match"
    dialog.confirm_password_input.clear()
    assert feedback.text() == ""
    dialog.close()


def test_maximum_length_is_enforced_separately_from_checklist(qt_widget):
    client = Mock()
    dialog = qt_widget(RegistrationDialog, client)
    password = "a" * 127 + "1!"
    fill_form(dialog, password=password, confirmation=password)

    assert_checklist(dialog, (True, True, True))
    dialog.create_account_button.click()
    client.register.assert_not_called()
    assert dialog.error_label.text() == PASSWORD_ERROR
    assert_checklist(dialog, (True, True, True))


@pytest.mark.parametrize(("fields", "message"), [
    ({"name": " "}, MISSING_FIELDS),
    ({"email": ""}, MISSING_FIELDS),
    ({"password": ""}, MISSING_FIELDS),
    ({"confirmation": ""}, MISSING_FIELDS),
    ({"email": "student@miners.utep.edu.fake.com"}, EMAIL_DOMAIN_ERROR),
    ({"password": "test1!"}, PASSWORD_ERROR),
    ({"password": "password!"}, PASSWORD_ERROR),
    ({"password": "password1"}, PASSWORD_ERROR),
    ({"confirmation": "different123!"}, PASSWORD_MISMATCH),
])
def test_invalid_form_does_not_call_api(qt_widget, fields, message):
    client = Mock()
    dialog = qt_widget(RegistrationDialog, client)
    fill_form(dialog, **fields)
    dialog.create_account_button.click()
    client.register.assert_not_called()
    assert dialog.error_label.text() == message


@pytest.mark.parametrize("submit", [False, True], ids=["cancel", "create"])
def test_create_account_opens_dialog_and_returns_to_sign_in(qt_app, qt_widget, monkeypatch, submit):
    client = Mock()
    login = qt_widget(LoginDialog, client)
    success = Mock()
    monkeypatch.setattr(QMessageBox, "information", success)
    login.show()
    assert login.create_account_button.isVisible()
    assert login.create_account_button.text() == "Create Account"
    observed = []

    def interact():
        dialog = qt_app.activeModalWidget()
        observed.append((
            isinstance(dialog, RegistrationDialog),
            dialog.password_input.echoMode(),
            dialog.confirm_password_input.echoMode(),
        ))
        fill_form(dialog, name=" Test Student ", email=EMAIL.upper())
        if submit:
            dialog.create_account_button.click()
        else:
            dialog.back_button.click()

    QTimer.singleShot(0, login, interact)
    login.create_account_button.click()

    assert observed == [(True, QLineEdit.EchoMode.Password, QLineEdit.EchoMode.Password)]
    assert login.isVisible()
    assert login.result() != QDialog.DialogCode.Accepted
    assert login.current_user is None
    client.login.assert_not_called()
    if submit:
        client.register.assert_called_once_with("Test Student", EMAIL, PASSWORD)
        success.assert_called_once()
        assert login.email_input.text() == EMAIL
    else:
        client.register.assert_not_called()
        success.assert_not_called()
    login.close()


@pytest.mark.parametrize(("status", "field", "message"), [
    (None, None, SERVER_UNAVAILABLE),
    (409, None, DUPLICATE_EMAIL),
    (422, "email", EMAIL_DOMAIN_ERROR),
    (422, "password", PASSWORD_ERROR),
    (500, None, REGISTRATION_FAILED),
])
def test_server_failure_shows_safe_message(qt_widget, status, field, message):
    client = Mock()
    request = httpx.Request("POST", "http://test/auth/register")
    if status is None:
        client.register.side_effect = httpx.ConnectError("refused", request=request)
    else:
        response = httpx.Response(status, request=request, json={
            "detail": [{"type": "value_error", "loc": ["body", field], "input": PASSWORD}],
        })
        client.register.side_effect = httpx.HTTPStatusError(
            "request failed", request=request, response=response,
        )
    dialog = qt_widget(RegistrationDialog, client)
    fill_form(dialog)
    dialog.create_account_button.click()
    assert dialog.error_label.text() == message
    assert dialog.result() != QDialog.DialogCode.Accepted
    assert dialog.password_input.text() == dialog.confirm_password_input.text() == ""
    assert dialog.create_account_button.isEnabled()


def test_registration_client_posts_credentials_without_creating_session(monkeypatch):
    def respond(request):
        assert request.method == "POST"
        assert request.url == "http://test/auth/register"
        assert "Authorization" not in request.headers
        assert json.loads(request.content) == {"name": "Test Student", "email": EMAIL, "password": PASSWORD}
        return httpx.Response(201, json={"account_role": "Student"})

    client = ApiClient()
    client.base_url = "http://test"
    transport_client = httpx.Client(transport=httpx.MockTransport(respond))
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: transport_client)
    client.register("Test Student", EMAIL, PASSWORD)
    assert client.access_token is None
