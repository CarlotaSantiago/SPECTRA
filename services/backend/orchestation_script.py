import xgboost as xgb

# Ensure the XGBClassifier is available in the environment
model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='mlogloss')