from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = PROJECT_ROOT / "saved_models"
TRAIN_DATA = PROJECT_ROOT / "data" / "processed" / "train.csv"

SAMPLE_SIZE = 100_000
RANDOM_STATE = 42


def train_random_forest(data_path=TRAIN_DATA):
    """Train Random Forest using a manageable CICIDS2017 sample."""

    print("Loading training data sample...")

    df = pd.read_csv(
        data_path,
        nrows=SAMPLE_SIZE,
        low_memory=False
    )

    print(f"Rows loaded: {len(df)}")

    # Remove spaces from column names
    df.columns = df.columns.str.strip()

    # Check label column
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

    # Encode attack labels
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

    # Train Random Forest
    print("Training Random Forest...")

    model = RandomForestClassifier(
        n_estimators=100,
        random_state=RANDOM_STATE,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    # Calculate accuracy
    accuracy = model.score(X_test, y_test)

    # Save files
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(
        model,
        MODEL_DIR / "random_forest.pkl"
    )

    joblib.dump(
        scaler,
        MODEL_DIR / "random_forest_scaler.pkl"
    )

    joblib.dump(
        encoder,
        MODEL_DIR / "random_forest_label_encoder.pkl"
    )

    print("\nRandom Forest trained successfully.")
    print(f"Accuracy: {accuracy:.4f}")
    print(
        f"Model saved to: "
        f"{MODEL_DIR / 'random_forest.pkl'}"
    )


if __name__ == "__main__":
    train_random_forest()