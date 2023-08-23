import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem, QMessageBox, QTableWidget, QInputDialog, QLineEdit
from views.feature_selection_dialog import FeatureSelectionDialog
from models.feature_selector_model import FeatureSelectorModel
from views.feature_selector_view import FeatureSelectorView
from views.themes import LIGHT_THEME, DARK_THEME


class FeatureSelectorController:
    def __init__(self):
        self.data = None
        self.result_data = None
        self.model = FeatureSelectorModel()
        self.view = FeatureSelectorView()
        self.feature_methods_dialog = FeatureSelectionDialog()

        self.current_theme = LIGHT_THEME
        self.setup_connections()
        self.view.show()

    def setup_connections(self):
        self.view.load_data_action.triggered.connect(self.load_data)
        self.view.new_file_action.triggered.connect(self.new_file)
        self.view.save_file_action.triggered.connect(self.save_file)
        self.view.save_results_button.clicked.connect(self.save_results)
        self.view.stop_button.clicked.connect(self.stop_execution)
        self.view.switch_theme_action.triggered.connect(self.switch_theme)
        self.view.run_action.triggered.connect(self.execute_selected_methods)
        self.view.feature_select_action.triggered.connect(self.open_feature_selection_dialog)
        self.view.rename_column_signal.connect(self.rename_column)
        self.view.set_target_column_signal.connect(self.set_target_column)

    def load_data(self):
        file_names, _ = QFileDialog.getOpenFileNames(self.view, "Open CSV", "", "CSV files (*.csv);;All files (*)")
        for file_name in file_names:
            if file_name:
                self.data = pd.read_csv(file_name)
                self.display_data_in_table(self.data, file_name)

    def new_file(self):
        self.view.add_new_data_table()
        self.view.status_bar.showMessage("New file created")

    def display_data_in_table(self, data, title="Untitled"):
        data_table = QTableWidget(data.shape[0], data.shape[1])
        data_table.setHorizontalHeaderLabels(data.columns)
        data_table.setContextMenuPolicy(Qt.CustomContextMenu)  # Set custom context menu policy
        data_table.customContextMenuRequested.connect(
            self.view.show_table_context_menu)  # Connect to the context menu slot
        data_table.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        data_table.horizontalHeader().customContextMenuRequested.connect(
            self.view.show_header_context_menu)  # Connect to the header context menu slot

        for row in range(data.shape[0]):
            for col in range(data.shape[1]):
                data_table.setItem(row, col, QTableWidgetItem(str(data.iloc[row, col])))
        self.view.data_tables.addTab(data_table, title.split('/')[-1])
        self.view.status_bar.showMessage(f"Loaded data from {title}")

    def stop_execution(self):
        # 这里添加停止执行的代码

        # 隐藏Stop按钮
        self.view.hide_stop_button()

    def save_results(self):
        file_name, _ = QFileDialog.getSaveFileName(self.view, "Save Results", "", "Text files (*.txt);;All files (*)")
        if file_name:
            with open(file_name, 'w') as f:
                f.write(self.view.results_text.toPlainText())
            self.view.status_bar.showMessage(f"Results saved to {file_name}")

    def save_file(self):
        try:
            current_table = self.view.data_tables.currentWidget()
            file_name, _ = QFileDialog.getSaveFileName(self.view, "Save File", "", "CSV files (*.csv);;All files (*)")
            if file_name:
                self.view.status_bar.showMessage("Saving file...")
                data = []
                headers = [current_table.horizontalHeaderItem(col).text() for col in range(current_table.columnCount())]
                for row in range(current_table.rowCount()):
                    row_data = []
                    for col in range(current_table.columnCount()):
                        item = current_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    data.append(row_data)
                df = pd.DataFrame(data, columns=headers)
                df.to_csv(file_name, index=False)
                self.view.status_bar.showMessage(f"File saved to {file_name}")
        except Exception as e:
            QMessageBox.critical(self.view, "Error", f"An error occurred while saving the file: {str(e)}")
            self.view.status_bar.showMessage("Error saving file.")

    def switch_theme(self):
        if self.current_theme == LIGHT_THEME:
            self.current_theme = DARK_THEME
        else:
            self.current_theme = LIGHT_THEME
        self.view.apply_theme(self.current_theme)

    def execute_selected_methods(self):
        # Check if data has been loaded in the GUI
        if self.view.data_tables.count() == 0:
            QMessageBox.warning(self.view, "No Data", "Please load data before running.")
            return

        # Get the selected methods and parameters from the dialog
        methods = self.feature_methods_dialog.get_selected_methods()
        keep_one_hot = self.feature_methods_dialog.get_one_hot() == 'True'
        if methods is None:
            QMessageBox.warning(self.view, "Select Methods", "Please select methods before running.")
            return

        # Check if the target column has been set
        if self.view.target_column_index is None:
            QMessageBox.warning(self.view, "Select Target", "Please select a target column before running.")
            return

        # 显示Stop按钮
        self.view.show_stop_button()

        # Get the target column name
        current_table = self.view.data_tables.currentWidget()
        target_column_name = current_table.horizontalHeaderItem(self.view.target_column_index).text()

        # Extract data from the current table
        data = self.data

        # Load the data in the model
        self.model.load_data(data)

        # try:
        #     success = self.model.method_result_signal.connect(self.view.display_method_result)
        #     print("Connection success:", success)
        # except Exception as e:
        #     print("Exception occurred during connection:", e)
        #
        # try:
        #     success = self.model.method_result_signal.connect(self.view.display_final_results)
        #     print("Connection success:", success)
        # except Exception as e:
        #     print("Exception occurred during connection:", e)

        # Connect signals to slots for updating the view
        self.model.method_result_signal.connect(self.view.display_method_result)
        self.model.final_results_signal.connect(self.view.display_final_results)

        # Perform feature selection in the model
        result_data = self.model.select_features(methods, target_column_name, keep_one_hot)

        # 隐藏Stop按钮，显示Save Results按钮
        self.view.hide_stop_button()
        self.view.show_save_results_button()

        # Save the result data for further use
        self.result_data = result_data

        # Disconnect the signals to avoid any unwanted connections
        self.model.method_result_signal.disconnect(self.view.display_method_result)
        self.model.final_results_signal.disconnect(self.view.display_final_results)

    def open_feature_selection_dialog(self):
        self.feature_methods_dialog.exec_()

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

    # def extract_data_from_table(self, current_table):
    #     rows, cols = current_table.rowCount(), current_table.columnCount()
    #     data = []
    #     for row in range(rows):
    #         row_data = []
    #         for col in range(cols):
    #             item = current_table.item(row, col)
    #             row_data.append(item.text() if item else "")
    #         data.append(row_data)
    #
    #     headers = [current_table.horizontalHeaderItem(col).text() for col in range(cols)]
    #     df = pd.DataFrame(data, columns=headers)
    #     return df
