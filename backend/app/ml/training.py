"""Training utility for administrator-uploaded tabular datasets."""
from pathlib import Path
import json
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

def train_regressor(csv_path: str, target_column: str, artifact_path: str) -> dict:
    data = pd.read_csv(csv_path).drop_duplicates()
    if target_column not in data.columns: raise ValueError(f"Target column '{target_column}' was not found")
    data = data.dropna(subset=[target_column]); features = data.drop(columns=[target_column]); target = data[target_column]
    numeric = features.select_dtypes(include="number").columns.tolist(); categorical = [name for name in features.columns if name not in numeric]
    processor = ColumnTransformer([("numeric", Pipeline([("imputer", SimpleImputer(strategy="median"))]), numeric), ("categorical", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("encode", OneHotEncoder(handle_unknown="ignore"))]), categorical)])
    model = Pipeline([("prepare", processor), ("model", RandomForestRegressor(n_estimators=300, min_samples_leaf=2, random_state=42, n_jobs=-1))])
    x_train, x_test, y_train, y_test = train_test_split(features, target, test_size=.2, random_state=42)
    model.fit(x_train, y_train); prediction = model.predict(x_test); Path(artifact_path).parent.mkdir(parents=True, exist_ok=True); joblib.dump(model, artifact_path)
    return {"rows": len(data), "features": list(features.columns), "metrics": {"mae": round(float(mean_absolute_error(y_test, prediction)), 4), "r2": round(float(r2_score(y_test, prediction)), 4)}, "metadata": json.dumps({"target": target_column})}
