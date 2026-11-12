import httpx

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem, QMessageBox

from PySide6.QtCore import Qt, Signal

from PySide6.QtWidgets import QDialog
from desktop.dialogs.create_project import CreateProjectDialog
from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QListWidget,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QTextEdit,
    QDateEdit,
    QMessageBox,
)


class ProjectsPage(QWidget):

    project_opened = Signal(dict)

    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client

        layout = QVBoxLayout(self)

        # Page heading
        title = QLabel("My Projects")
        title.setObjectName("heading")
        layout.addWidget(title)

        # Toolbar
        toolbar = QHBoxLayout()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search projects...")

        self.create_button = QPushButton("New Project")

        toolbar.addWidget(self.search)
        toolbar.addWidget(self.create_button)

        layout.addLayout(toolbar)

        # Sample projects
        self.project_list = QListWidget()

        layout.addWidget(self.project_list)

        # Connect signals
        self.search.textChanged.connect(self.filter_projects)
        self.create_button.clicked.connect(self.create_project)

        # Open a project when double-clicked
        self.project_list.itemDoubleClicked.connect(
            self.open_selected_project
        )

        # Load projects from PostgreSQL
        self.load_projects()

    def filter_projects(self, text):
        for row in range(self.project_list.count()):
            item = self.project_list.item(row)
            item.setHidden(
                text.lower() not in item.text().lower()
            )

    def load_projects(self):
        try:
            projects = self.api_client.get_projects()

        except (httpx.HTTPError, ValueError) as error:
            QMessageBox.warning(
                self,
                "Connection Error",
                f"Could not load projects:\n{error}"
            )
            return

        self.project_list.clear()

        for project in projects:
            item = QListWidgetItem(project["name"])

            # Store the database ID with the list item
            item.setData(
                Qt.ItemDataRole.UserRole,
                project
            )

            self.project_list.addItem(item)

        # Preserve the existing search filter
        self.filter_projects(self.search.text())

    

    def create_project(self):
        dialog = CreateProjectDialog(self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            project_data = dialog.get_data()

            try:
                self.api_client.create_project(
                    project_data["name"],
                    project_data["description"]
                )

            except httpx.HTTPError as error:
                QMessageBox.warning(
                    self,
                    "Save Failed",
                    f"Could not save project:\n{error}"
                )
                return

            # Reload the project list from PostgreSQL
            self.load_projects()

    def open_selected_project(self, item):
        project = item.data(Qt.ItemDataRole.UserRole)

        if project:
            self.project_opened.emit(project)
