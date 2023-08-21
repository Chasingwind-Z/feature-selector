import pandas as pd
from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem, QMessageBox, QTableWidget, QInputDialog, QLineEdit
from views.feature_selection_dialog import FeatureSelectionDialog
from models.feature_selector_model import FeatureSelectorModel
from views.feature_selector_view import FeatureSelectorView
from views.themes import LIGHT_THEME, DARK_THEME


class FeatureSelectorController:
    def __init__(self):
        self.model = FeatureSelectorModel()
        self.view = FeatureSelectorView()
        self.feature_methods_dialog = FeatureSelectionDialog()

        self.current_theme = LIGHT_THEME
        self.setup_connections()
        self.view.show()

    def setup_connections(self):
        self.view.load_data_action.triggered.connect(self.load_data)
        self.view.new_file_action.triggered.connect(self.new_file)
        self.view.save_results_action.triggered.connect(self.save_results)
        self.view.save_file_action.triggered.connect(self.save_file)
        self.view.switch_theme_action.triggered.connect(self.switch_theme)
        self.view.run_action.triggered.connect(self.execute_selected_methods)
        self.view.feature_select_action.triggered.connect(self.open_feature_selection_dialog)
        self.view.rename_column_signal.connect(self.rename_column)
        self.view.set_target_column_signal.connect(self.set_target_column)

    def load_data(self):
        file_names, _ = QFileDialog.getOpenFileNames(self.view, "Open CSV", "", "CSV files (*.csv);;All files (*)")
        for file_name in file_names:
            if file_name:
                data = pd.read_csv(file_name)
                self.display_data_in_table(data, file_name)

    def new_file(self):
        self.view.add_new_data_table()
        self.view.status_bar.showMessage("New file created")

    def display_data_in_table(self, data, title="Untitled"):
        data_table = QTableWidget(data.shape[0], data.shape[1])
        data_table.setHorizontalHeaderLabels(data.columns)
        for row in range(data.shape[0]):
            for col in range(data.shape[1]):
                data_table.setItem(row, col, QTableWidgetItem(str(data.iloc[row, col])))
        self.view.data_tables.addTab(data_table, title.split('/')[-1])
        self.view.status_bar.showMessage(f"Loaded data from {title}")

    def save_results(self):
        file_name, _ = QFileDialog.getSaveFileName(self.view, "Save Results", "", "Text files (*.txt);;All files (*)")
        if file_name:
            with open(file_name, 'w') as f:
                f.write(self.view.results_text.toPlainText())
            self.view.status_bar.showMessage(f"Results saved to {file_name}")

    def save_file(self):
        current_table = self.view.data_tables.currentWidget()
        file_name, _ = QFileDialog.getSaveFileName(self.view, "Save File", "", "CSV files (*.csv);;All files (*)")
        if file_name:
            data = []
            for row in range(current_table.rowCount()):
                row_data = []
                for col in range(current_table.columnCount()):
                    item = current_table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)
            df = pd.DataFrame(data)
            df.to_csv(file_name, index=False, header=[header.text() for header in current_table.horizontalHeader().findItems()])
            self.view.status_bar.showMessage(f"File saved to {file_name}")

    def switch_theme(self):
        if self.current_theme == LIGHT_THEME:
            self.current_theme = DARK_THEME
        else:
            self.current_theme = LIGHT_THEME
        self.view.apply_theme(self.current_theme)

    def execute_selected_methods(self):
        # Check if the target column has been selected
        if self.model.target_column is None:
            target_column, ok = self.view.select_target_column()
            if ok:
                self.model.set_target_column(target_column)
                self.view.highlight_target_column(target_column)
            else:
                QMessageBox.warning(self.view, "Select Target", "Please select a target column before running.")
                return

        # Existing method execution logic (if any)
        # Implement running the feature selection
        self.view.status_bar.showMessage("Running feature selection...")
        self.view.update_progress(50)  # Example of updating the progress bar
        # Implement the actual feature selection logic here
        self.view.update_progress(100)  # Update the progress bar to 100% when done
        self.view.status_bar.showMessage("Feature selection completed.")

    def open_feature_selection_dialog(self):
        self.feature_methods_dialog.show()

    def rename_column(self, column_index):
        current_table = self.view.data_tables.currentWidget()
        old_name = current_table.horizontalHeaderItem(column_index).text()
        new_name, ok = QInputDialog.getText(self.view, "Rename Column", "New Name:", QLineEdit.Normal, old_name)
        if ok and new_name:
            current_table.setHorizontalHeaderItem(column_index, QTableWidgetItem(new_name))
            self.view.status_bar.showMessage(f"Renamed column {old_name} to {new_name}")

    def set_target_column(self, column_index):
        self.view.target_column_index = column_index
        current_table = self.view.data_tables.currentWidget()
        for row in range(current_table.rowCount()):
            current_table.item(row, column_index).setBackground(Qt.yellow)
        self.view.status_bar.showMessage(f"Set column {column_index} as Target")