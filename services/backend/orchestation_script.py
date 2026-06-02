import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold, cross_val_predict, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import f1_score, accuracy_score, cohen_kappa_score, log_loss
from joblib import dump
import xgboost as xgb

# Load dataset (assuming it's already loaded into a DataFrame called df)
# X = df.drop('target', axis=1)
# y = df['target']

# Define the chain strategy
chain_strategy = {
    'strategy': ['especialidad', 'sala', 'prioridad'],
    'dependency': [('sala', 'especialidad'), ('prioridad', 'sala')]
}

# Initialize models and parameters
models = {}
params = {}

# especialidad (NOMINAL, 4 classes)
models['especialidad'] = RandomForestClassifier()
params['especialidad'] = {
    'n_estimators': [50, 100, 200],
    'max_depth': [None, 10, 20, 30]
}

# sala (NOMINAL, 2 classes)
models['sala'] = LogisticRegression(max_iter=1000)
params['sala'] = {
    'C': [0.01, 0.1, 1, 10],
    'penalty': ['l1', 'l2']
}

# prioridad (ORDINAL, 3 classes)
models['prioridad'] = GradientBoostingClassifier()
params['prioridad'] = {
    'n_estimators': [50, 100, 200],
    'max_depth': [None, 10, 20, 30]
}

# Initialize the HybridChain
from skopt import BayesSearchCV

chain_models = {}
for target in chain_strategy['strategy']:
    if models[target].__module__.startswith('sklearn'):
        cv_model = GridSearchCV(models[target], params[target], cv=StratifiedKFold(n_splits=10), scoring='accuracy')
    elif models[target].__module__.startswith('xgboost'):
        cv_model = BayesSearchCV(models[target], params[target], n_iter=50, cv=StratifiedKFold(n_splits=10), verbose=2, n_jobs=-1)
    chain_models[target] = cv_model

# Fit the HybridChain
X_train = df.drop('target', axis=1)
y_train = df['target']

for target in chain_strategy['strategy']:
    if target == 'especialidad':
        y_target = y_train[y_train.index % 2 == 0]
    elif target == 'sala':
        y_target = y_train[(y_train.index % 2 == 1) & (y_train.index % 3 != 0)]
    else:
        y_target = y_train[y_train.index % 3 == 0]

    X_target = X_train[X_train.index.isin(y_target.index)]
    
    if chain_strategy['dependency'] and any(dependency[0] == target for dependency in chain_strategy['dependency']):
        parent_model_name, _ = next((d for d in chain_strategy['dependency'] if d[1] == target), None)
        parent_model_fit = chain_models[parent_model_name].best_estimator_.predict(X_train[X_train.index.isin(y_target.index)])
        X_target = pd.concat([X_target.reset_index(drop=True), pd.Series(parent_model_fit, name=parent_model_name)], axis=1)
    
    chain_models[target].fit(X_target, y_target)

# Save models
for target in chain_strategy['strategy']:
    dump(chain_models[target], f'model_{target}.joblib')

# Print final summary with best params and validation metrics
for target in chain_strategy['strategy']:
    print(f"Model: {target}")
    print("Best Parameters:", chain_models[target].best_params_)
    if 'accuracy' in chain_strategy['targets'][target]['priority_metrics']:
        y_pred = cross_val_predict(chain_models[target], X_train, y_train[y_train.index.isin(y_target.index)], cv=StratifiedKFold(n_splits=10))
        print(f"Validation Accuracy: {accuracy_score(y_train[y_train.index.isin(y_target.index)], y_pred)}")
    if 'F1-Score' in chain_strategy['targets'][target]['priority_metrics']:
        y_pred = cross_val_predict(chain_models[target], X_train, y_train[y_train.index.isin(y_target.index)], cv=StratifiedKFold(n_splits=10))
        print(f"Validation F1-Score: {f1_score(y_train[y_train.index.isin(y_target.index)], y_pred, average='macro')}")
    if 'Kappa' in chain_strategy['targets'][target]['priority_metrics']:
        y_pred = cross_val_predict(chain_models[target], X_train, y_train[y_train.index.isin(y_target.index)], cv=StratifiedKFold(n_splits=10))
        print(f"Validation Kappa: {cohen_kappa_score(y_train[y_train.index.isin(y_target.index)], y_pred)}")
    if 'Log-Loss' in chain_strategy['targets'][target]['priority_metrics']:
        y_pred = cross_val_predict(chain_models[target], X_train, y_train[y_train.index.isin(y_target.index)], cv=StratifiedKFold(n_splits=10))
        print(f"Validation Log-Loss: {log_loss(y_train[y_train.index.isin(y_target.index)], y_pred)}")