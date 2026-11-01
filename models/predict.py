from pathlib import Path
import joblib
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = PROJECT_ROOT / "saved_models"


def load_model(model_name):
    model_path = MODEL_DIR / model_name

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    return joblib.load(model_path)


def predict_isolation_forest(features):
    model = load_model("isolation_forest.pkl")

    if isinstance(features, dict):
        features = pd.DataFrame([features])

    prediction = model.predict(features)

    return prediction


def predict_random_forest(features):
    model = load_model("random_forest.pkl")

    if isinstance(features, dict):
        features = pd.DataFrame([features])

    prediction = model.predict(features)

    return prediction


def predict_xgboost(features):
    model = load_model("xgboost.pkl")

    if isinstance(features, dict):
        features = pd.DataFrame([features])

    prediction = model.predict(features)

    return prediction
