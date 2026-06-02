import pandas as pd
from sklearn.model_selection import StratifiedKFold

# Load your data
data = pd.read_csv('data.csv')  # Replace 'your_data.csv' with your actual data file

# Define the target variable and features
target = 'especialidad'
features = [col for col in data.columns if col != target]

# Initialize StratifiedKFold
cv_strategy = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)

# Perform cross-validation
for train_index, test_index in cv_strategy.split(data[features], data[target]):
    X_train, X_test = data.iloc[train_index][features], data.iloc[test_index][features]
    y_train, y_test = data.iloc[train_index][target], data.iloc[test_index][target]

# Continue with your model training and evaluation