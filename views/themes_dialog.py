from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QGridLayout, QLabel,
                             QComboBox, QPushButton, QGroupBox, QFrame, QHBoxLayout)
from .themes import ALL_THEMES, THEME_NAME_TO_VAR, QLIGHTSTYLESHEET  # 使用相对导入

class ThemesDialog(QDialog):
    def __init__(self, current_theme_name, parent=None):
        super(ThemesDialog, self).__init__(parent)

        # 设置窗口标题和属性
        self.setWindowTitle("Switch Theme")
        self.setFixedSize(350, 180)

        # 主布局
        main_layout = QVBoxLayout()

        # 主题选择组框
        theme_group = QGroupBox("Theme Selection")
        theme_layout = QGridLayout()

        label = QLabel("Select Theme:")
        theme_layout.addWidget(label, 0, 0)

        self.theme_combobox = QComboBox()
        theme_names = [theme['name'] for theme in ALL_THEMES]
        self.theme_combobox.addItems(theme_names)
        self.theme_combobox.setCurrentText(current_theme_name)
        theme_layout.addWidget(self.theme_combobox, 0, 1)

        theme_group.setLayout(theme_layout)
        main_layout.addWidget(theme_group)

        # 按钮布局
        buttons_layout = QHBoxLayout()

        self.ok_button = QPushButton("OK")  # 已去除图标
        self.ok_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.ok_button)

        self.cancel_button = QPushButton("Cancel")  # 已去除图标
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        # 在按钮前添加水平线
        hline = QFrame()
        hline.setFrameShape(QFrame.HLine)
        hline.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(hline)

        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)

    def selected_theme(self):
        theme_name = self.theme_combobox.currentText()
        # Directly return the theme dictionary
        return THEME_NAME_TO_VAR.get(theme_name, QLIGHTSTYLESHEET)
