from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (QMainWindow, QLabel, QComboBox, QTextEdit, QVBoxLayout,
                             QWidget, QTableWidget, QMenuBar, QMenu, QSplitter, QStatusBar,
                             QAction, QDockWidget, QHBoxLayout, QFrame, QPushButton, QTabWidget,
                             QInputDialog, QHeaderView, QMenu, QTableWidgetItem, QLineEdit, QProgressBar)
from PyQt5.QtCore import Qt
from views.themes import LIGHT_THEME, DARK_THEME
from views.about_dialog import AboutDialog


class FeatureSelectorView(QMainWindow):
    rename_column_signal = pyqtSignal(int)
    set_target_column_signal = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        # Initializing instance variables
        self.about_dialog = None
        self.status_bar = None
        self.progress_bar = None
        self.data_tables = None
        self.results_text = None
        self.results_layout = QVBoxLayout()  # Layout to display the results table

        # GUI Components initialization
        self.init_ui()
        self.apply_theme(LIGHT_THEME)

        self.target_column_index = None

    def init_ui(self):
        # Window settings
        self.setWindowTitle('Feature Selector')
        self.resize(1200, 800)

        # Initialize components
        self.init_menu_bar()
        self.init_status_bar()
        self.init_layout()

    def init_menu_bar(self):
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        file_menu = QMenu("File", self)
        self.new_file_action = QAction("New File", self)
        file_menu.addAction(self.new_file_action)

        self.load_data_action = QAction("Load Data", self)
        file_menu.addAction(self.load_data_action)

        self.save_results_action = QAction("Save Results", self)
        file_menu.addAction(self.save_results_action)

        self.save_file_action = QAction("Save File", self)
        file_menu.addAction(self.save_file_action)

        menu_bar.addMenu(file_menu)

        view_menu = QMenu("View", self)
        self.switch_theme_action = QAction("Switch Theme", self)
        view_menu.addAction(self.switch_theme_action)
        menu_bar.addMenu(view_menu)

        self.run_action = QAction("Run", self)
        menu_bar.addAction(self.run_action)

        settings_menu = QMenu("Settings", self)
        self.feature_select_action = QAction("Feature Selection Methods", self)
        settings_menu.addAction(self.feature_select_action)
        menu_bar.addMenu(settings_menu)

        help_menu = QMenu("Help", self)
        self.about_action = QAction("About", self)
        help_menu.addAction(self.about_action)
        menu_bar.addMenu(help_menu)

        self.setMenuBar(menu_bar)

        self.about_dialog = AboutDialog(self)
        self.about_action.triggered.connect(self.about_dialog.show)

    def init_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Progress Bar (for feature selection progress)
        self.progress_bar = QProgressBar()
        self.status_bar.addPermanentWidget(self.progress_bar)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)

    def init_layout(self):
        central_splitter = QSplitter(Qt.Horizontal, self)
        self.setCentralWidget(central_splitter)

        left_splitter = QSplitter(Qt.Vertical, self)

        self.data_tables = QTabWidget(self)
        left_splitter.addWidget(self.data_tables)
        self.data_tables.setTabsClosable(True)
        self.data_tables.tabCloseRequested.connect(self.close_tab)

        self.results_text = QTextEdit(self)
        left_splitter.addWidget(self.results_text)

        central_splitter.addWidget(left_splitter)

        right_panel = QDockWidget("Visualization", self)
        placeholder_label = QLabel("Graphs will be displayed here.", self)
        placeholder_label.setAlignment(Qt.AlignCenter)
        right_panel.setWidget(placeholder_label)
        central_splitter.addWidget(right_panel)

    def apply_theme(self, theme):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {theme['background']};
                color: {theme['foreground']};
            }}
            QPushButton {{
                background-color: {theme['button']};
                color: {theme['button_text']};
            }}
            QPushButton:hover {{
                background-color: {theme['highlight']};
            }}
            QMenuBar::item:selected {{
                background-color: {theme['highlight']};
            }}
            QMenu::item:selected {{
                background-color: {theme['highlight']};
            }}
        """)

    def add_new_data_table(self, title="Untitled", default_data=True):
        data_table = QTableWidget(10, 5)
        data_table.setContextMenuPolicy(Qt.CustomContextMenu)
        data_table.customContextMenuRequested.connect(self.show_table_context_menu)
        data_table.setHorizontalHeaderLabels([f"Column {i}" for i in range(5)])
        data_table.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        data_table.horizontalHeader().customContextMenuRequested.connect(self.show_header_context_menu)

        if default_data:
            for row in range(10):
                for col in range(5):
                    data_table.setItem(row, col, QTableWidgetItem(f"Item {row}-{col}"))

        self.data_tables.addTab(data_table, title)

    def close_tab(self, index):
        self.data_tables.removeTab(index)
        self.status_bar.showMessage(f"Closed tab {index}")

    def show_table_context_menu(self, position):
        current_table = self.data_tables.currentWidget()
        global_position = current_table.mapToGlobal(position)
        context_menu = QMenu(self)
        add_row_action = context_menu.addAction("Add Row")
        delete_row_action = context_menu.addAction("Delete Row")
        add_column_action = context_menu.addAction("Add Column")
        delete_column_action = context_menu.addAction("Delete Column")
        rename_column_action = context_menu.addAction("Rename Column")
        action = context_menu.exec_(global_position)

        if action == add_row_action:
            current_table.insertRow(current_table.rowCount())
        elif action == delete_row_action:
            current_table.removeRow(current_table.currentRow())
        elif action == add_column_action:
            current_table.insertColumn(current_table.columnCount())
        elif action == delete_column_action:
            current_table.removeColumn(current_table.currentColumn())
        elif action == rename_column_action:
            column_index = current_table.currentColumn()
            self.rename_column_signal.emit(column_index)

    def show_header_context_menu(self, pos):
        global_pos = self.data_tables.currentWidget().horizontalHeader().mapToGlobal(pos)
        column_index = self.data_tables.currentWidget().horizontalHeader().logicalIndexAt(pos)
        menu = QMenu()
        set_target_action = QAction("Set as Target", self)
        set_target_action.triggered.connect(lambda: self.set_target_column_signal.emit(column_index))
        menu.addAction(set_target_action)
        menu.exec_(global_pos)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def display_results(self, selected_data, results):
        self.results_text.clear()
        self.results_text.append("Feature Selection Results:")

        # Display details about feature selection methods
        for method_name, result in results.items():
            self.results_text.append(f"Method: {method_name}")
            self.results_text.append(f"Feature Subset Count: {result['feature_count']}")
            self.results_text.append(f"Removed Features: {', '.join(result['removed_features'])}")
            if 'score' in result:  # If the score is applicable
                self.results_text.append(f"Score: {result['score']}")
            self.results_text.append("-" * 40)

        # Create a table widget to display the selected data
        table_widget = QTableWidget()
        table_widget.setRowCount(min(100, len(selected_data)))
        table_widget.setColumnCount(len(selected_data.columns))
        table_widget.setHorizontalHeaderLabels(selected_data.columns)

        # Fill the table with data (up to 100 rows)
        for row_idx, row_data in selected_data.head(100).iterrows():
            for col_idx, value in enumerate(row_data):
                table_widget.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

        # Create a widget to hold the results layout
        results_widget = QWidget()
        results_widget.setLayout(self.results_layout)
        self.results_layout.addWidget(table_widget)

        # Add the results widget to the left splitter
        left_splitter = self.centralWidget().widget(0)
        left_splitter.addWidget(results_widget)


