from views import main_window
from FeatureSelector import selectors
from Plotter import plots
from controllers import controller

import sys
from PyQt5.QtWidgets import QApplication

# 创建模块实例
app = QApplication(sys.argv)

window = main_window.MainWindow()

fs = selectors.FeatureSelector()

plotter = plots.Plotter()

controller = controller.Controller(window, fs, plotter)

# 启动控制器事件循环
controller.start()

# 启动GUI事件循环
app.exec_()