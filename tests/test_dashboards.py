from unittest.mock import Mock

import httpx
import pytest
from PySide6.QtWidgets import QDialog

from desktop.app_window import MainWindow
from desktop.dialogs.login_dialog import LoginDialog
from desktop.pages.professor_dashboard import ProfessorDashboard
from desktop.pages.student_dashboard import StudentDashboard


@pytest.mark.parametrize(
    "role, dashboard_type, navigation, actions",
    [
        (
            "Student",
            StudentDashboard,
            ("Dashboard", "My Classes", "My Projects", "My Tasks", "Project Workspace", "Settings"),
            {
                "View My Classes": "My Classes",
                "Join Class": "Join Class",
                "View My Projects": "My Projects",
                "View My Tasks": "My Tasks",
            },
        ),
        (
            "Professor",
            ProfessorDashboard,
            ("Dashboard", "My Classes", "Class Projects", "Project Workspace", "Reviews / Progress", "Settings"),
            {
                "View My Classes": "My Classes",
                "Create Class": "Create Class",
                "View Class Projects": "Class Projects",
                "Monitor Project Progress": "Reviews / Progress",
            },
        ),
    ],
)
def test_login_dashboard_navigation(qt_widget, role, dashboard_type, navigation, actions):
    api = Mock()
    api.get_current_user.return_value = {"name": "Alex Morgan", "account_role": role}
    dialog = qt_widget(LoginDialog, api)
    dialog.email_input.setText("alex@example.com")
    dialog.password_input.setText("a long enough password")
    dialog.sign_in_button.click()
    assert dialog.result() == QDialog.DialogCode.Accepted
    api.get_current_user.assert_called_once()

    window = qt_widget(MainWindow, api, dialog.current_user)
    dashboard = window.pages.currentWidget()
    assert isinstance(dashboard, dashboard_type)
    assert tuple(window.navigation_buttons) == navigation

    for destination, button in window.navigation_buttons.items():
        button.click()
        assert button.isChecked()
        assert window.pages.currentWidget() is window.page_by_name[destination]

    for name, destination in actions.items():
        window.navigation_buttons["Dashboard"].click()
        dashboard.quick_actions[name].click()
        assert window.pages.currentWidget() is window.page_by_name[destination]
        assert window.page_by_name[destination].status.text()

    api.get_projects.assert_not_called()
    api.get_tasks.assert_not_called()


@pytest.mark.parametrize("user", [None, {}, {"account_role": "Administrator"}])
def test_unsupported_roles_have_no_project_or_class_routes(qt_widget, user):
    api = Mock()
    window = qt_widget(MainWindow, api, user)
    assert tuple(window.page_by_name) == ("Dashboard",)
    assert tuple(window.navigation_buttons) == ("Dashboard",)
    assert window.dashboard_title.text() == "Dashboard unavailable"
    api.get_projects.assert_not_called()

    window.sign_out_button.click()
    api.logout.assert_called_once()
    assert window.sign_out_requested


def test_shared_projects_error_retry_and_empty_state(qt_widget):
    api = Mock()
    api.get_projects.side_effect = [httpx.ConnectError("offline"), []]
    window = qt_widget(MainWindow, api, {"name": "Alex Morgan", "account_role": "Student"})

    window.navigation_buttons["My Tasks"].click()
    window.show_project_tasks()
    projects = window.pages.currentWidget()
    assert projects is window.page_by_name["Shared Projects"]
    assert "Could not load shared projects" in projects.load_status.text()
    assert not projects.has_loaded

    projects.refresh_button.click()
    assert projects.has_loaded
    assert projects.project_list.count() == 0
    assert projects.load_status.text() == "No shared projects yet."


def test_workspace_keeps_selected_project_across_navigation(qt_widget):
    api = Mock()
    project = {"id": 42, "name": "Robotics Lab"}
    api.get_projects.return_value = [project]
    api.get_tasks.return_value = []
    api.get_team_members.return_value = []
    window = qt_widget(MainWindow, api, {"name": "Alex Morgan", "account_role": "Student"})

    window.navigate("Shared Projects")
    projects = window.pages.currentWidget()
    projects.project_list.itemDoubleClicked.emit(projects.project_list.item(0))
    workspace = window.project_workspace
    assert window.pages.currentWidget() is window.page_by_name["Project Workspace"]
    assert workspace.tabs.currentWidget() is workspace.overview

    window.navigation_buttons["Dashboard"].click()
    window.navigation_buttons["My Tasks"].click()
    window.show_project_tasks()
    assert window.current_project == project
    assert workspace.tabs.currentWidget() is workspace.tasks_tab
    window.navigation_buttons["Settings"].click()
    window.navigation_buttons["Project Workspace"].click()
    assert workspace.tabs.currentWidget() is workspace.tasks_tab
    assert workspace.title.text() == "Robotics Lab"
    api.get_tasks.assert_called_once_with(42)
