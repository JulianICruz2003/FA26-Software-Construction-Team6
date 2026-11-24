"""Main application shell and role-specific navigation."""

import sys

import httpx
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup, QFrame, QHBoxLayout, QMainWindow, QPushButton, QStackedWidget,
    QVBoxLayout, QWidget,
)

from desktop.pages.dashboard import FeaturePage, text_label
from desktop.pages.professor_dashboard import ProfessorDashboard
from desktop.pages.project_workspace import ProjectWorkspacePage
from desktop.pages.projects import ProjectsPage
from desktop.pages.student_dashboard import StudentDashboard
from desktop.services.api_client import ApiClient


class MainWindow(QMainWindow):
    signed_out = Signal()

    def __init__(self, api_client=None, current_user=None) -> None:
        super().__init__()
        self.api_client = api_client or ApiClient()
        self.current_user = current_user
        self.sign_out_requested = False
        self.current_project = None
        self.setWindowTitle("Miner Project Hub")
        self.setMinimumSize(760, 420)
        self.resize(1050, 720)

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        sidebar = QFrame(objectName="sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 20, 12, 16)
        sidebar_layout.setSpacing(6)
        sidebar_layout.addWidget(text_label("Miner Project Hub", "sidebarTitle"))
        sidebar_layout.addSpacing(12)
        self.pages = QStackedWidget()
        self.page_by_name = {}
        self.navigation_buttons = {}
        self.navigation_group = QButtonGroup(self)
        layout.addWidget(sidebar)
        layout.addWidget(self.pages, 1)
        self.setCentralWidget(container)

        user = current_user or {}
        role = user.get("account_role")
        dashboard_type = {
            "Student": StudentDashboard,
            "Professor": ProfessorDashboard,
        }.get(role)

        if dashboard_type is None:
            dashboard = FeaturePage(
                "Dashboard unavailable",
                "Your account does not have a supported dashboard role. Sign out "
                "and contact your administrator if this persists.",
            )
            self.add_page("Dashboard", dashboard)
            navigation = ("Dashboard",)
        else:
            dashboard = dashboard_type(user.get("name", ""))
            dashboard.action_requested.connect(self.navigate)
            self.add_page("Dashboard", dashboard)
            for name, page in dashboard.feature_pages().items():
                self.add_page(name, page)
            self.add_project_pages()
            self.add_page("Settings", self.build_settings())
            self.page_by_name["My Classes"].add_action(
                "Join Class" if role == "Student" else "Create Class",
                lambda: self.navigate("Join Class" if role == "Student" else "Create Class"),
            )
            if role == "Student":
                navigation = (
                    "Dashboard", "My Classes", "My Projects", "My Tasks",
                    "Project Workspace", "Settings",
                )
                self.page_by_name["My Projects"].add_action(
                    "Browse Shared Projects", lambda: self.navigate("Shared Projects")
                )
                self.page_by_name["My Tasks"].add_action(
                    "Open Project Tasks", self.show_project_tasks
                )
            else:
                navigation = (
                    "Dashboard", "My Classes", "Class Projects",
                    "Project Workspace", "Reviews / Progress", "Settings",
                )
        self.dashboard_title = dashboard.title

        for name in navigation:
            button = QPushButton(name, objectName="navigationButton", checkable=True)
            button.clicked.connect(lambda checked=False, page=name: self.navigate(page))
            self.navigation_group.addButton(button)
            self.navigation_buttons[name] = button
            sidebar_layout.addWidget(button)

        sidebar_layout.addStretch()
        self.sign_out_button = QPushButton("Sign Out", objectName="signOut")
        self.sign_out_button.clicked.connect(self.sign_out)
        sidebar_layout.addWidget(self.sign_out_button)
        self.navigate("Dashboard")
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #f8fafc; color: #15243a; font-size: 14px; }
            QFrame#sidebar, QLabel#sidebarTitle { background: #172a42; color: white; }
            QLabel#sidebarTitle { font-size: 17px; font-weight: 700; padding: 4px; }
            QLabel#heading { font-size: 27px; font-weight: 700; }
            QLabel#sectionTitle { font-size: 15px; font-weight: 700; }
            QLabel#subtitle { color: #4b5c70; }
            QFrame#dashboardHero { background: #fff0e6; border: 1px solid #f4c2a5;
                                   border-radius: 10px; padding: 8px; }
            QFrame#dashboardCard { background: white; border: 1px solid #dce4ed;
                                   border-radius: 8px; padding: 4px; }
            QFrame#dashboardHero QLabel, QFrame#dashboardCard QLabel { background: transparent; }
            QPushButton { background: #1558b0; color: white; border: 1px solid transparent;
                          border-radius: 6px; padding: 9px 12px; font-weight: 600; }
            QPushButton:hover { background: #10468b; }
            QPushButton:disabled { background: #e2e8f0; color: #546174; }
            QPushButton#dashboardAction { background: #9e3b14; }
            QPushButton#dashboardAction:hover { background: #78300f; }
            QPushButton#navigationButton, QPushButton#signOut {
                background: #172a42; color: white; text-align: left;
            }
            QPushButton#navigationButton:hover, QPushButton#signOut:hover { background: #284462; }
            QPushButton#navigationButton:checked { background: #fee3d3; color: #732b0e; }
            QPushButton:focus { border: 1px solid #e98046; }
        """)

    def add_page(self, name, widget):
        self.page_by_name[name] = widget
        self.pages.addWidget(widget)

    def navigate(self, name):
        page = self.page_by_name[name]
        self.pages.setCurrentWidget(page)
        sidebar_name = {
            "Join Class": "My Classes",
            "Create Class": "My Classes",
            "Shared Projects": "Project Workspace",
        }.get(name, name)
        self.navigation_buttons[sidebar_name].setChecked(True)
        if name == "Shared Projects" and not page.has_loaded:
            page.load_projects()

    def add_project_pages(self):
        self.project_workspace = ProjectWorkspacePage(self.api_client)
        workspace = QWidget()
        layout = QVBoxLayout(workspace)
        browse = QPushButton("Browse Shared Projects", objectName="dashboardAction")
        browse.clicked.connect(lambda: self.navigate("Shared Projects"))
        layout.addWidget(browse)
        layout.addWidget(self.project_workspace)
        self.add_page("Project Workspace", workspace)

        projects = ProjectsPage(self.api_client, load_on_init=False)
        projects.project_opened.connect(self.show_project_workspace)
        self.add_page("Shared Projects", projects)

    def show_project_workspace(self, project):
        if project != self.current_project:
            self.project_workspace.display_project(project)
            self.current_project = project
        self.navigate("Project Workspace")

    def show_project_tasks(self):
        if self.current_project is None:
            self.navigate("Shared Projects")
            return
        self.navigate("Project Workspace")
        self.project_workspace.tabs.setCurrentWidget(self.project_workspace.tasks_tab)

    def build_settings(self):
        page = FeaturePage("Settings", "Check the connection to the API and database.")
        self.connection_status = text_label("Connection unchecked", "subtitle")
        page.layout_box.insertWidget(2, self.connection_status)
        page.add_action("Check Connection", self.check_connection)
        return page

    def check_connection(self):
        if not self.api_client.check_api():
            self.connection_status.setText("API unavailable. Database check skipped.")
        elif self.api_client.check_database():
            self.connection_status.setText("API and database connected.")
        else:
            self.connection_status.setText("API connected. Database unavailable.")

    def sign_out(self):
        try:
            self.api_client.logout()
        except httpx.HTTPError as exc:
            # ApiClient clears the local token even if the API is unreachable.
            print(f"Sign out request failed: {exc}", file=sys.stderr)
        self.sign_out_requested = True
        self.signed_out.emit()
        self.close()
