from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextBrowser
from PyQt5.QtCore import Qt


class UsageDialog(QDialog):
    def __init__(self, parent=None):
        super(UsageDialog, self).__init__(parent)
        self.setWindowTitle('Usage Instructions')
        self.setFixedSize(900, 600)
        self.setWindowFlags(self.windowFlags() | Qt.WindowSystemMenuHint |
                            Qt.WindowMinMaxButtonsHint)

        layout = QVBoxLayout()
        self.text_browser = QTextBrowser(self)
        self.text_browser.setOpenExternalLinks(True)

        # Details for Missing Values
        self.text_browser.append("<h2>1. Missing Values (缺失值)</h2>")
        self.text_browser.append(
            "<b>Introduction :</b> In real-world datasets, it's common to have features with missing values. Features with a high percentage of missing values might be less informative and could hinder the performance of machine learning models.")
        self.text_browser.append(
            "<b>Principle :</b> This method evaluates each feature based on the percentage of missing values. Features with missing values exceeding a predefined threshold are considered for removal, as they might not add value to the prediction.")
        self.text_browser.append(
            "<b>Usage :</b> Set a threshold for the acceptable percentage of missing values. Features exceeding this threshold will be identified for removal.")

        # Details for Single Unique Value
        self.text_browser.append("<h2>2. Single Unique Value (单一唯一值)</h2>")
        self.text_browser.append(
            "<b>Introduction :</b> Features with only one unique value (constant features) don't provide any variability and hence might not be useful for predictions.")
        self.text_browser.append(
            "<b>Principle :</b> This method identifies and suggests removal of features that have only one unique value across all records, as they don't provide any meaningful information.")
        self.text_browser.append(
            "<b>Usage :</b> Simply apply the method to the dataset. It will automatically identify and suggest features with only one unique value for removal.")

        # Details for Collinear Features
        self.text_browser.append("<h2>3. Collinear Features (共线特征)</h2>")
        self.text_browser.append(
            "<b>Introduction :</b> Features that are highly correlated with others might introduce multicollinearity in linear models, which can lead to unstable estimates.")
        self.text_browser.append(
            "<b>Principle :</b> This method identifies pairs of features that have a correlation coefficient above a specified threshold. Removing one feature from each pair can help in reducing multicollinearity.")
        self.text_browser.append(
            "<b>Usage :</b> Set a threshold for the acceptable correlation coefficient. Features with correlation coefficients exceeding this threshold will be identified for removal.")

        # Details for Zero Importance Features
        self.text_browser.append("<h2>4. Zero Importance Features (零重要性特征)</h2>")
        self.text_browser.append(
            "<b>Introduction :</b> Not all features contribute equally to a model's predictive power. Some might have minimal or no impact at all.")
        self.text_browser.append(
            "<b>Principle :</b> By fitting a tree-based model to the data, this method ranks features based on their importance. Features with zero importance might not be useful for the model.")
        self.text_browser.append(
            "<b>Usage :</b> Fit a tree-based model like Decision Tree, Random Forest, or Gradient Boosted Trees to the data and retrieve the feature importance scores. Features with zero importance will be identified for removal.")

        # Details for Low Importance Features
        self.text_browser.append("<h2>5. Low Importance Features (低重要性特征)</h2>")
        self.text_browser.append(
            "<b>Introduction :</b> While some features might not be completely irrelevant, their contribution to the model's predictive power can be very low.")
        self.text_browser.append(
            "<b>Principle :</b> Similar to zero importance features, this method uses a tree-based model to rank features. Features with an importance score below a certain threshold are considered for removal to simplify the model without sacrificing much accuracy.")
        self.text_browser.append(
            "<b>Usage :</b> Fit a tree-based model to the data, retrieve the feature importance scores, and set a threshold for low importance. Features below this threshold will be identified for removal.")

        # Details for One-Hot Encoding
        self.text_browser.append("<h2>6. One-Hot Encoding (独热编码)</h2>")
        self.text_browser.append(
            "<b>Introduction :</b> Many machine learning algorithms require numerical input data. One-Hot Encoding is a process of converting categorical data variables into a binary matrix representation.")
        self.text_browser.append(
            "<b>Principle :</b> For each unique value in a categorical feature, a new binary (0 or 1) feature is created. If the original feature has N unique values, then N binary columns are created, where each column corresponds to one unique value. For a given record, the binary column corresponding to the record's categorical value is set to 1, and all other binary columns are set to 0.")
        self.text_browser.append(
            "<b>Usage :</b> Use One-Hot Encoding on categorical features before feeding the data to algorithms that require numerical input, such as linear regression or support vector machines.")

        layout.addWidget(self.text_browser)
        self.setLayout(layout)
