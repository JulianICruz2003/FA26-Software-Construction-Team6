
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
)


class FilesTab(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        # Page heading
        title = QLabel("Project Files")
        title.setObjectName("heading")
        layout.addWidget(title)

        self.project_label = QLabel("No project selected")
        layout.addWidget(self.project_label)

        # File controls
        toolbar = QHBoxLayout()

        self.add_button = QPushButton("Add Files")
        self.remove_button = QPushButton("Remove Selected")

        toolbar.addWidget(self.add_button)
        toolbar.addWidget(self.remove_button)
        toolbar.addStretch()

        layout.addLayout(toolbar)

        # File table
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(3)

        self.file_table.setHorizontalHeaderLabels([
            "File Name",
            "Type",
            "Size"
        ])

        self.file_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )

        self.file_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.file_table.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )

        self.file_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        layout.addWidget(self.file_table)

        # File count
        self.file_count = QLabel("0 local files selected")
        layout.addWidget(self.file_count)

        # Track selected file paths
        self.selected_paths = set()

        # Connect buttons
        self.add_button.clicked.connect(self.add_files)
        self.remove_button.clicked.connect(self.remove_files)

    def add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files",
            "",
            "All Files (*)"
        )

        for file_path in paths:
            if file_path in self.selected_paths:
                continue

            path = Path(file_path)

            try:
                size_bytes = path.stat().st_size
            except OSError:
                continue

            row = self.file_table.rowCount()
            self.file_table.insertRow(row)

            name_item = QTableWidgetItem(path.name)
            name_item.setData(256, file_path)

            file_type = path.suffix or "File"
            size = f"{size_bytes / 1024:.1f} KB"

            self.file_table.setItem(row, 0, name_item)
            self.file_table.setItem(
                row, 1, QTableWidgetItem(file_type)
            )
            self.file_table.setItem(
                row, 2, QTableWidgetItem(size)
            )

            self.selected_paths.add(file_path)

        self.update_file_count()

    def remove_files(self):
        rows = sorted(
            {index.row() for index in
             self.file_table.selectedIndexes()},
            reverse=True
        )

        for row in rows:
            item = self.file_table.item(row, 0)
            self.selected_paths.discard(item.data(256))
            self.file_table.removeRow(row)

        self.update_file_count()

    def update_file_count(self):
        count = self.file_table.rowCount()
        self.file_count.setText(
            f"{count} local files selected (not uploaded)"
        )

    def set_project(self, project):
        self.project_label.setText(
            f"Files for: {project['name']}"
        )

        # Clear local selections for the new project
        self.file_table.setRowCount(0)
        self.selected_paths.clear()
        self.update_file_count()
