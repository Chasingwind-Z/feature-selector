from itertools import chain

import numpy as np
import pandas as pd
from PyQt5.QtCore import pyqtSignal, QObject, QThread
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split
import lightgbm as lgb
import gc


class FeatureSelectorModel(QObject):
    # Signal definitions
    method_result_signal = pyqtSignal(list, str)
    final_results_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        self.labels = None
        self.one_hot_correlated = False
        self.data_all = None
        self.one_hot_features = None
        self.base_features = None
        self.cumulative_importance = None
        self.correlation_threshold = None
        self.corr_matrix = None
        self.unique_stats = None
        self.missing_threshold = None
        self.missing_stats = None
        self.result_data = None
        self.original_features = None
        self.data = None
        # Dataframes recording information about features to remove
        self.record_missing = None
        self.record_single_unique = None
        self.record_collinear = None
        self.record_zero_importance = None
        self.record_low_importance = None
        self.feature_importances = None
        # Dictionary to hold removal operations
        self.removal_ops = {}

    def load_data(self, data):
        self.data = data
        self.base_features = list(data.columns)

    def select_features(self, selected_methods_and_params, target_column_name, keep_one_hot=True):
        self.labels = self.data[target_column_name]  # Extracting the target column as labels
        self.data = self.data.drop(columns=[target_column_name])  # Dropping the target column from the data
        selected_removal_methods = []
        all_methods = ['Missing Values', 'Single Unique Value', 'Collinear Features', 'Zero Importance Features',
                       'Low Importance Features']

        for method, params in selected_methods_and_params.items():
            if QThread.currentThread().isInterruptionRequested():
                return

            # Match the method name with the appropriate function call
            if method == 'Missing Values':
                selected_removal_methods.append('missing')
                to_drop, details = self.identify_missing(params['missing_threshold'])
            elif method == 'Single Unique Value':
                selected_removal_methods.append('single_unique')
                to_drop, details = self.identify_single_unique()
            elif method == 'Collinear Features':
                selected_removal_methods.append('collinear')
                to_drop, details = self.identify_collinear(params['correlation_threshold'], params['one_hot'])
            elif method == 'Zero Importance Features':
                selected_removal_methods.append('zero_importance')
                to_drop, details = self.identify_zero_importance(**params)  # Using all params here
            elif method == 'Low Importance Features':
                selected_removal_methods.append('low_importance')
                to_drop, details = self.identify_low_importance(params['cumulative_importance'])
            else:
                continue

            # Emit signal to update the GUI with the results of the individual method
            self.method_result_signal.emit(to_drop, details)

        # If all methods are selected
        if set(all_methods) == set(selected_methods_and_params.keys()):
            selected_removal_methods = 'all'

        # Finally, remove the features based on the results of all methods
        removal_summary = self.remove_features(selected_removal_methods, keep_one_hot)
        # Emit signal to update the GUI with the final results
        self.final_results_signal.emit(removal_summary)
        # Return the result data with the same feature order as the original data
        return self.result_data

    def identify_missing(self, missing_threshold):
        """Find the features with a fraction of missing values above `missing_threshold`"""

        self.missing_threshold = missing_threshold

        # Calculate the fraction of missing in each column
        missing_series = self.data.isnull().sum() / self.data.shape[0]
        self.missing_stats = pd.DataFrame(missing_series).rename(columns={'index': 'feature', 0: 'missing_fraction'})

        # Sort with highest number of missing values on top
        self.missing_stats = self.missing_stats.sort_values('missing_fraction', ascending=False)

        # Find the columns with a missing percentage above the threshold
        record_missing = pd.DataFrame(missing_series[missing_series > missing_threshold]).reset_index().rename(columns=
        {
            'index': 'feature',
            0: 'missing_fraction'})

        to_drop = list(record_missing['feature'])

        self.record_missing = record_missing
        self.removal_ops['missing'] = to_drop

        details = '%d features with greater than %0.2f missing values.\n' % (
            len(self.removal_ops['missing']), self.missing_threshold)

        return to_drop, details

    def identify_single_unique(self):
        """Identifies features with only a single unique value. NaNs do not count as a unique value."""

        # Calculate the unique counts in each column
        unique_counts = self.data.nunique()

        self.unique_stats = pd.DataFrame(unique_counts).rename(columns={'index': 'feature', 0: 'nunique'})
        self.unique_stats = self.unique_stats.sort_values('nunique', ascending=True)

        # Find the columns with only one unique count
        record_single_unique = pd.DataFrame(unique_counts[unique_counts == 1]).reset_index().rename(
            columns={'index': 'feature', 0: 'nunique'})

        to_drop = list(record_single_unique['feature'])

        self.record_single_unique = record_single_unique
        self.removal_ops['single_unique'] = to_drop

        details = '%d features with a single unique value.\n' % len(self.removal_ops['single_unique'])

        return to_drop, details

    def identify_collinear(self, correlation_threshold, one_hot=False):
        """
        Finds collinear features based on the correlation coefficient between features.
        For each pair of features with a correlation coefficient greater than `correlation_threshold`,
        only one of the pair is identified for removal.

        Parameters
        --------
        correlation_threshold : float between 0 and 1
            Value of the Pearson correlation coefficient for identifying correlation features

        one_hot : boolean, default = False
            Whether to one-hot encode the features before calculating the correlation coefficients
        """

        self.correlation_threshold = correlation_threshold
        self.one_hot_correlated = one_hot

        # Calculate the correlations between every column
        if one_hot:
            # One hot encoding
            features = pd.get_dummies(self.data)
            self.one_hot_features = [column for column in features.columns if column not in self.base_features]

            # Add one hot encoded data to original data
            self.data_all = pd.concat([features[self.one_hot_features], self.data], axis=1)

            corr_matrix = pd.get_dummies(features).corr(numeric_only=True)
        else:
            corr_matrix = self.data.corr(numeric_only=True)

        self.corr_matrix = corr_matrix

        # Extract the upper triangle of the correlation matrix
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(np.bool))

        # Select the features with correlations above the threshold
        to_drop = [column for column in upper.columns if any(upper[column].abs() > correlation_threshold)]

        # Dataframe to hold correlated pairs
        record_collinear = pd.DataFrame(columns=['drop_feature', 'corr_feature', 'corr_value'])

        # Iterate through the columns to drop
        for column in to_drop:
            # Find the correlated features
            corr_features = list(upper.index[upper[column].abs() > correlation_threshold])

            # Find the correlated values
            corr_values = list(upper[column][upper[column].abs() > correlation_threshold])
            drop_features = [column for _ in range(len(corr_features))]

            # Record the information (need a temp df for now)
            temp_df = pd.DataFrame.from_dict({'drop_feature': drop_features,
                                              'corr_feature': corr_features,
                                              'corr_value': corr_values})

            # Add to dataframe
            record_collinear = pd.concat([record_collinear, temp_df], ignore_index=True)

        self.record_collinear = record_collinear
        self.removal_ops['collinear'] = to_drop

        details = '%d features with a correlation magnitude greater than %0.2f.\n' % (
            len(self.removal_ops['collinear']), self.correlation_threshold)

        return to_drop, details

    def identify_zero_importance(self, eval_metric=None, task='classification',
                                 n_iterations=10, early_stopping=True,
                                 importance_type='split', n_permutations=10):
        """
        Identify the features with zero importance according to a gradient boosting machine.
        The GBM can be trained with early stopping using a validation set to prevent overfitting.
        The feature importances are averaged over n_iterations to reduce variance.
        Uses the LightGBM implementation.
        """

        # Check for early stopping and eval metric
        if early_stopping and eval_metric is None:
            raise ValueError("""eval metric must be provided with early stopping. Examples include "auc" for classification,
                             "l2" for regression, or "quantile" for quantile""")
        # One hot encoding
        features = pd.get_dummies(self.data)
        self.one_hot_features = [column for column in features.columns if column not in self.base_features]
        # Add one hot encoded data to original data
        self.data_all = pd.concat([features[self.one_hot_features], self.data], axis=1)
        # Extract feature names
        feature_names = list(features.columns)
        # Convert to np array
        features = np.array(features)
        labels = np.array(self.labels).reshape((-1,))
        # Empty array for feature importances
        feature_importance_values = np.zeros(len(feature_names))
        print('Training Gradient Boosting Model\n')

        # Iterate through each fold
        lgb_params = {
            'n_jobs': -1,
            'n_estimators': 2000,
            'learning_rate': 0.05,
            'importance_type': importance_type
        }
        for i in range(n_iterations):

            if task == 'classification':
                model = lgb.LGBMClassifier(**lgb_params)
            elif task == 'regression':
                model = lgb.LGBMRegressor(**lgb_params)

            elif task == 'quantile':
                # try different alphas
                alpha = 0.01 + 0.99 / n_iterations * i
                model = lgb.LGBMRegressor(objective='quantile', alpha=alpha, **lgb_params)

            else:
                raise ValueError('Task must be either "classification", "regression", or "quantile"')

            # If training using early stopping or using permutations need a validation set
            if early_stopping or importance_type == 'permutation':
                if task == 'classification':
                    train_features, valid_features, train_labels, valid_labels = train_test_split(features, labels,
                                                                                                  test_size=0.2,
                                                                                                  stratify=labels)
                elif task in ['regression', 'quantile']:
                    train_features, valid_features, train_labels, valid_labels = train_test_split(features, labels,
                                                                                                  test_size=0.2)

                if early_stopping:
                    # Train the model with early stopping
                    try:
                        # 定义回调函数列表
                        callbacks = [
                            lgb.callback.early_stopping(stopping_rounds=100, verbose=False),
                        ]

                        # 使用回调函数列表调用 fit 方法
                        model.fit(train_features, train_labels, eval_metric=eval_metric,
                                  eval_set=[(valid_features, valid_labels)],
                                  callbacks=callbacks)
                    except Exception as e:
                        print("An error occurred:", e)
                else:
                    model.fit(train_features, train_labels)

            else:
                model.fit(features, labels)

            # Record the feature importances
            if importance_type == 'permutation':
                # calculate permutation importance
                r = permutation_importance(model, valid_features, valid_labels,
                                           n_repeats=n_permutations, n_jobs=-1)
                feature_importance_values += r.importances_mean / n_iterations

            else:
                feature_importance_values += model.feature_importances_ / n_iterations

                # Clean up memory
            gc.enable()
            del train_features, train_labels, valid_features, valid_labels
            gc.collect()
            # Record the feature importances

        feature_importances = pd.DataFrame({'feature': feature_names, 'importance': feature_importance_values})

        # Sort based on importance
        feature_importances = feature_importances.sort_values(by='importance', ascending=False).reset_index(drop=True)

        # Normalize the feature importances to add up to one
        postive_features_sum = (feature_importances['importance'] * (feature_importances['importance'] >= 0)).sum()
        feature_importances['normalized_importance'] = feature_importances['importance'] / postive_features_sum
        feature_importances['cumulative_importance'] = np.cumsum(feature_importances['normalized_importance'])

        # Extract the features with zero or negative importance
        record_zero_importance = feature_importances[feature_importances['importance'] <= 0.0]

        to_drop = list(record_zero_importance['feature'])

        self.feature_importances = feature_importances
        self.record_zero_importance = record_zero_importance
        self.removal_ops['zero_importance'] = to_drop

        details = '\n%d features with zero or negative importance after one-hot encoding.\n' % len(
            self.removal_ops['zero_importance'])
        print(details)

        return to_drop, details

    def identify_low_importance(self, cumulative_importance):
        """
        Finds the lowest importance features not needed to account for `cumulative_importance` fraction
        of the total feature importance from the gradient boosting machine.

        Parameters
        --------
        cumulative_importance : float between 0 and 1
            The fraction of cumulative importance to account for

        """
        self.cumulative_importance = cumulative_importance
        # The feature importances need to be calculated before running
        if self.feature_importances is None:
            raise NotImplementedError("""Feature importances have not yet been determined. 
                                         Call the `identify_zero_importance` method first.""")
        # Make sure most important features are on top
        self.feature_importances = self.feature_importances.sort_values('cumulative_importance')
        # Identify the features not needed to reach the cumulative_importance
        record_low_importance = self.feature_importances[
            self.feature_importances['cumulative_importance'] > cumulative_importance]
        to_drop = list(record_low_importance['feature'])
        self.record_low_importance = record_low_importance
        self.removal_ops['low_importance'] = to_drop
        print('%d features required for cumulative importance of %0.2f after one hot encoding.' % (
            len(self.feature_importances) -
            len(self.record_low_importance), self.cumulative_importance))
        details = '%d features do not contribute to cumulative importance of %0.2f.\n' % (
            len(self.removal_ops['low_importance']),
            self.cumulative_importance)
        print(details)
        return to_drop, details

    def remove_features(self, selected_methods, keep_one_hot=True):
        """
        Remove the features from the data according to the specified methods.

        Parameters
        --------
            selected_methods : list of strings or 'all'
                The removal method(s) to use. If 'all', any methods that have been run will be used.
                Available methods:
                    'missing': remove missing features
                    'single_unique': remove features with a single unique value
                    'collinear': remove collinear features
                    'zero_importance': remove zero importance features
                    'low_importance': remove low importance features

            keep_one_hot : boolean, default = True
                Whether or not to keep one-hot encoded features.

        Returns
        --------
            results : dict
                A dictionary containing the information about the removed features for each method.
        """

        features_to_drop = []

        if selected_methods == 'all':
            # Need to use one-hot encoded data
            data = self.data_all

            # Get all features to drop from all methods
            features_to_drop = set(list(chain(*list(self.removal_ops.values()))))

        else:
            # Check if we need to use one-hot encoded data
            if 'zero_importance' in selected_methods or 'low_importance' in selected_methods or self.one_hot_correlated:
                data = self.data_all
            else:
                data = self.data

            # Iterate through the selected methods to collect features to drop
            for method in selected_methods:
                features_to_drop.extend(self.removal_ops[method])

            # Convert to set for unique values
            features_to_drop = set(features_to_drop)

        if not keep_one_hot:
            if self.one_hot_features is None:
                print('Data has not been one-hot encoded')
            else:
                features_to_drop = features_to_drop | set(self.one_hot_features)

        # Remove the features from the data
        data = data.drop(columns=list(features_to_drop))

        # Removal summary
        removal_summary = []

        if not keep_one_hot:
            removal_summary.append(
                f'Removed {len(features_to_drop)} features including one-hot features: {", ".join(features_to_drop)}')
        else:
            removal_summary.append(f'Removed {len(features_to_drop)} features: {", ".join(features_to_drop)}')

        return {"removal_summary": removal_summary}

    def request_stop(self):
        """Set the stop_requested attribute to True."""
        self.stop_requested = True

    def reset_stop(self):
        """Reset the stop_requested attribute to False."""
        self.stop_requested = False
