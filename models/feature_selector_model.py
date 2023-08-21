import pandas as pd
import numpy as np
from sklearn.feature_selection import RFE, SelectKBest, chi2
from sklearn.linear_model import LogisticRegression, Lasso
from sklearn.ensemble import RandomForestClassifier

class FeatureSelectorModel:
    def __init__(self):
        self.data = None
        self.selected_features = None

    def load_data(self, file_name):
        self.data = pd.read_csv(file_name)

    def remove_missing_values(self, threshold=0.6):
        missing = self.data.isnull().mean()
        to_drop = missing[missing > threshold].index.tolist()
        self.data.drop(columns=to_drop, inplace=True)

    def remove_single_unique(self):
        unique_counts = self.data.nunique()
        to_drop = unique_counts[unique_counts == 1].index.tolist()
        self.data.drop(columns=to_drop, inplace=True)

    def remove_collinear_features(self, threshold=0.95):
        corr_matrix = self.data.corr().abs()
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(np.bool))
        to_drop = [column for column in upper.columns if any(upper[column] > threshold)]
        self.data.drop(columns=to_drop, inplace=True)

    def remove_zero_importance(self, target_column):
        X = self.data.drop(columns=[target_column])
        y = self.data[target_column]
        model = RandomForestClassifier(n_estimators=50, random_state=0)
        model.fit(X, y)
        feature_importance = pd.Series(model.feature_importances_, index=X.columns)
        to_drop = feature_importance[feature_importance == 0].index.tolist()
        self.data.drop(columns=to_drop, inplace=True)

    def statistical_tests(self, target_column, k=10):
        X = self.data.drop(columns=[target_column])
        y = self.data[target_column]
        select_k_best = SelectKBest(score_func=chi2, k=k)
        select_k_best.fit(X, y)
        self.data = self.data[X.columns[select_k_best.get_support()].tolist() + [target_column]]

    def rfe_selection(self, target_column, n_features_to_select=10):
        X = self.data.drop(columns=[target_column])
        y = self.data[target_column]
        rfe_selector = RFE(estimator=LogisticRegression(), n_features_to_select=n_features_to_select)
        rfe_selector.fit(X, y)
        self.data = self.data[X.columns[rfe_selector.get_support()].tolist() + [target_column]]

    def linear_model_selection(self, target_column, threshold=0.1):
        X = self.data.drop(columns=[target_column])
        y = self.data[target_column]
        lasso = Lasso(alpha=0.1)
        lasso.fit(X, y)
        selected_features = X.columns[np.abs(lasso.coef_) > threshold].tolist()
        self.data = self.data[selected_features + [target_column]]

    def get_features(self):
        return self.data.columns.tolist()
