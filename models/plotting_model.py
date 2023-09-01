class PlottingModel:
    def __init__(self, feature_selector_model):
        self.feature_selector_model = feature_selector_model

    def get_missing_status(self):
        """
        Return the missing fraction for each feature.
        """
        return self.feature_selector_model.missing_stats

    def get_unique_stats(self):
        """
        Return a DataFrame with the unique values statistics for each feature.
        """
        return self.feature_selector_model.unique_stats

    def get_collinear_data(self):
        """
        Get the data for collinear features.
        """
        return self.feature_selector_model.corr_matrix, self.feature_selector_model.record_collinear

    def get_feature_importances_data(self):
        """
        Get the feature importance data.
        """
        return self.feature_selector_model.feature_importances, self.feature_selector_model.record_zero_importance


