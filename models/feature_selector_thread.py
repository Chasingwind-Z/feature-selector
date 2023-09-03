from PyQt5.QtCore import QThread


class FeatureSelectionThread(QThread):
    def __init__(self, model, methods, target_column_name, keep_one_hot, parent=None):
        super(FeatureSelectionThread, self).__init__(parent)
        self.model = model
        self.methods = methods
        self.target_column_name = target_column_name
        self.keep_one_hot = keep_one_hot

    def run(self):
        self.model.select_features(self.methods, self.target_column_name, self.keep_one_hot)
