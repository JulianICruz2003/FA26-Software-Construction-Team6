
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
)


class OverviewTab(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Project description
        description_group = QGroupBox("Project Description")
        description_layout = QVBoxLayout(description_group)

        self.description = QLabel("No project selected.")
        self.description.setWordWrap(True)

        description_layout.addWidget(self.description)
        layout.addWidget(description_group)

        # Project information
        info_layout = QGridLayout()

        status_group = QGroupBox("Project Status")
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel("Not configured")
        status_layout.addWidget(self.status_label)

        deadline_group = QGroupBox("Deadline")
        deadline_layout = QVBoxLayout(deadline_group)
        self.deadline_label = QLabel("Not configured")
        deadline_layout.addWidget(self.deadline_label)

        tasks_group = QGroupBox("Tasks")
        tasks_layout = QVBoxLayout(tasks_group)
        self.tasks_label = QLabel("Not implemented")
        tasks_layout.addWidget(self.tasks_label)

        team_group = QGroupBox("Team Members")
        team_layout = QVBoxLayout(team_group)
        self.team_label = QLabel("Not implemented")
        team_layout.addWidget(self.team_label)

        info_layout.addWidget(status_group, 0, 0)
        info_layout.addWidget(deadline_group, 0, 1)
        info_layout.addWidget(tasks_group, 1, 0)
        info_layout.addWidget(team_group, 1, 1)

        layout.addLayout(info_layout)
        layout.addStretch()

    def set_project(self, project):
        # Update information from the selected project
        self.description.setText(
            project.get("description")
            or "No description provided."
        )
