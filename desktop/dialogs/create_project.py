
from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QDateEdit,
    QMessageBox,
)


class CreateProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Create New Project")
        self.resize(420, 350)

        form = QFormLayout(self)

        # Project name
        self.project_name = QLineEdit()
        self.project_name.setPlaceholderText("Enter project name")

        # Project description
        self.description = QTextEdit()
        self.description.setPlaceholderText("Describe your project")
        self.description.setFixedHeight(80)

        # Deadline
        self.deadline = QDateEdit()
        self.deadline.setCalendarPopup(True)
        self.deadline.setDate(QDate.currentDate())
        self.deadline.setMinimumDate(QDate.currentDate())

        # Team name
        self.team_name = QLineEdit()
        self.team_name.setPlaceholderText("Optional team name")

        # Add fields to the form
        form.addRow("Project Name:", self.project_name)
        form.addRow("Description:", self.description)
        form.addRow("Deadline:", self.deadline)
        form.addRow("Team Name:", self.team_name)

        # Save and Cancel buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        form.addRow(buttons)

        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)

    def validate_and_accept(self):
        if not self.project_name.text().strip():
            QMessageBox.warning(
                self,
                "Missing Name",
                "Please enter a project name."
            )
            return

        self.accept()

    def get_data(self):
        return {
            "name": self.project_name.text().strip(),
            "description": self.description.toPlainText().strip(),
            "deadline": self.deadline.date().toString("yyyy-MM-dd"),
            "team_name": self.team_name.text().strip(),
        }
