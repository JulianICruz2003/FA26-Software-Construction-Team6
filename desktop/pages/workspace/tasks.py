
import httpx

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QMessageBox,
)


class TasksTab(QWidget):
    def __init__(self, api_client):
        super().__init__()

        self.api_client = api_client
        self.project_id = None

        layout = QVBoxLayout(self)

        # Heading
        title = QLabel("Project Tasks")
        title.setObjectName("heading")
        layout.addWidget(title)

        self.project_label = QLabel("No project selected")
        layout.addWidget(self.project_label)

        # Task controls
        toolbar = QHBoxLayout()

        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Enter a task...")

        self.add_button = QPushButton("Add Task")

        toolbar.addWidget(self.task_input)
        toolbar.addWidget(self.add_button)
        layout.addLayout(toolbar)

        # Task table
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(2)
        self.task_table.setHorizontalHeaderLabels([
            "Task Name",
            "Status"
        ])

        self.task_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )

        self.task_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.task_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        layout.addWidget(self.task_table)

        # Complete task button
        self.complete_button = QPushButton("Mark Complete")
        layout.addWidget(self.complete_button)

        # Connect signals
        self.add_button.clicked.connect(self.add_task)
        self.task_input.returnPressed.connect(self.add_task)
        self.complete_button.clicked.connect(self.mark_complete)

    def load_tasks(self):
        if self.project_id is None:
            return

        try:
            tasks = self.api_client.get_tasks(self.project_id)

        except (httpx.HTTPError, ValueError) as error:
            QMessageBox.warning(
                self,
                "Connection Error",
                f"Could not load tasks:\n{error}"
            )
            return

        # Clear the table before loading database records
        self.task_table.setRowCount(0)

        for task in tasks:
            row = self.task_table.rowCount()
            self.task_table.insertRow(row)

            name_item = QTableWidgetItem(task["title"])

            # Save database task ID within the table item
            name_item.setData(
                Qt.ItemDataRole.UserRole,
                task["id"]
            )

            status_text = (
                "Complete" if task["is_complete"] else "Pending"
            )

            self.task_table.setItem(row, 0, name_item)
            self.task_table.setItem(
                row, 1, QTableWidgetItem(status_text)
            )

    def add_task(self):
        title = self.task_input.text().strip()

        if not title or self.project_id is None:
            return

        try:
            self.api_client.create_task(
                self.project_id,
                title
            )

        except httpx.HTTPError as error:
            QMessageBox.warning(
                self,
                "Save Failed",
                f"Could not save task:\n{error}"
            )
            return

        self.task_input.clear()
        self.load_tasks()

    def mark_complete(self):
        row = self.task_table.currentRow()

        if row < 0 or self.project_id is None:
            return

        item = self.task_table.item(row, 0)

        if item is None:
            return

        task_id = item.data(Qt.ItemDataRole.UserRole)

        try:
            self.api_client.update_task(
                self.project_id,
                task_id,
                True
            )

        except httpx.HTTPError as error:
            QMessageBox.warning(
                self,
                "Update Failed",
                f"Could not update task:\n{error}"
            )
            return

        self.load_tasks()

    def set_project(self, project):
        self.project_id = project["id"]

        self.project_label.setText(
            f"Tasks for: {project['name']}"
        )

        self.task_input.clear()

        # Retrieve tasks belonging to the selected project
        self.load_tasks()
