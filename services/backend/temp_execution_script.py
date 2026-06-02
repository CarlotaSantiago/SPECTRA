import pandas as pd
from sklearn.model_selection import StratifiedKFold

# Load your data here
data = pd.read_csv('data.csv')

# Define the features and target
X = data.drop('target', axis=1)
y = data['target']

# Initialize the cross-validator
cv = StratifiedKFold(n_splits=10)

# Split the data using the cross-validator
for train_index, test_index in cv.split(X, y):
    X_train, X_test = X.iloc[train_index], X.iloc[test_index]
    y_train, y_test = y.iloc[train_index], y.iloc[test_index]

# Add your model training and evaluation code here