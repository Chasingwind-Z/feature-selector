import sys
import os
import pandas as pd
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, QComboBox, 
                             QTextEdit, QVBoxLayout, QWidget, QFileDialog)
from PyQt5.QtCore import Qt

class FeatureSelectorGUI(QMainWindow):

    def __init__(self):
        super().__init__()

        # Attributes
        self.data = None

        self.init_ui()

    def init_ui(self):
        # Window settings
        self.setWindowTitle('Feature Selector')
        self.resize(500, 400)

        # Load data button
        self.load_data_btn = QPushButton('Load Data', self)
        self.load_data_btn.clicked.connect(self.load_data)

        # Data info label
        self.data_info_lbl = QLabel('Data not loaded', self)
        self.data_info_lbl.setAlignment(Qt.AlignCenter)

        # Feature selection methods dropdown
        self.feature_methods_combo = QComboBox(self)
        self.feature_methods_combo.addItems(['Random Selection'])  # Sample method

        # Run button
        self.run_btn = QPushButton('Run', self)
        self.run_btn.clicked.connect(self.run_feature_selection)

        # Results text box
        self.selected_features_txt = QTextEdit(self)

        # Save button
        self.save_btn = QPushButton('Save Results', self)
        self.save_btn.clicked.connect(self.save_results)

        # Layout settings
        layout = QVBoxLayout()
        layout.addWidget(self.load_data_btn)
        layout.addWidget(self.data_info_lbl)
        layout.addWidget(self.feature_methods_combo)
        layout.addWidget(self.run_btn)
        layout.addWidget(self.selected_features_txt)
        layout.addWidget(self.save_btn)

        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def load_data(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV files (*.csv);;All files (*)")
        
        if file_name:
            self.data = pd.read_csv(file_name)
            self.data_info_lbl.setText(os.path.basename(file_name))

    def run_feature_selection(self):
        if self.data is not None:
            # Simulating feature selection
            columns = list(self.data.columns)
            selected_features = random.sample(columns, min(5, len(columns)))
            
            self.selected_features_txt.setPlainText("\n".join(selected_features))
        else:
            self.selected_features_txt.setPlainText("Please load data first.")

    def save_results(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Results", "", "Text files (*.txt);;All files (*)")
        
        if file_name:
            with open(file_name, 'w') as f:
                f.write(self.selected_features_txt.toPlainText())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = FeatureSelectorGUI()
    main_win.show()
    sys.exit(app.exec_())
