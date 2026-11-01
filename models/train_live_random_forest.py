from pathlib import Path

import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler


# ==============================================================
# PATHS
# ==============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "live_train.csv"
)

MODEL_DIR = PROJECT_ROOT / "saved_models"

RANDOM_STATE = 42


# ==============================================================
# FEATURES
# ==============================================================

FEATURE_COLUMNS = [
    "dst_port",
    "packet_count",
    "total_bytes",
    "avg_packet_size",
    "flow_duration",
    "packets_per_second",
    "bytes_per_second",
]


# ==============================================================
# TRAIN RANDOM FOREST
# ==============================================================

def train_live_random_forest():

    print("=" * 64)
    print("AI-NIDS LIVE RANDOM FOREST TRAINING")
    print("=" * 64)

    print()
    print("Loading live training data...")

    df = pd.read_csv(
        DATA_FILE,
        low_memory=False
    )

    print(
        f"Rows loaded: {len(df)}"
    )

    # ----------------------------------------------------------
    # CHECK REQUIRED FEATURES
    # ----------------------------------------------------------

    missing_features = [
        feature
        for feature in FEATURE_COLUMNS
        if feature not in df.columns
    ]

    if missing_features:

        raise ValueError(
            "Missing required features: "
            + ", ".join(missing_features)
        )

    # ----------------------------------------------------------
    # SELECT FEATURES
    # ----------------------------------------------------------

    X = df[FEATURE_COLUMNS].copy()

    y = (
        df["Label"]
        .astype(str)
        .str.strip()
    )

    print()
    print(
        f"Features used: {X.shape[1]}"
    )

    for feature in FEATURE_COLUMNS:
        print(f"- {feature}")

    # ----------------------------------------------------------
    # CLEAN DATA
    # ----------------------------------------------------------

    X = X.replace(
        [float("inf"), float("-inf")],
        0
    )

    X = X.fillna(0)

    # ----------------------------------------------------------
    # LABEL ENCODING
    # ----------------------------------------------------------

    encoder = LabelEncoder()

    y_encoded = encoder.fit_transform(y)

    print()
    print(
        f"Number of classes: "
        f"{len(encoder.classes_)}"
    )

    print(
        f"Classes: "
        f"{list(encoder.classes_)}"
    )

    # ----------------------------------------------------------
    # SCALE FEATURES
    # ----------------------------------------------------------

    print()
    print("Scaling features...")

    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(X)

    # ----------------------------------------------------------
    # TRAIN / TEST SPLIT
    # ----------------------------------------------------------

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X_scaled,
            y_encoded,
            test_size=0.20,
            random_state=RANDOM_STATE,
            stratify=y_encoded
        )
    )

    print()
    print(
        f"Training samples: "
        f"{len(X_train)}"
    )

    print(
        f"Testing samples: "
        f"{len(X_test)}"
    )

    # ----------------------------------------------------------
    # TRAIN MODEL
    # ----------------------------------------------------------

    print()
    print(
        "Training live Random Forest..."
    )

    model = RandomForestClassifier(
        n_estimators=200,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        class_weight="balanced",
    )

    model.fit(
        X_train,
        y_train
    )

    # ----------------------------------------------------------
    # EVALUATE
    # ----------------------------------------------------------

    y_pred = model.predict(
        X_test
    )

    accuracy = accuracy_score(
        y_test,
        y_pred
    )

    print()
    print("=" * 64)
    print("RANDOM FOREST EVALUATION")
    print("=" * 64)

    print()
    print(
        f"Accuracy: {accuracy:.4f}"
    )

    print()
    print(
        classification_report(
            y_test,
            y_pred,
            target_names=encoder.classes_,
            zero_division=0
        )
    )

    # ----------------------------------------------------------
    # SAVE MODEL
    # ----------------------------------------------------------

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    model_path = (
        MODEL_DIR
        / "live_random_forest.pkl"
    )

    scaler_path = (
        MODEL_DIR
        / "live_random_forest_scaler.pkl"
    )

    encoder_path = (
        MODEL_DIR
        / "live_random_forest_label_encoder.pkl"
    )

    joblib.dump(
        model,
        model_path
    )

    joblib.dump(
        scaler,
        scaler_path
    )

    joblib.dump(
        encoder,
        encoder_path
    )

    # ----------------------------------------------------------
    # FINAL SUMMARY
    # ----------------------------------------------------------

    print()
    print("=" * 64)
    print("LIVE RANDOM FOREST TRAINED SUCCESSFULLY")
    print("=" * 64)

    print()
    print(
        f"Accuracy: {accuracy:.4f}"
    )

    print()
    print(
        f"Model saved to:"
        f"\n{model_path}"
    )

    print()
    print(
        f"Scaler saved to:"
        f"\n{scaler_path}"
    )

    print()
    print(
        f"Label encoder saved to:"
        f"\n{encoder_path}"
    )

    print()
    print("=" * 64)


# ==============================================================
# RUN
# ==============================================================

if __name__ == "__main__":
    train_live_random_forest()