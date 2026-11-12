"""Simple PySide6 desktop application that checks central API status."""
import os
import sys
from desktop.pages.projects import ProjectsPage
from pathlib import Path

from desktop.services.api_client import ApiClient

from desktop.pages.project_workspace import ProjectWorkspacePage

import httpx
from dotenv import load_dotenv
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QStackedWidget,
    QLineEdit,
    QListWidget,
    QMessageBox,
)

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.api_client = ApiClient()
        self.setWindowTitle("Miner Project Hub — Development Starter")
        self.setMinimumSize(620, 360)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 30, 32, 30)
        layout.setSpacing(16)

        heading = QLabel("Miner Project Hub")
        heading.setObjectName("heading")
        layout.addWidget(heading)

        subtitle = QLabel("Desktop client • Python + PySide6")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        intro = QLabel(
            "Student and professor workflows will share a central API. "
            "This development starter verifies that your local application can reach it."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.api_status = QLabel("API: not checked")
        self.db_status = QLabel("Database: not checked")
        self.api_status.setObjectName("status")
        self.db_status.setObjectName("status")
        layout.addWidget(self.api_status)
        layout.addWidget(self.db_status)

        button = QPushButton("Check connection")
        button.clicked.connect(self.check_connection)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(button)

        address = QLabel(f"Server: {self.api_client.base_url}")
        address.setObjectName("subtitle")
        address.setWordWrap(True)
        layout.addWidget(address)
        layout.addStretch()

        
        # Create a stack to hold all application pages
        self.pages = QStackedWidget()

        # Keep the existing connection-check screen as the first page
        self.pages.addWidget(container)

        # Define the main navigation pages
        page_names = [
            "Dashboard",
            "My Projects",
            "Project Workspace",
            "Tasks",
            "Files",
            "Diagrams",
            "Teams",
            "Courses",
            "Reviews",
            "Settings"
        ]

        # Create the project workspace page
        self.project_workspace = ProjectWorkspacePage(self.api_client)
        self.current_project = None

        # Create the main application layout
        main_container = QWidget()
        main_layout = QHBoxLayout(main_container)

        # Create the sidebar
        sidebar = QVBoxLayout()

        for index, name in enumerate(page_names):

            if index != 0:
                if name == "My Projects":
                    page = ProjectsPage(self.api_client)

                    page.project_opened.connect(
                        self.show_project_workspace
                    )

                elif name == "Project Workspace":
                    page = self.project_workspace

                else:
                    page = QWidget()
                    page_layout = QVBoxLayout(page)

                    title = QLabel(name)
                    title.setObjectName("heading")

                    page_layout.addWidget(title)
                    page_layout.addWidget(
                        QLabel("This page is under development.")
                    )
                    page_layout.addStretch()

                self.pages.addWidget(page)

            # Create navigation buttons
            button = QPushButton(name)

            if name == "Tasks":
                button.clicked.connect(self.show_tasks_from_sidebar)
            elif name == "Files":
                button.clicked.connect(self.show_files_from_sidebar)
            elif name == "Teams":
                button.clicked.connect(self.show_team_from_sidebar)
            else:
                button.clicked.connect(
                    lambda checked=False, i=index: self.pages.setCurrentIndex(i)
                )

            sidebar.addWidget(button)

        sidebar.addStretch()

        # Put sidebar and pages next to each other
        main_layout.addLayout(sidebar, 1)
        main_layout.addWidget(self.pages, 4)

        self.setCentralWidget(main_container)

        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #f8fafc; color: #15243a; font-size: 14px; }
            QLabel#heading { font-size: 27px; font-weight: 700; }
            QLabel#subtitle { color: #63748c; }
            QLabel#status { background: #e9eef5; padding: 10px; border-radius: 5px; }
            QPushButton { background-color: #1558b0; color: white; border: 0;
                          border-radius: 6px; padding: 11px 18px; font-weight: 600; }
            QPushButton:hover { background-color: #10468b; }
        """)

    
    def check_connection(self):
        # Check FastAPI
        api_connected = self.api_client.check_api()

        if api_connected:
            self.api_status.setText("API: connected")
        else:
            self.api_status.setText("API: unavailable")
            self.db_status.setText("Database: not checked")
            return

        # Check PostgreSQL through FastAPI
        db_connected = self.api_client.check_database()

        if db_connected:
            self.db_status.setText("Database: connected")
        else:
            self.db_status.setText("Database: unavailable")

    def show_project_workspace(self, project):
        self.current_project = project

        self.project_workspace.display_project(project)
        self.pages.setCurrentWidget(self.project_workspace)

    def show_tasks_from_sidebar(self):
        if self.current_project is None:
            QMessageBox.information(
                self,
                "No Project Selected",
                "Please open a project before viewing its tasks."
            )

            # Navigate to My Projects
            self.pages.setCurrentIndex(1)
            return

        # Open the selected project's workspace
        self.pages.setCurrentWidget(self.project_workspace)

        # Switch directly to its Tasks tab
        self.project_workspace.tabs.setCurrentWidget(
            self.project_workspace.tasks_tab
        )
    
    def show_files_from_sidebar(self):
        if self.current_project is None:
            QMessageBox.information(
                self,
                "No Project Selected",
                "Please open a project before viewing its files."
            )

            self.pages.setCurrentIndex(1)
            return

        self.pages.setCurrentWidget(self.project_workspace)

        self.project_workspace.tabs.setCurrentWidget(
            self.project_workspace.files_tab
        )

    def show_team_from_sidebar(self):
        if self.current_project is None:
            QMessageBox.information(
                self,
                "No Project Selected",
                "Please open a project before viewing its team."
            )
            self.pages.setCurrentIndex(1)
            return

        self.pages.setCurrentWidget(self.project_workspace)

        self.project_workspace.tabs.setCurrentWidget(
            self.project_workspace.team_tab
        )