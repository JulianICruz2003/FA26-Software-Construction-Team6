"""Shared presentation for role dashboards and their feature pages."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)


def text_label(text, style=""):
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(True)
    label.setObjectName(style)
    return label


class DashboardPage(QScrollArea):
    action_requested = Signal(str)

    def __init__(self, title, name, introduction, summaries, actions, sections):
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)
        self.setWidget(content)

        hero = QFrame(objectName="dashboardHero")
        hero_layout = QVBoxLayout(hero)
        self.title = text_label(title, "heading")
        hero_layout.addWidget(self.title)
        hero_layout.addWidget(text_label(f"Welcome, {name}", "sectionTitle"))
        hero_layout.addWidget(text_label(introduction, "subtitle"))
        layout.addWidget(hero)

        cards = QGridLayout()
        for index, (label, availability) in enumerate(summaries):
            card = QFrame(objectName="dashboardCard")
            card_layout = QVBoxLayout(card)
            card_layout.addWidget(text_label(label, "sectionTitle"))
            card_layout.addWidget(text_label(availability, "subtitle"))
            cards.addWidget(card, index // 2, index % 2)
        cards.setColumnStretch(0, 1)
        cards.setColumnStretch(1, 1)
        layout.addLayout(cards)

        layout.addWidget(text_label("Quick Actions", "sectionTitle"))
        buttons = QGridLayout()
        self.quick_actions = {}
        for index, (label, destination) in enumerate(actions):
            button = QPushButton(label, objectName="dashboardAction")
            button.clicked.connect(
                lambda checked=False, page=destination: self.action_requested.emit(page)
            )
            self.quick_actions[label] = button
            buttons.addWidget(button, index // 2, index % 2)
        buttons.setColumnStretch(0, 1)
        buttons.setColumnStretch(1, 1)
        layout.addLayout(buttons)

        for title, description in sections:
            panel = QFrame(objectName="dashboardCard")
            panel_layout = QVBoxLayout(panel)
            panel_layout.addWidget(text_label(title, "sectionTitle"))
            panel_layout.addWidget(text_label(description, "subtitle"))
            layout.addWidget(panel)
        layout.addStretch()


class FeaturePage(QWidget):
    def __init__(self, title, description):
        super().__init__()
        self.layout_box = QVBoxLayout(self)
        self.layout_box.setContentsMargins(24, 20, 24, 24)
        self.layout_box.setSpacing(14)
        self.title = text_label(title, "heading")
        self.layout_box.addWidget(self.title)
        self.status = text_label(description, "subtitle")
        self.layout_box.addWidget(self.status)
        self.layout_box.addStretch()

    def add_action(self, label, callback):
        button = QPushButton(label, objectName="dashboardAction")
        button.clicked.connect(callback)
        self.layout_box.insertWidget(
            self.layout_box.count() - 1, button, alignment=Qt.AlignmentFlag.AlignLeft
        )
