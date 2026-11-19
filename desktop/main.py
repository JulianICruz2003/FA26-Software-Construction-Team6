
import sys

import httpx
from PySide6.QtWidgets import QApplication, QDialog

from desktop.app_window import MainWindow
from desktop.dialogs.login_dialog import LoginDialog
from desktop.services.api_client import ApiClient


def main():
    app = QApplication(sys.argv)
    api_client = ApiClient()

    while True:
        # Require sign in before showing the main window
        login = LoginDialog(api_client)
        if login.exec() != QDialog.DialogCode.Accepted:
            return 0

        window = MainWindow(api_client, login.current_user)
        window.show()
        app.exec()

        if not window.sign_out_requested:
            # Window was closed without signing out, so end the session
            try:
                api_client.logout()
            except httpx.HTTPError:
                pass
            return 0


if __name__ == "__main__":
    sys.exit(main())
