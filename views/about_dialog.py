from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextBrowser

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        info_text = QTextBrowser()
        info_text.setText("Feature Selector\n\nVersion 1.0\n\nDeveloped by Zhu zhi fei")
        layout.addWidget(info_text)
        self.setLayout(layout)
        self.setWindowTitle("About")
        self.resize(400, 200)
