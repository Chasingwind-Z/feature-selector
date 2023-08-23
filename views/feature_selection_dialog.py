from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel,
                             QLineEdit, QPushButton, QScrollArea, QWidget, QMessageBox, QComboBox,
                             QGroupBox)


class FeatureSelectionDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.keep_one_hot_combo = None
        self.keep_one_hot = None
        self.selected_methods = None
        self.methods_checkboxes = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Feature Selection Methods Settings")
        self.setGeometry(200, 200, 900, 600)

        layout = QVBoxLayout()

        # Keep One Hot Encoding option
        keep_one_hot_layout = QHBoxLayout()
        keep_one_hot_label = QLabel("Keep One Hot Encoding:")
        self.keep_one_hot_combo = QComboBox()
        self.keep_one_hot_combo.addItem('True')
        self.keep_one_hot_combo.addItem('False')
        keep_one_hot_layout.addWidget(keep_one_hot_label)
        keep_one_hot_layout.addWidget(self.keep_one_hot_combo)
        layout.addLayout(keep_one_hot_layout)

        # Scroll Area for methods selection
        scroll_layout = QVBoxLayout()

        # Method configurations
        methods_config = [
            ("Missing Values", QLineEdit("0.6"), "Threshold: 0 to 1", "missing_threshold"),
            ("Single Unique Value", None, None, None),
            ("Collinear Features", QLineEdit("0.975"), "Threshold: 0 to 1", "correlation_threshold"),
            ("Zero Importance Features", None, "Settings for Zero Importance Features", None),
            ("Low Importance Features", QLineEdit("0.99"), "Threshold: 0 to 1", "cumulative_importance")
        ]

        self.methods_checkboxes = {}

        for method_name, parameter_widget, range_text, param_name in methods_config:
            group_box = QGroupBox(method_name)
            group_box_layout = QVBoxLayout()

            # Add checkbox for each method
            checkbox = QCheckBox("Enable")
            group_box_layout.addWidget(checkbox)

            if parameter_widget:
                parameter_widget.setMaximumWidth(100)

            if method_name == "Zero Importance Features":
                hbox = QHBoxLayout()
                task_combobox = QComboBox()
                task_combobox.addItems(['classification', 'regression'])
                eval_metric_combobox = QComboBox()
                eval_metric_combobox.addItems(['auc', 'l2'])
                n_iterations_line_edit = QLineEdit("10")
                early_stopping_checkbox = QCheckBox("Early Stopping")
                early_stopping_checkbox.setChecked(True)
                hbox.addWidget(QLabel("Task:"))
                hbox.addWidget(task_combobox)
                hbox.addWidget(QLabel("Eval Metric:"))
                hbox.addWidget(eval_metric_combobox)
                hbox.addWidget(QLabel("Iterations:"))
                hbox.addWidget(n_iterations_line_edit)
                hbox.addWidget(early_stopping_checkbox)
                group_box_layout.addLayout(hbox)
                # Connect to the special method for zero importance checkbox
                checkbox.stateChanged.connect(self.on_zero_importance_checkbox_changed)
                self.methods_checkboxes[method_name] = (
                    checkbox, (task_combobox, eval_metric_combobox, n_iterations_line_edit, early_stopping_checkbox))
            else:
                if parameter_widget and param_name:
                    hbox = QHBoxLayout()
                    hbox.addWidget(QLabel(f"{param_name.capitalize()}:"))
                    hbox.addWidget(parameter_widget)
                    if range_text:
                        hbox.addWidget(QLabel(range_text))
                    group_box_layout.addLayout(hbox)
                self.methods_checkboxes[method_name] = (checkbox, parameter_widget)

            group_box.setLayout(group_box_layout)
            scroll_layout.addWidget(group_box)

        # 初始化时禁用 "Low Importance Features" 的复选框
        low_importance_checkbox = self.methods_checkboxes["Low Importance Features"][0]
        low_importance_checkbox.setEnabled(False)

        scroll_widget = QWidget()
        scroll_widget.setLayout(scroll_layout)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        # Buttons
        btn_layout = QHBoxLayout()
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_selection)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(apply_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def on_zero_importance_checkbox_changed(self, state):
        try:
            # 获取 "Low Importance Features" 的复选框
            low_importance_checkbox = self.methods_checkboxes["Low Importance Features"][0]

            # 如果 "Zero Importance Features" 复选框被选中，则启用 "Low Importance Features" 复选框
            if state == Qt.Checked:
                low_importance_checkbox.setEnabled(True)
            else:
                # 如果 "Zero Importance Features" 复选框未选中，则取消选中并禁用 "Low Importance Features" 复选框
                low_importance_checkbox.setChecked(False)
                low_importance_checkbox.setEnabled(False)
        except Exception as e:
            print("An error occurred:", e)

    def apply_selection(self):
        try:
            selected_methods = {}
            validation_errors = []

            # Missing Values
            checkbox, threshold_widget = self.methods_checkboxes["Missing Values"]
            if checkbox.isChecked():
                threshold = threshold_widget.text()
                error_message = self.validate_parameter("Missing Values", threshold)
                if error_message:
                    validation_errors.append(error_message)
                else:
                    selected_methods["Missing Values"] = {"missing_threshold": float(threshold)}

            # Single Unique Value
            checkbox, _ = self.methods_checkboxes["Single Unique Value"]
            if checkbox.isChecked():
                selected_methods["Single Unique Value"] = {}

            # Collinear Features
            checkbox, threshold_widget = self.methods_checkboxes["Collinear Features"]
            if checkbox.isChecked():
                threshold = threshold_widget.text()
                error_message = self.validate_parameter("Collinear Features", threshold)
                if error_message:
                    validation_errors.append(error_message)
                else:
                    selected_methods["Collinear Features"] = {"correlation_threshold": float(threshold)}

            # Zero Importance Features
            checkbox, zero_importance_widgets = self.methods_checkboxes["Zero Importance Features"]
            if checkbox.isChecked():
                task_combobox, eval_metric_combobox, n_iterations_line_edit, early_stopping_checkbox = zero_importance_widgets
                task = task_combobox.currentText()
                eval_metric = eval_metric_combobox.currentText()
                n_iterations = n_iterations_line_edit.text()
                early_stopping = early_stopping_checkbox.isChecked()
                param_values = (task, eval_metric, n_iterations, early_stopping)

                error_message = self.validate_parameter("Zero Importance Features", param_values)
                if error_message:
                    validation_errors.append(error_message)
                else:
                    selected_methods["Zero Importance Features"] = {
                        "task": task,
                        "eval_metric": eval_metric,
                        "n_iterations": int(n_iterations),
                        "early_stopping": early_stopping
                    }

            # Low Importance Features
            checkbox, cumulative_importance_threshold_widget = self.methods_checkboxes["Low Importance Features"]
            if checkbox.isChecked():
                cumulative_importance_threshold = cumulative_importance_threshold_widget.text()
                error_message = self.validate_parameter("Low Importance Features", cumulative_importance_threshold)
                if error_message:
                    validation_errors.append(error_message)
                else:
                    selected_methods["Low Importance Features"] = {
                        "cumulative_importance_threshold": float(cumulative_importance_threshold)
                    }

            # If there are validation errors, show them and do not proceed
            if validation_errors:
                error_message = "\n".join(validation_errors)
                QMessageBox.critical(self, "Validation Errors", error_message)
                return

            self.selected_methods = selected_methods
            # Get the value from the Keep One Hot combo box
            self.keep_one_hot = self.keep_one_hot_combo.currentText()
            print(self.keep_one_hot)

            self.accept()
        except Exception as e:
            print("An error occurred in apply_selection:", str(e))
            import traceback
            traceback.print_exc()

    def validate_parameter(self, method_name, param_values):
        print("Validating method:", method_name)

        if method_name == "Missing Values":
            try:
                threshold = float(param_values)
                if 0 <= threshold <= 1:
                    return None
                else:
                    return "Missing Values threshold must be between 0 and 1."
            except ValueError:
                return "Missing Values threshold must be a number."

        elif method_name == "Collinear Features":
            try:
                correlation_threshold = float(param_values)
                if 0 <= correlation_threshold <= 1:
                    return None
                else:
                    return "Collinear Features threshold must be between 0 and 1."
            except ValueError:
                return "Collinear Features threshold must be a number."

        elif method_name == "Zero Importance Features":
            task, eval_metric, n_iterations, early_stopping = param_values
            if task not in ["classification", "regression"]:
                return "Invalid task value for Zero Importance Features."
            if eval_metric not in ["auc", "l2"]:
                return "Invalid eval_metric value for Zero Importance Features."
            try:
                n_iterations = int(n_iterations)
                if n_iterations <= 0:
                    return "n_iterations must be greater than 0 for Zero Importance Features."
            except ValueError:
                return "n_iterations must be an integer for Zero Importance Features."
            if not isinstance(early_stopping, bool):
                return "Invalid early_stopping value for Zero Importance Features."
            return None

        elif method_name == "Low Importance Features":
            try:
                cumulative_importance_threshold = float(param_values)
                if 0 <= cumulative_importance_threshold <= 1:
                    return None
                else:
                    return "Low Importance Features threshold must be between 0 and 1."
            except ValueError:
                return "Low Importance Features threshold must be a number."

        return "Unknown method."

    def get_selected_methods(self):
        return self.selected_methods

    def get_one_hot(self):
        return self.keep_one_hot
