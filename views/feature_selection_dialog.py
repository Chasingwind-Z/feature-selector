from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel,
                             QLineEdit, QPushButton, QFormLayout, QScrollArea, QWidget, QMessageBox)


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
            "Missing Values": [("Threshold (0-1)", QLineEdit("0.6"))],
            "Single Unique Value": [],
            "Collinear Features": [("Threshold (0-1)", QLineEdit("0.95"))],
            "Zero Importance Features": [],
            "Statistical Tests": [("Top K Features (positive integer)", QLineEdit("10"))],
            "RFE Selection": [("Number of Features (positive integer)", QLineEdit("10"))],
            "Linear Model Selection": [("Threshold (positive float)", QLineEdit("0.1"))]
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

    def validate_threshold(self, value):
        try:
            value = float(value)
            return 0 <= value <= 1
        except ValueError:
            return False

    def validate_positive_integer(self, value):
        try:
            value = int(value)
            return value > 0
        except ValueError:
            return False

    def validate_positive_float(self, value):
        try:
            value = float(value)
            return value > 0
        except ValueError:
            return False

    def accept(self):
        validation_errors = []

        # Validate the Missing Values threshold
        threshold_value = self.methods["Missing Values"][0][1].text()
        if not self.validate_threshold(threshold_value):
            validation_errors.append("Missing Values threshold must be between 0 and 1.")

        # Validate the Collinear Features threshold
        threshold_value = self.methods["Collinear Features"][0][1].text()
        if not self.validate_threshold(threshold_value):
            validation_errors.append("Collinear Features threshold must be between 0 and 1.")

        # Validate Top K Features
        top_k_value = self.methods["Statistical Tests"][0][1].text()
        if not self.validate_positive_integer(top_k_value):
            validation_errors.append("Top K Features must be a positive integer.")

        # Validate Number of Features for RFE Selection
        num_features_value = self.methods["RFE Selection"][0][1].text()
        if not self.validate_positive_integer(num_features_value):
            validation_errors.append("Number of Features for RFE Selection must be a positive integer.")

        # Validate Threshold for Linear Model Selection
        threshold_value = self.methods["Linear Model Selection"][0][1].text()
        if not self.validate_positive_float(threshold_value):
            validation_errors.append("Threshold for Linear Model Selection must be a positive float.")

        if validation_errors:
            error_message = "\n".join(validation_errors)
            QMessageBox.warning(self, "Validation Error", error_message)
        else:
            super().accept()

    def get_selected_methods(self):
        selected_methods = {}
        for row in range(self.form_layout.rowCount()):
            widget = self.form_layout.itemAt(row, QFormLayout.FieldRole).widget()
            if isinstance(widget, QCheckBox) and widget.isChecked():
                method_name = widget.text()
                params = {}
                for param_name, param_input in self.methods[method_name]:
                    params[param_name] = float(param_input.text())
                selected_methods[method_name] = params
        return selected_methods
