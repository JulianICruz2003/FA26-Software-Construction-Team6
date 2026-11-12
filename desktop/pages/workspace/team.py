
import httpx

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class TeamTab(QWidget):
    def __init__(self, api_client):
        super().__init__()

        self.api_client = api_client
        self.project_id = None
        self.members = []

        layout = QVBoxLayout(self)

        heading = QLabel("Project Team")
        heading.setObjectName("heading")
        layout.addWidget(heading)

        self.project_label = QLabel("No project selected")
        layout.addWidget(self.project_label)

        # Create New is first so adding a new user is clear
        top_buttons = QHBoxLayout()

        self.create_button = QPushButton("Create New Member")
        self.add_button = QPushButton("Add Existing Member")

        top_buttons.addWidget(self.create_button)
        top_buttons.addWidget(self.add_button)
        top_buttons.addStretch()

        layout.addLayout(top_buttons)

        other_buttons = QHBoxLayout()

        self.remove_button = QPushButton("Remove Selected")
        self.refresh_button = QPushButton("Refresh")

        other_buttons.addWidget(self.remove_button)
        other_buttons.addWidget(self.refresh_button)
        other_buttons.addStretch()

        layout.addLayout(other_buttons)

        # Team table
        self.member_table = QTableWidget()
        self.member_table.setColumnCount(3)

        self.member_table.setHorizontalHeaderLabels([
            "Name",
            "Email",
            "Project Role"
        ])

        self.member_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.member_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.member_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.member_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        layout.addWidget(self.member_table)

        self.member_count = QLabel("0 team members")
        layout.addWidget(self.member_count)

        # Connect buttons
        self.create_button.clicked.connect(
            self.create_and_add_member
        )
        self.add_button.clicked.connect(self.add_member)
        self.remove_button.clicked.connect(self.remove_member)
        self.refresh_button.clicked.connect(self.load_members)

    def load_members(self):
        if self.project_id is None:
            return

        try:
            members = self.api_client.get_team_members(
                self.project_id
            )

        except (httpx.HTTPError, ValueError) as error:
            QMessageBox.warning(
                self,
                "Connection Error",
                f"Could not load team members:\n{error}"
            )
            return

        self.members = members
        self.member_table.setRowCount(0)

        for member in members:
            row = self.member_table.rowCount()
            self.member_table.insertRow(row)

            name_item = QTableWidgetItem(member["name"])

            name_item.setData(
                Qt.ItemDataRole.UserRole,
                member["id"]
            )

            self.member_table.setItem(row, 0, name_item)

            self.member_table.setItem(
                row, 1,
                QTableWidgetItem(member["email"])
            )

            self.member_table.setItem(
                row, 2,
                QTableWidgetItem(member["project_role"])
            )

        count = len(members)

        self.member_count.setText(
            f"{count} team member"
            if count == 1
            else f"{count} team members"
        )

    def add_member(self):
        # Add an existing user to the selected project
        if self.project_id is None:
            return

        try:
            users = self.api_client.get_users()

        except (httpx.HTTPError, ValueError) as error:
            QMessageBox.warning(
                self,
                "Connection Error",
                f"Could not retrieve users:\n{error}"
            )
            return

        existing_user_ids = {
            member["user_id"] for member in self.members
        }

        available_users = [
            user for user in users
            if user["id"] not in existing_user_ids
        ]

        if not available_users:
            # Automatically allow creation instead
            self.create_and_add_member()
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Add Existing Member")
        dialog.resize(450, 180)

        form = QFormLayout(dialog)

        user_input = QComboBox()

        for user in available_users:
            user_input.addItem(
                f"{user['name']} ({user['email']})",
                userData=user["id"]
            )

        role_input = QComboBox()
        role_input.addItems([
            "Member",
            "Team Lead",
            "Reviewer"
        ])

        form.addRow("User:", user_input)
        form.addRow("Project Role:", role_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        form.addRow(buttons)

        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            self.api_client.add_team_member(
                self.project_id,
                user_input.currentData(),
                role_input.currentText()
            )

        except httpx.HTTPError as error:
            QMessageBox.warning(
                self,
                "Save Failed",
                f"Could not add team member:\n{error}"
            )
            return

        self.load_members()

    def create_and_add_member(self):
        # Create a new development user and project membership
        if self.project_id is None:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Member")
        dialog.resize(450, 250)

        form = QFormLayout(dialog)

        name_input = QLineEdit()
        name_input.setPlaceholderText("Full name")

        email_input = QLineEdit()
        email_input.setPlaceholderText("Email address")

        account_role_input = QComboBox()
        account_role_input.addItems([
            "Student",
            "Professor"
        ])

        project_role_input = QComboBox()
        project_role_input.addItems([
            "Member",
            "Team Lead",
            "Reviewer"
        ])

        form.addRow("Name:", name_input)
        form.addRow("Email:", email_input)
        form.addRow("Account Type:", account_role_input)
        form.addRow("Project Role:", project_role_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        form.addRow(buttons)

        def validate():
            name = name_input.text().strip()
            email = email_input.text().strip()

            if (
                not name
                or email.count("@") != 1
                or " " in email
            ):
                QMessageBox.warning(
                    dialog,
                    "Invalid Information",
                    "Enter a name and a valid email address."
                )
                return

            dialog.accept()

        buttons.accepted.connect(validate)
        buttons.rejected.connect(dialog.reject)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            user = self.api_client.create_user(
                name_input.text().strip(),
                email_input.text().strip().lower(),
                account_role_input.currentText()
            )

        except httpx.HTTPStatusError as error:
            if error.response.status_code == 409:
                QMessageBox.information(
                    self,
                    "Account Already Exists",
                    "That email already belongs to an account. "
                    "Use 'Add Existing Member' instead."
                )
            else:
                QMessageBox.warning(
                    self,
                    "User Creation Failed",
                    f"Could not create user:\n{error}"
                )
            return

        except (httpx.HTTPError, ValueError) as error:
            QMessageBox.warning(
                self,
                "User Creation Failed",
                f"Could not create user:\n{error}"
            )
            return

        # Add the new user to the current project
        try:
            self.api_client.add_team_member(
                self.project_id,
                user["id"],
                project_role_input.currentText()
            )

        except httpx.HTTPError as error:
            QMessageBox.warning(
                self,
                "Membership Failed",
                "The user was created but was not added "
                "to this project. Use 'Add Existing Member' "
                "to try again.\n\n"
                f"{error}"
            )
            return

        self.load_members()

    def remove_member(self):
        if self.project_id is None:
            return

        row = self.member_table.currentRow()

        if row < 0:
            QMessageBox.information(
                self,
                "No Member Selected",
                "Please select a member to remove."
            )
            return

        item = self.member_table.item(row, 0)

        if item is None:
            return

        membership_id = item.data(
            Qt.ItemDataRole.UserRole
        )

        answer = QMessageBox.question(
            self,
            "Remove Team Member",
            f"Remove {item.text()} from this project?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.api_client.remove_team_member(
                self.project_id,
                membership_id
            )

        except httpx.HTTPError as error:
            QMessageBox.warning(
                self,
                "Removal Failed",
                f"Could not remove member:\n{error}"
            )
            return

        self.load_members()

    def set_project(self, project):
        self.project_id = project["id"]

        self.project_label.setText(
            f"Team for: {project['name']}"
        )

        self.members = []
        self.member_table.setRowCount(0)
        self.member_count.setText("Loading team members...")

        self.load_members()
