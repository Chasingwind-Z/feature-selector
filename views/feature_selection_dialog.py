from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel,
                             QLineEdit, QPushButton, QFormLayout, QScrollArea, QWidget)

class FeatureSelectionDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Feature Selection Methods Settings")
        self.setGeometry(300, 300, 400, 400)

        layout = QVBoxLayout()

        # Scroll Area for methods and their parameters
        self.scroll_area = QScrollArea(self)
        self.scroll_content = QWidget(self.scroll_area)
        self.form_layout = QFormLayout(self.scroll_content)

        # Add methods and parameters to the form layout
        self.methods = {
            "Missing Values": [("Threshold", QLineEdit("0.6"))],
            "Single Unique Value": [],
            "Collinear Features": [("Threshold", QLineEdit("0.95"))],
            "Zero Importance Features": [],
            "Statistical Tests": [("Top K Features", QLineEdit("10"))],
            "RFE Selection": [("Number of Features", QLineEdit("10"))],
            "Linear Model Selection": [("Threshold", QLineEdit("0.1"))]
        }

        for method, params in self.methods.items():
            checkbox = QCheckBox(method, self)
            self.form_layout.addRow(checkbox)
            for param_name, param_input in params:
                self.form_layout.addRow(QLabel(param_name), param_input)

        self.scroll_content.setLayout(self.form_layout)
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)

        # Save button
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save", self)
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel", self)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)
