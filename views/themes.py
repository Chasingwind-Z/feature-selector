# themes.py

# Import qt_material to access its themes
import qt_material

QLIGHTSTYLESHEET = {
    "name": "Light",
    "qss_path": "QLightStyleSheet"
}

QDARKSTYLESHEET = {
    "name": "Dark",
    "qss_path": "QDarkStyleSheet"
}

MIDNIGHT_BLUE_THEME = {
    "name": "Midnight Blue",
    "background": "#003366",
    "foreground": "#FFFFFF",
    "button": "#004080",
    "button_text": "#FFFFFF",
    "button_hover": "#00509E",
    "highlight": "#0066CC",
    "menu_bar": "#001F3F",
    "menu_text": "#FFFFFF",
    "qss": """
        QPushButton {{
            background-color: {button};
            color: {button_text};
            border: 1px solid {highlight};
            padding: 5px;
            border-radius: 3px;
        }}
        QPushButton:hover {{
            background-color: {button_hover};
        }}
    """
}

OLIVE_GREEN_THEME = {
    "name": "Olive Green",
    "background": "#3B3F00",
    "foreground": "#FFFFFF",
    "button": "#5A5F00",
    "button_text": "#FFFFFF",
    "button_hover": "#7A7F00",
    "highlight": "#9A9F00",
    "menu_bar": "#2A2F00",
    "menu_text": "#FFFFFF",
    "qss": """
        QPushButton {{
            background-color: {button};
            color: {button_text};
            border: 1px solid {highlight};
            padding: 5px;
            border-radius: 3px;
        }}
        QPushButton:hover {{
            background-color: {button_hover};
        }}
    """
}

# Add all available qt-material themes
QT_MATERIAL_THEME_NAMES = ['dark_amber.xml',
                           'light_yellow.xml']
                           #  'dark_blue.xml',
                           # 'dark_cyan.xml',
                           # 'dark_lightgreen.xml',
                           # 'dark_pink.xml',
                           # 'dark_purple.xml',
                           # 'dark_red.xml',
                           # 'dark_teal.xml',
                           # 'dark_yellow.xml',
                           # 'light_amber.xml',
                           # 'light_blue.xml',
                           # 'light_cyan.xml',
                           # 'light_cyan_500.xml',
                           # 'light_lightgreen.xml',
                           # 'light_pink.xml',
                           # 'light_purple.xml',
                           # 'light_red.xml',
                           # 'light_teal.xml',
QT_MATERIAL_THEMES = [{"name": theme_name, "material": theme_name} for theme_name in QT_MATERIAL_THEME_NAMES]

ALL_THEMES = [QLIGHTSTYLESHEET, QDARKSTYLESHEET, MIDNIGHT_BLUE_THEME, OLIVE_GREEN_THEME] + QT_MATERIAL_THEMES

# 添加一个常量字典来映射主题名称和主题变量名
THEME_NAME_TO_VAR = {
    "Light": QLIGHTSTYLESHEET,
    "Dark": QDARKSTYLESHEET,
    "Midnight Blue": MIDNIGHT_BLUE_THEME,
    "Olive Green": OLIVE_GREEN_THEME,
}

# Add qt-material themes to the THEME_NAME_TO_VAR mapping
THEME_NAME_TO_VAR.update({theme["name"]: theme for theme in QT_MATERIAL_THEMES})
