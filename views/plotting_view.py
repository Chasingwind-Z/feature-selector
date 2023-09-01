import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QComboBox, QLabel, QLineEdit, QHBoxLayout, QCheckBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class PlottingView(QWidget):
    plot_requested = pyqtSignal(str, dict)  # 修改信号以传递额外的参数信息

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Dropdown for plot selection
        self.plot_dropdown = QComboBox()
        self.plot_dropdown.addItems(["Missing Values", "Unique Values", "Collinear Features", "Feature Importances"])
        layout.addWidget(QLabel("Select Plot Type:"))
        layout.addWidget(self.plot_dropdown)

        # Collinear Plot Settings
        self.collinear_checkbox = QCheckBox("Plot All Correlations")
        layout.addWidget(self.collinear_checkbox)

        # Feature Importances Settings
        fi_layout = QHBoxLayout()
        fi_layout.addWidget(QLabel("Number of Features to Plot:"))
        self.fi_plot_n = QLineEdit("15")
        fi_layout.addWidget(self.fi_plot_n)
        fi_layout.addWidget(QLabel("Cumulative Importance Threshold:"))
        self.fi_threshold = QLineEdit()
        fi_layout.addWidget(self.fi_threshold)
        layout.addLayout(fi_layout)

        # Plot button
        self.plot_button = QPushButton("Generate Plot")
        self.plot_button.clicked.connect(self.generate_plot)
        layout.addWidget(self.plot_button)

        # Message label for displaying notifications or errors
        self.message_label = QLabel("")
        layout.addWidget(self.message_label)

        # Add the canvas for plotting
        layout.addWidget(self.canvas)

        self.setLayout(layout)

    def generate_plot(self):
        plot_type = self.plot_dropdown.currentText()

        # Create a dictionary for additional parameters
        params = {}
        if plot_type == "Collinear Features":
            params['plot_all'] = self.collinear_checkbox.isChecked()
        elif plot_type == "Feature Importances":
            params['plot_n'] = int(self.fi_plot_n.text()) if self.fi_plot_n.text().isdigit() else 15
            params['threshold'] = float(self.fi_threshold.text()) if self.fi_threshold.text() else None

        # Emit the signal with the plot type and the additional parameters
        self.plot_requested.emit(plot_type, params)

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
        ax.set_yticklabels(list(corr_matrix_plot.index), size=int(160 / corr_matrix_plot.shape[0]));

        # Set the xlabels
        ax.set_xticks([x + 0.5 for x in list(range(corr_matrix_plot.shape[1]))])
        ax.set_xticklabels(list(corr_matrix_plot.columns), size=int(160 / corr_matrix_plot.shape[1]));

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

        # Need to adjust number of features if greater than the features in the data
        if plot_n > feature_importances.shape[0]:
            plot_n = feature_importances.shape[0] - 1

        # Clear previous figures
        self.figure.clear()

        # Make a horizontal bar chart of feature importances
        ax1 = self.figure.add_subplot(211)

        # Need to reverse the index to plot most important on top
        ax1.barh(list(reversed(list(feature_importances.index[:plot_n]))),
                 feature_importances['normalized_importance'].iloc[:plot_n],
                 align='center', edgecolor='k')

        # Set the yticks and labels
        ax1.set_yticks(list(reversed(list(feature_importances.index[:plot_n]))))
        ax1.set_yticklabels(feature_importances['feature'].iloc[:plot_n], size=12)

        # Plot labeling
        ax1.set_xlabel('Normalized Importance', size=16)
        ax1.set_title('Feature Importances', size=18)
        self.canvas.draw()

        # Cumulative importance plot
        ax2 = self.figure.add_subplot(212)
        ax2.plot(list(range(1, len(feature_importances) + 1)), feature_importances['cumulative_importance'], 'r-')
        ax2.set_xlabel('Number of Features', size=14)
        ax2.set_ylabel('Cumulative Importance', size=14)
        ax2.set_title('Cumulative Feature Importance', size=16)

        if threshold:
            # Index of minimum number of features needed for cumulative importance threshold
            importance_index = np.min(np.where(feature_importances['cumulative_importance'] > threshold))
            ax2.vlines(x=importance_index + 1, ymin=0, ymax=1, linestyles='--', colors='blue')
            # Redraw the canvas
            self.canvas.draw()
            self.message_label.setText(
                '%d features required for %0.2f of cumulative importance' % (importance_index + 1, threshold))
