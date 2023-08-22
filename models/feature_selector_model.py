import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import lightgbm as lgb
import gc

class FeatureSelectorModel:
    def __init__(self):
        self.data = None

    def load_data(self, data):
        self.data = data

    def select_features(self, methods, target_column):
        try:
            results = {}
            common_features = set(self.data.columns.tolist())
            common_features.remove(target_column)

            # Iterate through the selected methods and execute them
            for method_name, params in methods.items():
                method = getattr(self, method_name, None)
                if method:
                    selected_features, details = method(target_column, **params)
                    common_features.intersection_update(selected_features)
                    results[method_name] = {
                        "feature_count": len(selected_features),
                        "selected_features": selected_features,
                        "details": details
                    }

            # Compute the intersection of selected features and maintain original order
            final_features = [feature for feature in self.data.columns if feature in common_features]

            return results, final_features
        except Exception as e:
            print("Exception occurred:", str(e))
            raise

    def select_missing_values(self, target_column, missing_threshold=0.6):
        # 确保阈值是浮点数
        missing_threshold = float(missing_threshold)

        # 计算每列的缺失值分数
        missing_series = self.data.isnull().sum() / self.data.shape[0]

        # 创建 DataFrame 以存储缺失值分数
        missing_stats = pd.DataFrame(missing_series).rename(columns={0: 'missing_fraction'})
        missing_stats.index.name = 'feature'

        # 找到高于阈值的列
        record_missing = missing_stats[missing_stats['missing_fraction'] > missing_threshold].reset_index()

        # 将要删除的特征列表
        to_drop = list(record_missing['feature'])
        if target_column in to_drop:
            to_drop.remove(target_column)

        details = {
            "record_missing": record_missing.to_dict(orient='records'),
            "missing_stats": missing_stats.sample(5).to_dict(orient='records')
        }

        selected_features = [feature for feature in self.data.columns if feature not in to_drop]

        return selected_features, details

    def select_single_unique_value(self, target_column):
        unique_counts = self.data.nunique()
        removed_features = unique_counts[unique_counts == 1].index.tolist()
        if target_column in removed_features:
            removed_features.remove(target_column)
        details = {
            "removed_features": removed_features,
            "unique_stats": unique_counts.sample(5).to_dict()
        }
        selected_features = [feature for feature in self.data.columns if feature not in removed_features]
        return selected_features, details

    def select_collinear_features(self, target_column, correlation_threshold=0.975):
        # 明确设置 numeric_only 参数的值
        corr_matrix = self.data.corr(numeric_only=True)
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(np.bool))
        drop_features = [column for column in upper.columns if any(upper[column].abs() > correlation_threshold)]

        if target_column in drop_features:
            drop_features.remove(target_column)

        selected_features = [feature for feature in self.data.columns if feature not in drop_features]

        record_collinear = pd.DataFrame(columns=['drop_feature', 'corr_feature', 'corr_value'])
        for column in drop_features:
            # 找到相关特征
            corr_features = list(upper.index[upper[column].abs() > correlation_threshold])
            # 找到相关值
            corr_values = list(upper[column][upper[column].abs() > correlation_threshold])
            drop_features_list = [column for _ in range(len(corr_features))]
            temp_df = pd.DataFrame.from_dict({'drop_feature': drop_features_list,
                                              'corr_feature': corr_features,
                                              'corr_value': corr_values})
            # 添加到 dataframe
            record_collinear = record_collinear.append(temp_df, ignore_index=True)

        details = {
            "removed_features": drop_features,
            "record_collinear": record_collinear.to_dict(orient='records')
        }


        return selected_features, details

    def select_zero_importance_features(self, target_column, eval_metric, task='classification',
                                        n_iterations=10, early_stopping=True):
        # Get features and labels
        features = self.data.drop(columns=[target_column])
        labels = self.data[target_column]

        # One hot encoding
        features = pd.get_dummies(features)
        feature_names = features.columns.tolist()  # Save feature names before converting to numpy array

        # Convert to numpy array
        features = np.array(features)
        labels = np.array(labels).reshape((-1,))

        # Empty array for feature importances
        feature_importance_values = np.zeros(features.shape[1])

        # Iterate through each iteration
        for _ in range(n_iterations):
            if task == 'classification':
                model = lgb.LGBMClassifier(n_estimators=1000, learning_rate=0.05, verbose=-1)
            elif task == 'regression':
                model = lgb.LGBMRegressor(n_estimators=1000, learning_rate=0.05, verbose=-1)
            else:
                raise ValueError('Task must be either "classification" or "regression"')

            # Split data if early stopping is used
            if early_stopping:
                train_features, valid_features, train_labels, valid_labels = train_test_split(features, labels,
                                                                                              test_size=0.15)
                model.fit(train_features, train_labels, eval_metric=eval_metric,
                          eval_set=[(valid_features, valid_labels)],
                          early_stopping_rounds=100, verbose=-1)
                del train_features, train_labels, valid_features, valid_labels
                gc.collect()
            else:
                model.fit(features, labels)

            feature_importance_values += model.feature_importances_ / n_iterations

        feature_importances = pd.DataFrame({'feature': feature_names, 'importance': feature_importance_values})

        # Normalize the feature importances to add up to one
        feature_importances['normalized_importance'] = feature_importances['importance'] / feature_importances[
            'importance'].sum()
        feature_importances['cumulative_importance'] = np.cumsum(feature_importances['normalized_importance'])

        # Identify the features with zero importance
        selected_features = list(feature_importances[feature_importances['importance'] == 0.0]['feature'])

        details = {
            "removed_features": selected_features,
            "feature_importances": feature_importances.sort_values('importance', ascending=False).head(10).to_dict(
                orient='records')
        }

        return selected_features, details

    def select_low_importance_features(self, target_column, cumulative_importance_threshold=0.99):
        # First, ensure that select_zero_importance_features has been run to get feature_importances
        selected_features_zero_importance, details_zero_importance = self.select_zero_importance_features(target_column,
                                                                                                          eval_metric='auc')
        feature_importances = pd.DataFrame(details_zero_importance["feature_importances"])

        # 确保最重要的特征在顶部
        feature_importances = feature_importances.sort_values('cumulative_importance')

        # 确定达到累积重要性阈值不需要的特征
        record_low_importance = feature_importances[
            feature_importances['cumulative_importance'] > cumulative_importance_threshold]
        selected_features = list(record_low_importance['feature'])

        details = {
            "removed_features": selected_features,
            "feature_importances": feature_importances.head(10).to_dict(orient='records')
        }

        return selected_features, details

