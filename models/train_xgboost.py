from pathlib import Path
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from xgboost import XGBClassifier


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = PROJECT_ROOT / "saved_models"
TRAIN_DATA = PROJECT_ROOT / "data" / "processed" / "train.csv"

SAMPLE_SIZE = 100_000
RANDOM_STATE = 42


def train_xgboost(data_path=TRAIN_DATA):
    """Train XGBoost using a manageable CICIDS2017 sample."""

    print("Loading training data sample...")

    df = pd.read_csv(
        data_path,
        nrows=SAMPLE_SIZE,
        low_memory=False
    )

    print(f"Rows loaded: {len(df)}")

    # Remove spaces from column names
    df.columns = df.columns.str.strip()

    # Check label
    if "Label" not in df.columns:
        raise ValueError("Label column not found.")

    # Separate features and labels
    y = df["Label"].astype(str).str.strip()
    X = df.drop(columns=["Label"])

    # Keep numeric features
    X = X.select_dtypes(include=["number"])

    # Replace infinite values
    X = X.replace(
        [float("inf"), float("-inf")],
        float("nan")
    )

    # Replace missing values
    X = X.fillna(0)

    print(f"Features used: {X.shape[1]}")

    # Encode labels
    encoder = LabelEncoder()
    y_encoded = encoder.fit_transform(y)

    print(f"Classes: {list(encoder.classes_)}")

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled,
        y_encoded,
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=y_encoded
    )

    print(f"Training samples: {len(X_train)}")
    print(f"Testing samples: {len(X_test)}")

    # Train XGBoost
    print("Training XGBoost...")

    model = XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        eval_metric="mlogloss"
    )

    model.fit(X_train, y_train)

    # Accuracy
    accuracy = model.score(X_test, y_test)

    # Save model
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(
        model,
        MODEL_DIR / "xgboost.pkl"
    )

    joblib.dump(
        scaler,
        MODEL_DIR / "xgboost_scaler.pkl"
    )

    joblib.dump(
        encoder,
        MODEL_DIR / "xgboost_label_encoder.pkl"
    )

    print("\nXGBoost trained successfully.")
    print(f"Accuracy: {accuracy:.4f}")
    print(
        f"Model saved to: "
        f"{MODEL_DIR / 'xgboost.pkl'}"
    )


if __name__ == "__main__":
    train_xgboost()