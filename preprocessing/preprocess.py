import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import LabelEncoder, StandardScaler


def load_data(file_path):
    """Load a CICIDS2017 CSV dataset."""
    return pd.read_csv(file_path, low_memory=False)


def preprocess_data(df, target_column="Label"):
    """Prepare CICIDS2017 flow data for machine learning."""

    df = df.copy()

    # Remove spaces from column names
    df.columns = df.columns.str.strip()

    # Remove completely empty rows and columns
    df = df.dropna(axis=0, how="all")
    df = df.dropna(axis=1, how="all")

    # Check that the label column exists
    if target_column not in df.columns:
        raise ValueError(
            f"Target column '{target_column}' not found. "
            f"Available columns: {df.columns.tolist()}"
        )

    # Separate labels from features
    y = df[target_column].astype(str).str.strip()
    X = df.drop(columns=[target_column])

    # Keep only numeric network-flow features
    X = X.select_dtypes(include=["number"])

    # Replace infinity values safely
    X = X.replace([np.inf, -np.inf], np.nan)

    # Replace missing values with column medians
    X = X.fillna(X.median())

    # Replace anything still missing with zero
    X = X.fillna(0)

    # Encode labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return X_scaled, y_encoded, scaler, label_encoder


def save_processed_data(X, y, output_path):
    """Save processed features and labels."""

    output_path = Path(output_path)

    processed = pd.DataFrame(X)
    processed["label"] = y

    output_path.parent.mkdir(parents=True, exist_ok=True)

    processed.to_csv(output_path, index=False)


if __name__ == "__main__":
    print("CICIDS2017 preprocessing module loaded successfully.")