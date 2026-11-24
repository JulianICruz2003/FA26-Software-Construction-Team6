import pytest
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication
from shiboken6 import isValid


@pytest.fixture(scope="session")
def qt_app():
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("QT_QPA_PLATFORM", "offscreen")
        existing_app = QApplication.instance()
        app = existing_app if existing_app is not None else QApplication([])
        try:
            yield app
        finally:
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            if existing_app is None:
                app.shutdown()


@pytest.fixture
def qt_widget(qt_app):
    widgets = []

    def create(widget_type, *args, **kwargs):
        widget = widget_type(*args, **kwargs)
        widgets.append(widget)
        return widget

    yield create

    # Keep the Python wrappers alive while Qt destroys the native widgets,
    # their children, and their signal connections on the GUI thread.
    for widget in reversed(widgets):
        if isValid(widget):
            widget.close()
            widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
