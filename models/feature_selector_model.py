import numpy as np
import pandas as pd
from PyQt5.QtCore import pyqtSignal, QObject
from sklearn.exceptions import NotFittedError
from sklearn.model_selection import train_test_split
import lightgbm as lgb
import gc


class FeatureSelectorModel(QObject):
    # Signal definitions
    method_result_signal = pyqtSignal(list, str)
    final_results_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
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
        self.original_features = data.columns.tolist()  # Record the original features

    def select_features(self, selected_methods_and_params, target_column_name, keep_one_hot=True):
        labels = self.data[target_column_name]  # Extracting the target column as labels
        selected_removal_methods = []

        for method, params in selected_methods_and_params.items():
            # Match the method name with the appropriate function call
            if method == 'Missing Values':
                selected_removal_methods.append('missing')
                to_drop, details = self.identify_missing(self.data, params['missing_threshold'])
                print(to_drop)
                print(details)
                print(self.record_missing)
            elif method == 'Single Unique Value':
                selected_removal_methods.append('single_unique')
                to_drop, details = self.identify_single_unique(self.data)
                print(to_drop)
                print(details)
            elif method == 'Collinear Features':
                selected_removal_methods.append('collinear')
                to_drop, details = self.identify_collinear(self.data, params['correlation_threshold'])
                print(to_drop)
                print(details)
            elif method == 'Zero Importance Features':
                selected_removal_methods.append('zero_importance')
                params['labels'] = labels  # Adding labels to the params
                to_drop, details = self.identify_zero_importance(**params)  # Using all params here
                print(to_drop)
                print(details)
            elif method == 'Low Importance Features':
                selected_removal_methods.append('low_importance')
                to_drop, details = self.identify_low_importance(params['cumulative_importance'])
            else:
                continue

            # Emit signal to update the GUI with the results of the individual method
            self.method_result_signal.emit(to_drop, details)

        print(selected_removal_methods)
        # Finally, remove the features based on the results of all methods
        removal_summary = self.remove_features(selected_removal_methods, keep_one_hot)

        # Emit signal to update the GUI with the final results
        self.final_results_signal.emit(removal_summary)

        # Return the result data with the same feature order as the original data
        return self.result_data

    def identify_missing(self, data, missing_threshold):
        """Find the features with a fraction of missing values above `missing_threshold`"""

        self.missing_threshold = missing_threshold

        # Calculate the fraction of missing in each column
        missing_series = data.isnull().sum() / data.shape[0]

        self.missing_stats = pd.DataFrame(missing_series).rename(columns={'index': 'feature', 0: 'missing_fraction'})

        # Find the columns with a missing percentage above the threshold
        record_missing = pd.DataFrame(missing_series[missing_series > missing_threshold]).reset_index().rename(
            columns={'index': 'feature', 0: 'missing_fraction'})

        to_drop = list(record_missing['feature'])

        self.record_missing = record_missing
        self.removal_ops['missing'] = to_drop

        details = '%d features with greater than %0.2f missing values.\n' % (
            len(self.removal_ops['missing']), self.missing_threshold)

        return to_drop, details

    def identify_single_unique(self, data):
        """Identifies features with only a single unique value. NaNs do not count as a unique value."""

        # Calculate the unique counts in each column
        unique_counts = data.nunique()

        self.unique_stats = pd.DataFrame(unique_counts).rename(columns={'index': 'feature', 0: 'nunique'})

        # Find the columns with only one unique count
        record_single_unique = pd.DataFrame(unique_counts[unique_counts == 1]).reset_index().rename(
            columns={'index': 'feature', 0: 'nunique'})

        to_drop = list(record_single_unique['feature'])

        self.record_single_unique = record_single_unique
        self.removal_ops['single_unique'] = to_drop

        details = '%d features with a single unique value.\n' % len(self.removal_ops['single_unique'])

        return to_drop, details

    def identify_collinear(self, data, correlation_threshold):
        """
        Finds collinear features based on the correlation coefficient between features.
        For each pair of features with a correlation coefficient greather than `correlation_threshold`,
        only one of the pair is identified for removal.

        Using code adapted from: https://gist.github.com/Swarchal/e29a3a1113403710b6850590641f046c

        Parameters
        --------

        data : dataframe
            Data observations in the rows and features in the columns

        correlation_threshold : float between 0 and 1
            Value of the Pearson correlation cofficient for identifying correlation features

        """

        self.correlation_threshold = correlation_threshold

        # Calculate the correlations between every column
        corr_matrix = data.corr()

        self.corr_matrix = corr_matrix

        # Extract the upper triangle of the correlation matrix
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(np.bool))

        # Select the features with correlations above the threshold
        # Need to use the absolute value
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

        details = '%d features with a correlation greater than %0.2f.\n' % (
            len(self.removal_ops['collinear']), self.correlation_threshold)

        return to_drop, details

    def identify_zero_importance(self, features, labels, eval_metric, task='classification', n_iterations=10,
                                 early_stopping=True):
        """
        Identify the features with zero importance according to a gradient boosting machine.
        The GBM can be trained with early stopping using a validation set to prevent overfitting.
        The feature importances are averaged over n_iterations to reduce variance.
        Uses the LightGBM implementation (http://lightgbm.readthedocs.io/en/latest/index.html)
        """

        # One hot encoding
        features = pd.get_dummies(features)

        # Extract feature names
        feature_names = list(features.columns)

        # Convert to np array
        features = np.array(features)
        labels = np.array(labels).reshape((-1,))

        # Empty array for feature importances
        feature_importance_values = np.zeros(len(feature_names))

        print('Training Gradient Boosting Model\n')

        # Iterate through each fold
        for _ in range(n_iterations):
            if task == 'classification':
                model = lgb.LGBMClassifier(n_estimators=1000, learning_rate=0.05, verbose=-1)
            elif task == 'regression':
                model = lgb.LGBMRegressor(n_estimators=1000, learning_rate=0.05, verbose=-1)
            else:
                raise ValueError('Task must be either "classification" or "regression"')

            # If training using early stopping, need a validation set
            if early_stopping:
                train_features, valid_features, train_labels, valid_labels = train_test_split(features, labels,
                                                                                              test_size=0.15)

                # Train the model with early stopping
                model.fit(train_features, train_labels, eval_metric=eval_metric,
                          eval_set=[(valid_features, valid_labels)],
                          early_stopping_rounds=100, verbose=-1)

                # Clean up memory
                gc.enable()
                del train_features, train_labels, valid_features, valid_labels
                gc.collect()
            else:
                model.fit(features, labels)

            # Record the feature importances
            feature_importance_values += model.feature_importances_ / n_iterations

        feature_importances = pd.DataFrame({'feature': feature_names, 'importance': feature_importance_values})

        # Sort features according to importance
        feature_importances = feature_importances.sort_values('importance', ascending=False).reset_index(drop=True)

        # Normalize the feature importances to add up to one
        feature_importances['normalized_importance'] = feature_importances['importance'] / feature_importances[
            'importance'].sum()
        feature_importances['cumulative_importance'] = np.cumsum(feature_importances['normalized_importance'])

        # Extract the features with zero importance
        record_zero_importance = feature_importances[feature_importances['importance'] == 0.0]

        to_drop = list(record_zero_importance['feature'])

        self.feature_importances = feature_importances
        self.record_zero_importance = record_zero_importance
        self.removal_ops['zero_importance'] = to_drop

        details = '\n%d features with zero importance.\n' % len(self.removal_ops['zero_importance'])

        return to_drop, details

    def identify_low_importance(self, cumulative_importance):
        """
        Finds the lowest importance features not needed to account for `cumulative_importance`
        of the feature importance from the gradient boosting machine. As an example, if cumulative
        importance is set to 0.95, this will retain only the most important features needed to
        reach 95% of the total feature importance. The identified features are those not needed.

        Parameters
        --------
        cumulative_importance : float between 0 and 1
            The fraction of cumulative importance to account for

        """

        self.cumulative_importance = cumulative_importance

        # The feature importances need to be calculated before running
        if self.feature_importances is None:
            raise NotFittedError(
                'Feature importances have not yet been determined. Call the `identify_zero_importance` method` first.')

        # Make sure most important features are on top
        self.feature_importances = self.feature_importances.sort_values('cumulative_importance')

        # Identify the features not needed to reach the cumulative_importance
        record_low_importance = self.feature_importances[
            self.feature_importances['cumulative_importance'] > cumulative_importance]

        to_drop = list(record_low_importance['feature'])

        self.record_low_importance = record_low_importance
        self.removal_ops['low_importance'] = to_drop

        details = '%d features that do not contribute to cumulative importance of %0.2f.\n' % (
            len(self.removal_ops['low_importance']), self.cumulative_importance)

        return to_drop, details

    def remove_features(self, selected_methods, keep_one_hot=True):
        """
        Remove the features from the data according to the specified methods.

        Parameters
        --------
            selected_methods : list of strings
                The removal method(s) to use.
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

        # If one-hot encoding is required, perform the encoding
        if keep_one_hot:
            data = pd.get_dummies(self.data)
        else:
            data = self.data.copy()

        removal_summary = []

        # Iterate through the selected methods
        for method in selected_methods:
            removed_features = self.removal_ops[method]
            data = data.drop(columns=removed_features)
            removal_summary.append(f'Removed {len(removed_features)} features using {method} method.')
        # Store the data in the global variable with the same feature order as the original data
        # self.result_data = data[self.original_features]
        return {"removal_summary": removal_summary}
