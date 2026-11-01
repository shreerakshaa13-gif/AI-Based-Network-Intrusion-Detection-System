import joblib
import pandas as pd

from pathlib import Path

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


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
# MAIN TRAINING FUNCTION
# ==============================================================

def train_isolation_forest():

    print("=" * 64)
    print("AI-NIDS LIVE ISOLATION FOREST TRAINING")
    print("=" * 64)

    print()
    print("Loading dataset...")

    df = pd.read_csv(DATA_FILE)

    print(f"Dataset shape: {df.shape}")

    # ----------------------------------------------------------
    # CHECK FEATURES
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

    # ----------------------------------------------------------
    # CLEAN DATA
    # ----------------------------------------------------------

    X = X.replace(
        [float("inf"), float("-inf")],
        pd.NA,
    )

    X = X.fillna(0)

    print()
    print("Features used:")

    for feature in FEATURE_COLUMNS:
        print(f"- {feature}")

    # ----------------------------------------------------------
    # SCALE FEATURES
    # ----------------------------------------------------------

    print()
    print("Scaling features...")

    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(X)

    # ----------------------------------------------------------
    # TRAIN ISOLATION FOREST
    # ----------------------------------------------------------

    print()
    print("Training Isolation Forest...")

    model = IsolationForest(
        n_estimators=200,
        contamination=0.10,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X_scaled)

    # ----------------------------------------------------------
    # SAVE MODEL
    # ----------------------------------------------------------

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    model_path = (
        MODEL_DIR
        / "live_isolation_forest.pkl"
    )

    scaler_path = (
        MODEL_DIR
        / "live_isolation_scaler.pkl"
    )

    joblib.dump(
        model,
        model_path,
    )

    joblib.dump(
        scaler,
        scaler_path,
    )

    # ----------------------------------------------------------
    # TRAINING SUMMARY
    # ----------------------------------------------------------

    predictions = model.predict(X_scaled)

    normal_count = int(
        (predictions == 1).sum()
    )

    suspicious_count = int(
        (predictions == -1).sum()
    )

    print()
    print("=" * 64)
    print("TRAINING COMPLETE")
    print("=" * 64)

    print()
    print(f"Total samples      : {len(X)}")
    print(f"Normal samples     : {normal_count}")
    print(f"Suspicious samples : {suspicious_count}")

    print()
    print(f"Model saved to:")
    print(model_path)

    print()
    print(f"Scaler saved to:")
    print(scaler_path)

    print()
    print("=" * 64)


# ==============================================================
# RUN
# ==============================================================

if __name__ == "__main__":
    train_isolation_forest()