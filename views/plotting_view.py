import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from PyQt5.QtCore import pyqtSignal, Qt, QBuffer
from PyQt5.QtGui import QCursor, QPixmap
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QComboBox, QLabel, QLineEdit, QSplitter, QStackedWidget,
                             QMenu, QFileDialog, QFrame, QApplication, QFormLayout)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class PlottingView(QWidget):
    plot_requested = pyqtSignal(str, dict)  # 修改信号以传递额外的参数信息

    def __init__(self, model, app):
        super().__init__()

        self.app = app
        self.model = model
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.mpl_connect('button_press_event', self.context_menu)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        main_layout = QVBoxLayout()

        # 控制面板
        control_panel = QWidget()
        control_layout = QVBoxLayout()

        # 选择绘图类型的组合框
        select_layout = QFormLayout()
        self.plot_dropdown = QComboBox()
        self.plot_dropdown.addItems(["Missing Values", "Unique Values", "Collinear Features", "Feature Importances"])
        select_layout.addRow("Select Plot Type:", self.plot_dropdown)
        control_layout.addLayout(select_layout)

        # 使用QStackedWidget动态显示参数输入
        self.parameters_stacked_widget = QStackedWidget()
        self.init_parameters_widgets()
        control_layout.addWidget(self.parameters_stacked_widget)

        # Generate Plot按钮
        self.plot_button = QPushButton("Generate Plot")
        self.plot_button.clicked.connect(self.generate_plot)
        control_layout.addWidget(self.plot_button)

        # 用于显示通知或错误的消息标签
        self.message_label = QLabel("")
        control_layout.addWidget(self.message_label)

        control_panel.setLayout(control_layout)

        # 添加绘图区域的边框
        plotting_frame = QFrame(self)
        plotting_frame.setFrameShape(QFrame.StyledPanel)
        plotting_layout = QVBoxLayout()
        plotting_layout.addWidget(self.canvas)
        plotting_frame.setLayout(plotting_layout)

        # 主窗口布局
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(control_panel)
        splitter.addWidget(plotting_frame)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def init_parameters_widgets(self):
        # 对于每种绘图类型，我们都可以添加一个特定的参数窗口部件

        # Missing Values: 无参数
        self.parameters_stacked_widget.addWidget(QWidget())

        # Unique Values: 无参数
        self.parameters_stacked_widget.addWidget(QWidget())

        # Collinear Features
        collinear_widget = QWidget()
        collinear_layout = QFormLayout()
        self.plot_all_combobox = QComboBox()
        self.plot_all_combobox.addItems(["True", "False"])
        collinear_layout.addRow("Plot All:", self.plot_all_combobox)
        collinear_widget.setLayout(collinear_layout)
        self.parameters_stacked_widget.addWidget(collinear_widget)

        # Feature Importances
        feature_importances_widget = QWidget()
        feature_importances_layout = QFormLayout()
        self.plot_n_lineedit = QLineEdit("15")
        self.plot_n_lineedit.setFixedWidth(50)
        feature_importances_layout.addRow("Plot N:", self.plot_n_lineedit)
        self.threshold_lineedit = QLineEdit("0.99")
        self.threshold_lineedit.setFixedWidth(50)
        feature_importances_layout.addRow("Threshold:", self.threshold_lineedit)
        feature_importances_widget.setLayout(feature_importances_layout)
        self.parameters_stacked_widget.addWidget(feature_importances_widget)

        self.plot_dropdown.currentIndexChanged.connect(self.parameters_stacked_widget.setCurrentIndex)

    def generate_plot(self):
        plot_type = self.plot_dropdown.currentText()
        parameters = {}
        if plot_type == "Collinear Features":
            parameters['plot_all'] = self.plot_all_combobox.currentText() == "True"
        elif plot_type == "Feature Importances":
            parameters['plot_n'] = int(self.plot_n_lineedit.text())
            parameters['threshold'] = float(self.threshold_lineedit.text())
        self.plot_requested.emit(plot_type, parameters)

    def context_menu(self, event):
        if event.button == 3:  # Right click
            context_menu = QMenu(self)
            save_action = context_menu.addAction("Save Figure")
            copy_action = context_menu.addAction("Copy Figure")
            action = context_menu.exec_(QCursor.pos())

            if action == save_action:
                file_path, _ = QFileDialog.getSaveFileName(self, "Save Figure", "", "PNG(*.png);;JPEG(*.jpg *.jpeg);;All Files(*.*)")
                if file_path:
                    self.figure.savefig(file_path)
            elif action == copy_action:
                clipboard = QApplication.clipboard()
                buffer = QBuffer()
                buffer.open(QBuffer.ReadWrite)
                self.figure.savefig(buffer, format="png")
                pixmap = QPixmap()
                pixmap.loadFromData(buffer.data(), "png")
                clipboard.setPixmap(pixmap)

    def plot_missing(self):
        """Histogram of missing fraction in each feature"""
        missing_stats = self.model.get_missing_status()

        if missing_stats is None:
            self.message_label.setText('Missing values have not been calculated. Run `identify_missing`')
            return

        # Clear previous figures
        self.figure.clear()

        # Histogram of missing values
        ax = self.figure.add_subplot(111)
        sns.histplot(missing_stats['missing_fraction'], bins=np.linspace(0, 1, 11), edgecolor='k', color='red',
                     linewidth=1.5, ax=ax)
        ax.set_xticks(np.linspace(0, 1, 11))
        ax.set_xlabel('Missing Fraction', size=14)
        ax.set_ylabel('Count of Features', size=14)
        ax.set_title("Fraction of Missing Values Histogram", size=16)

        # Redraw the canvas
        self.canvas.draw()

    def plot_unique(self):
        """Histogram of number of unique values in each feature"""
        unique_stats = self.model.get_unique_stats()

        if unique_stats is None:
            self.message_label.setText('Unique values have not been calculated. Run `identify_single_unique`')
            return

        # Clear previous figures
        self.figure.clear()

        # Histogram of number of unique values
        ax = self.figure.add_subplot(111)
        sns.histplot(unique_stats, edgecolor='k', ax=ax)

        ax.set_ylabel('Frequency', size=14)
        ax.set_xlabel('Unique Values', size=14)
        ax.set_title('Number of Unique Values Histogram', size=16)

        # Redraw the canvas
        self.canvas.draw()

    def plot_collinear(self, plot_all=False):
        """
        Heatmap of the correlation values. If plot_all=True, plots all the correlations, otherwise
        plots only those features that have a correlation above the threshold.
        """

        corr_matrix, record_collinear = self.model.get_collinear_data()

        if record_collinear is None:
            self.message_label.setText('Collinear features have not been identified. Run `identify_collinear`')
            return

        # Clear previous figures
        self.figure.clear()

        if plot_all:
            corr_matrix_plot = corr_matrix
            title = 'All Correlations'
        else:
            # Identify the correlations that were above the threshold
            # columns (x-axis) are features to drop and rows (y_axis) are correlated pairs
            corr_matrix_plot = corr_matrix.loc[list(set(record_collinear['corr_feature'])),
            list(set(record_collinear['drop_feature']))]
            title = "Correlations Above Threshold"

        ax = self.figure.add_subplot(111)

        # Diverging colormap
        cmap = sns.diverging_palette(220, 10, as_cmap=True)

        # Draw the heatmap with a color bar
        sns.heatmap(corr_matrix_plot, cmap=cmap, center=0,
                    linewidths=.25, cbar_kws={"shrink": 0.6}, ax=ax)

        # Set the ylabels
        ax.set_yticks([x + 0.5 for x in list(range(corr_matrix_plot.shape[0]))])
        ax.set_yticklabels(list(corr_matrix_plot.index), size=int(160 / corr_matrix_plot.shape[0]))

        # Set the xlabels
        ax.set_xticks([x + 0.5 for x in list(range(corr_matrix_plot.shape[1]))])
        ax.set_xticklabels(list(corr_matrix_plot.columns), size=int(160 / corr_matrix_plot.shape[1]))

        ax.set_title(title, size=14)

        # Redraw the canvas
        self.canvas.draw()

    def plot_feature_importances(self, plot_n=15, threshold=None):
        """
        Plots `plot_n` most important features and the cumulative importance of features.
        If `threshold` is provided, prints the number of features needed to reach `threshold` cumulative importance.

        Parameters
        --------

        plot_n : int, default = 15
            Number of most important features to plot. Defaults to 15 or the maximum number of features whichever is smaller

        threshold : float, between 0 and 1 default = None
            Threshold for printing information about cumulative importances

        """

        feature_importances, record_zero_importance = self.model.get_feature_importances_data()

        if record_zero_importance is None:
            self.message_label.setText('Feature importances have not been determined. Run `identify_zero_importance`')
            return

        if plot_n > feature_importances.shape[0]:
            plot_n = feature_importances.shape[0] - 1

        # Clear previous figures
        self.figure.clear()

        # Adjust figure size
        self.figure.set_size_inches(10, 8)  # Adjust width and height as needed

        # Make a horizontal bar chart of feature importances
        ax1 = self.figure.add_subplot(211)

        ax1.barh(list(reversed(list(feature_importances.index[:plot_n]))),
                 feature_importances['normalized_importance'].iloc[:plot_n],
                 align='center', edgecolor='k')

        # Adjust ytick labels size
        ax1.set_yticks(list(reversed(list(feature_importances.index[:plot_n]))))
        ax1.set_yticklabels(feature_importances['feature'].iloc[:plot_n], size=10)  # Adjust font size

        ax1.set_xlabel('Normalized Importance', size=14)
        ax1.set_title('Feature Importances', size=16)

        # Cumulative importance plot
        ax2 = self.figure.add_subplot(212)
        ax2.plot(list(range(1, len(feature_importances) + 1)), feature_importances['cumulative_importance'], 'r-')
        ax2.set_xlabel('Number of Features', size=14)
        ax2.set_ylabel('Cumulative Importance', size=14)
        ax2.set_title('Cumulative Feature Importance', size=16)

        if threshold:
            importance_index = np.min(np.where(feature_importances['cumulative_importance'] > threshold))
            ax2.vlines(x=importance_index + 1, ymin=0, ymax=1, linestyles='--', colors='blue')
            self.message_label.setText(
                '%d features required for %0.2f of cumulative importance' % (importance_index + 1, threshold))

        # Adjust layout to prevent overlap
        self.figure.tight_layout()

        self.canvas.draw()
