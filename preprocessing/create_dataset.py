import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "CSV"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

CHUNK_SIZE = 50_000
RANDOM_STATE = 42


def clean_chunk(df):
    """Clean one CICIDS2017 data chunk."""

    df.columns = df.columns.str.strip()

    df = df.dropna(axis=0, how="all")

    if "Label" not in df.columns:
        raise ValueError("Label column not found.")

    labels = df["Label"].astype(str).str.strip()

    features = df.drop(columns=["Label"])
    features = features.select_dtypes(include=["number"])

    features = features.replace(
        [float("inf"), float("-inf")],
        float("nan")
    )

    features = features.fillna(0)

    features["Label"] = labels.values

    return features


def create_dataset():
    """Create train.csv and test.csv using limited memory."""

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(RAW_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError("No CICIDS2017 CSV files found.")

    print(f"Found {len(csv_files)} CSV files.")

    train_parts = []
    test_parts = []

    for file_path in csv_files:

        print(f"\nProcessing: {file_path.name}")

        for chunk_number, chunk in enumerate(
            pd.read_csv(
                file_path,
                chunksize=CHUNK_SIZE,
                low_memory=False
            ),
            start=1
        ):

            cleaned = clean_chunk(chunk)

            train_chunk, test_chunk = train_test_split(
                cleaned,
                test_size=0.20,
                random_state=RANDOM_STATE,
                stratify=cleaned["Label"]
            )

            train_parts.append(train_chunk)
            test_parts.append(test_chunk)

            print(
                f"  Chunk {chunk_number}: "
                f"{len(cleaned)} rows"
            )

            # Keep only a limited number of chunks in memory
            if len(train_parts) >= 10:

                train_df = pd.concat(
                    train_parts,
                    ignore_index=True
                )

                test_df = pd.concat(
                    test_parts,
                    ignore_index=True
                )

                train_path = PROCESSED_DIR / "train.csv"
                test_path = PROCESSED_DIR / "test.csv"

                train_df.to_csv(
                    train_path,
                    mode="a",
                    header=not train_path.exists(),
                    index=False
                )

                test_df.to_csv(
                    test_path,
                    mode="a",
                    header=not test_path.exists(),
                    index=False
                )

                train_parts.clear()
                test_parts.clear()

    # Save remaining chunks
    if train_parts:

        train_df = pd.concat(
            train_parts,
            ignore_index=True
        )

        test_df = pd.concat(
            test_parts,
            ignore_index=True
        )

        train_path = PROCESSED_DIR / "train.csv"
        test_path = PROCESSED_DIR / "test.csv"

        train_df.to_csv(
            train_path,
            mode="a",
            header=not train_path.exists(),
            index=False
        )

        test_df.to_csv(
            test_path,
            mode="a",
            header=not test_path.exists(),
            index=False
        )

    print("\nDataset creation completed.")
    print(f"Training data: {PROCESSED_DIR / 'train.csv'}")
    print(f"Testing data:  {PROCESSED_DIR / 'test.csv'}")


if __name__ == "__main__":
    create_dataset()