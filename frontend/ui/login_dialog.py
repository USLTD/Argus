from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel

from frontend.core.user import User


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.user = None

        self.setWindowTitle("ARGUS Login")

        layout = QVBoxLayout(self)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")

        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)

        login_btn = QPushButton("Login")

        login_btn.clicked.connect(self.login)

        layout.addWidget(QLabel("Username"))

        layout.addWidget(self.username)

        layout.addWidget(self.password)

        layout.addWidget(login_btn)

    def login(self):

        username = self.username.text()

        if username.lower() == "admin":
            self.user = User(username, "Admin")

        else:
            self.user = User(username, "User")

        self.accept()
