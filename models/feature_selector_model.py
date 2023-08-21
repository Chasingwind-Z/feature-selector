import pandas as pd
import numpy as np
from sklearn.feature_selection import RFE, SelectKBest, chi2
from sklearn.linear_model import LogisticRegression, Lasso
from sklearn.ensemble import RandomForestClassifier

class FeatureSelectorModel:
    def __init__(self):
        self.data = None

    def load_data(self, data):
        self.data = data

    def select_features(self, methods, target_column):
        results = {}
        common_features = set(self.data.columns.tolist())
        common_features.remove(target_column)

        # Iterate through the selected methods and execute them
        for method_name, params in methods.items():
            method = getattr(self, method_name, None)
            if method:
                selected_features = method(target_column, **params)
                common_features.intersection_update(selected_features)
                results[method_name] = {
                    "feature_count": len(selected_features),
                    "selected_features": selected_features,
                    "removed_features": [feat for feat in self.data.columns if feat not in selected_features and feat != target_column]
                }

        # Take the intersection of all the selected features
        self.data = self.data[list(common_features) + [target_column]]
        return self.data, results

    def remove_missing_values(self, target_column, threshold=0.6):
        missing = self.data.isnull().mean()
        to_drop = missing[missing > threshold].index.tolist()
        self.data.drop(columns=to_drop, inplace=True)
        return set(self.data.columns) - {target_column}

    def remove_single_unique(self, target_column):
        unique_counts = self.data.nunique()
        to_drop = unique_counts[unique_counts == 1].index.tolist()
        self.data.drop(columns=to_drop, inplace=True)
        return set(self.data.columns) - {target_column}

    def remove_collinear_features(self, target_column, threshold=0.95):
        corr_matrix = self.data.corr().abs()
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(np.bool))
        to_drop = [column for column in upper.columns if any(upper[column] > threshold)]
        self.data.drop(columns=to_drop, inplace=True)
        return set(self.data.columns) - {target_column}

    def remove_zero_importance(self, target_column):
        X = self.data.drop(columns=[target_column])
        y = self.data[target_column]
        model = RandomForestClassifier(n_estimators=50, random_state=0)
        model.fit(X, y)
        feature_importance = pd.Series(model.feature_importances_, index=X.columns)
        to_drop = feature_importance[feature_importance == 0].index.tolist()
        self.data.drop(columns=to_drop, inplace=True)
        return set(self.data.columns) - {target_column}

    def statistical_tests(self, target_column, k=10):
        X = self.data.drop(columns=[target_column])
        y = self.data[target_column]
        select_k_best = SelectKBest(score_func=chi2, k=k)
        select_k_best.fit(X, y)
        selected_features = X.columns[select_k_best.get_support()].tolist()
        self.data = self.data[selected_features + [target_column]]
        return selected_features

    def rfe_selection(self, target_column, n_features_to_select=10):
        X = self.data.drop(columns=[target_column])
        y = self.data[target_column]
        rfe_selector = RFE(estimator=LogisticRegression(), n_features_to_select=n_features_to_select)
        rfe_selector.fit(X, y)
        selected_features = X.columns[rfe_selector.get_support()].tolist()
        self.data = self.data[selected_features + [target_column]]
        return selected_features

    def linear_model_selection(self, target_column, threshold=0.1):
        X = self.data.drop(columns=[target_column])
        y = self.data[target_column]
        lasso = Lasso(alpha=0.1)
        lasso.fit(X, y)
        selected_features = X.columns[np.abs(lasso.coef_) > threshold].tolist()
        self.data = self.data[selected_features + [target_column]]
        return selected_features

    def get_features(self):
        return self.data.columns.tolist()
