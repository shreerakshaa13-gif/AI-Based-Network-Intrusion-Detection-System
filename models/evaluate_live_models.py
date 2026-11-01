from pathlib import Path

import joblib
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = PROJECT_ROOT / "data" / "processed" / "live_train.csv"
MODEL_DIR = PROJECT_ROOT / "saved_models"

RANDOM_STATE = 42


def evaluate_models():

    print("Loading live dataset...")

    df = pd.read_csv(
        DATA_FILE,
        low_memory=False
    )

    print(f"Rows loaded: {len(df)}")

    feature_columns = [
        "dst_port",
        "packet_count",
        "total_bytes",
        "avg_packet_size"
    ]

    X = df[feature_columns]

    y = (
        df["Label"]
        .astype(str)
        .str.strip()
    )

    X = X.replace(
        [float("inf"), float("-inf")],
        0
    )

    X = X.fillna(0)

    # Use the same label encoding as the trained models
    encoder = joblib.load(
        MODEL_DIR / "live_random_forest_label_encoder.pkl"
    )

    scaler = joblib.load(
        MODEL_DIR / "live_random_forest_scaler.pkl"
    )

    model_rf = joblib.load(
        MODEL_DIR / "live_random_forest.pkl"
    )

    model_xgb = joblib.load(
        MODEL_DIR / "live_xgboost.pkl"
    )

    # Encode labels
    y_encoded = encoder.transform(y)

    # Use the same scaling used during training
    X_scaled = scaler.transform(X)

    # Recreate the same test split
    _, X_test, _, y_test = train_test_split(
        X_scaled,
        y_encoded,
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=y_encoded
    )

    print(
        f"Test samples: {len(X_test)}"
    )

    # --------------------------------------------------
    # RANDOM FOREST
    # --------------------------------------------------

    print("\n==============================")
    print("RANDOM FOREST EVALUATION")
    print("==============================")

    rf_predictions = model_rf.predict(
        X_test
    )

    rf_accuracy = accuracy_score(
        y_test,
        rf_predictions
    )

    print(
        f"\nAccuracy: {rf_accuracy:.4f}"
    )

    print("\nClassification Report:")

    print(
        classification_report(
            y_test,
            rf_predictions,
            labels=range(len(encoder.classes_)),
            target_names=encoder.classes_,
            zero_division=0
        )
    )

    print("Confusion Matrix:")

    print(
        confusion_matrix(
            y_test,
            rf_predictions,
            labels=range(len(encoder.classes_))
        )
    )

    # --------------------------------------------------
    # XGBOOST
    # --------------------------------------------------

    print("\n==============================")
    print("XGBOOST EVALUATION")
    print("==============================")

    xgb_predictions = model_xgb.predict(
        X_test
    )

    xgb_accuracy = accuracy_score(
        y_test,
        xgb_predictions
    )

    print(
        f"\nAccuracy: {xgb_accuracy:.4f}"
    )

    print("\nClassification Report:")

    print(
        classification_report(
            y_test,
            xgb_predictions,
            labels=range(len(encoder.classes_)),
            target_names=encoder.classes_,
            zero_division=0
        )
    )

    print("Confusion Matrix:")

    print(
        confusion_matrix(
            y_test,
            xgb_predictions,
            labels=range(len(encoder.classes_))
        )
    )

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    print("\n==============================")
    print("MODEL COMPARISON")
    print("==============================")

    print(
        f"Random Forest Accuracy: {rf_accuracy:.4f}"
    )

    print(
        f"XGBoost Accuracy:       {xgb_accuracy:.4f}"
    )


if __name__ == "__main__":
    evaluate_models()