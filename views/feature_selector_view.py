from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import (QMainWindow, QLabel, QTextEdit, QVBoxLayout,
                             QWidget, QTableWidget, QMenuBar, QSplitter, QStatusBar,
                             QAction, QDockWidget, QHBoxLayout, QPushButton, QTabWidget,
                             QMenu, QTableWidgetItem)
from PyQt5.QtCore import Qt
from views.themes import LIGHT_THEME, DARK_THEME
from views.about_dialog import AboutDialog


class FeatureSelectorView(QMainWindow):
    rename_column_signal = pyqtSignal(int)
    set_target_column_signal = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        # Initializing instance variables
        self.about_action = None
        self.feature_select_action = None
        self.run_action = None
        self.save_file_action = None
        self.load_data_action = None
        self.switch_theme_action = None
        self.new_file_action = None
        self.about_dialog = None
        self.status_bar = None
        self.data_tables = None
        self.results_text = None
        self.results_layout = QVBoxLayout()  # Layout to display the results table

        # 创建Stop和Save Results按钮，并设置为初始隐藏
        self.stop_button = QPushButton("Stop")
        self.stop_button.setVisible(False)  # 初始设置为隐藏
        self.save_results_button = QPushButton("Save Results")
        self.save_results_button.setFixedWidth(100)  # 设置按钮的宽度
        self.save_results_button.setVisible(False)  # 初始设置为隐藏

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

        # Create a widget to hold the results layout
        results_widget = QWidget()
        results_widget.setLayout(self.results_layout)

        # 将Stop和Save Results按钮添加到结果布局，并将Save Results按钮移到最左侧
        results_buttons_layout = QHBoxLayout()
        results_buttons_layout.addWidget(self.save_results_button)
        results_buttons_layout.addWidget(self.stop_button)
        results_buttons_layout.addStretch()  # 在布局的右侧添加空间，将Save Results按钮推到最左侧
        self.results_layout.addLayout(results_buttons_layout)

        # Add the results text
        self.results_layout.addWidget(self.results_text)

        # Add the results widget to the left splitter
        left_splitter = self.centralWidget().widget(0)
        left_splitter.addWidget(results_widget)

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

    @pyqtSlot(list, str)
    def display_method_result(self, to_drop, details):
        # to_drop 是一个包含要删除的特征名称的列表
        # details 是一个字符串，描述了所选方法的具体细节
        try:
            self.results_text.append(f"Details: {details}")
            self.results_text.append(f"Feature to Drop Count: {len(to_drop)}")
            if to_drop:
                self.results_text.append(f"Removed Features: {', '.join(to_drop)}")
            self.results_text.append("-" * 40)
        except Exception as e:
            print("Error in display_method_result:", e)

    @pyqtSlot(dict)
    def display_final_results(self, removal_summary):
        # removal_summary 是一个字典，其中包含已删除特征的摘要信息的列表
        summary_list = removal_summary.get("removal_summary", [])

        self.results_text.append("Final Removal Summary:")
        for summary in summary_list:
            self.results_text.append(summary)
            self.results_text.append("\n")

        # 显示保存结果按钮
        self.save_results_button.setVisible(True)

    def show_save_results_button(self):
        self.save_results_button.setVisible(True)

    def hide_save_results_button(self):
        self.save_results_button.setVisible(False)

    def show_stop_button(self):
        self.stop_button.setVisible(True)

    def hide_stop_button(self):
        self.stop_button.setVisible(False)
