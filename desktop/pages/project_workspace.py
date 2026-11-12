from desktop.pages.workspace.tasks import TasksTab
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTabWidget,
)

from desktop.pages.workspace.overview import OverviewTab

from desktop.pages.workspace.files import FilesTab
from desktop.pages.workspace.team import TeamTab

class ProjectWorkspacePage(QWidget):
    def __init__(self, api_client):
        super().__init__()

        layout = QVBoxLayout(self)

        # Project heading
        self.title = QLabel("Project Workspace")
        self.title.setObjectName("heading")

        self.project_id = QLabel("No project selected")

        layout.addWidget(self.title)
        layout.addWidget(self.project_id)

        # Create tab navigation
        self.tabs = QTabWidget()

        # Overview tab
        self.overview = OverviewTab()
        self.tabs.addTab(self.overview, "Overview")

        # Tasks tab
        self.tasks_tab = TasksTab(api_client)
        self.tabs.addTab(self.tasks_tab, "Tasks")

        # Files tab
        self.files_tab = FilesTab()
        self.tabs.addTab(self.files_tab, "Files")

        # Team tab
        self.team_tab = TeamTab(api_client)
        self.tabs.addTab(self.team_tab, "Team")


        # Placeholder tabs
        tab_names = [
            "Diagrams",
            "Activity"
        ]

        for name in tab_names:
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)

            label = QLabel(
                f"{name} features will be implemented here."
            )

            tab_layout.addWidget(label)
            tab_layout.addStretch()

            self.tabs.addTab(tab, name)

        layout.addWidget(self.tabs)

    def display_project(self, project):
        self.title.setText(project["name"])

        self.project_id.setText(
            f"Project ID: {project['id']}"
        )

        # Pass the selected project to the Overview tab
        self.overview.set_project(project)
        self.tasks_tab.set_project(project)
        self.files_tab.set_project(project)
        self.team_tab.set_project(project)

        self.tabs.setCurrentIndex(0)
