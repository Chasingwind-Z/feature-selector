
from PyQt5.QtWidgets import (QMainWindow, QLabel, QComboBox, QTextEdit, QVBoxLayout,
                             QWidget, QTableWidget, QMenuBar, QMenu, QSplitter, QStatusBar,
                             QAction, QDockWidget, QHBoxLayout, QFrame, QPushButton, QTabWidget,
                             QInputDialog, QHeaderView, QMenu, QTableWidgetItem, QLineEdit, QProgressBar)
from PyQt5.QtCore import Qt
from views.themes import LIGHT_THEME, DARK_THEME
from views.about_dialog import AboutDialog

class FeatureSelectorView(QMainWindow):
    def __init__(self):
        super().__init__()

        # GUI Components initialization
        self.init_ui()
        self.apply_theme(LIGHT_THEME)

    def init_ui(self):
        # Window settings
        self.setWindowTitle('Feature Selector')
        self.resize(1200, 800)

        # Menu Bar
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

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Progress Bar (for feature selection progress)
        self.progress_bar = QProgressBar()
        self.status_bar.addPermanentWidget(self.progress_bar)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)

    def apply_theme(self, theme):
        self.setStyleSheet(f'''
            QWidget {{
                background-color: {{theme['background']}};
                color: {{theme['foreground']}};
            }}
            QPushButton {{
                background-color: {{theme['button']}};
                color: {{theme['button_text']}};
            }}
            QPushButton:hover {{
                background-color: {{theme['highlight']}};
            }}
            QMenuBar::item:selected {{
                background-color: {{theme['highlight']}};
            }}
            QMenu::item:selected {{
                background-color: {{theme['highlight']}};
            }}
        ''')

    def add_new_data_table(self, title="Untitled", default_data=True):
        data_table = QTableWidget(10, 5)
        data_table.setContextMenuPolicy(Qt.CustomContextMenu)
        data_table.customContextMenuRequested.connect(self.show_table_context_menu)
        data_table.setHorizontalHeaderLabels([f"Column {{i}}" for i in range(5)])
        data_table.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        data_table.horizontalHeader().customContextMenuRequested.connect(self.show_header_context_menu)

        if default_data:
            for row in range(10):
                for col in range(5):
                    data_table.setItem(row, col, QTableWidgetItem(f"Item {{row}}-{{col}}"))

        self.data_tables.addTab(data_table, title)

    def close_tab(self, index):
        self.data_tables.removeTab(index)
        self.status_bar.showMessage(f"Closed tab {{index}}")

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
            self.rename_column(current_table.currentColumn())

    def show_header_context_menu(self, pos):
        global_pos = self.data_tables.currentWidget().horizontalHeader().mapToGlobal(pos)
        column_index = self.data_tables.currentWidget().horizontalHeader().logicalIndexAt(pos)
        menu = QMenu()
        set_target_action = QAction("Set as Target", self)
        set_target_action.triggered.connect(lambda: self.set_target_column(column_index))
        menu.addAction(set_target_action)
        menu.exec_(global_pos)

    def set_target_column(self, column_index):
        self.target_column_index = column_index
        current_table = self.data_tables.currentWidget()
        for row in range(current_table.rowCount()):
            current_table.item(row, column_index).setBackground(Qt.yellow)
        self.status_bar.showMessage(f"Set column {column_index} as Target")

    def rename_column(self, column_index):
        old_name = self.data_tables.currentWidget().horizontalHeaderItem(column_index).text()
        new_name, ok = QInputDialog.getText(self, "Rename Column", "New Name:", QLineEdit.Normal, old_name)
        if ok and new_name:
            self.data_tables.currentWidget().setHorizontalHeaderItem(column_index, QTableWidgetItem(new_name))
            self.status_bar.showMessage(f"Renamed column {old_name} to {new_name}")

    def update_progress(self, value):
        self.progress_bar.setValue(value)
