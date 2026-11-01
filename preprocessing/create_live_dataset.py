import pandas as pd
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "train.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "live_train.csv"
)

CHUNK_SIZE = 50_000

# Maximum number of samples to keep for common classes.
MAX_SAMPLES_PER_CLASS = 20_000


# ==============================================================
# FEATURE EXTRACTION
# ==============================================================

def create_live_features(chunk):
    """
    Convert CICIDS2017 training features into the
    feature representation used by live AI-NIDS.
    """

    live_data = pd.DataFrame()

    # ----------------------------------------------------------
    # Destination port
    # ----------------------------------------------------------

    live_data["dst_port"] = (
        chunk["Destination Port"]
    )

    # ----------------------------------------------------------
    # Packet count
    # ----------------------------------------------------------

    live_data["packet_count"] = (
        chunk["Total Fwd Packets"]
        + chunk["Total Backward Packets"]
    )

    # ----------------------------------------------------------
    # Total bytes
    # ----------------------------------------------------------

    live_data["total_bytes"] = (
        chunk["Total Length of Fwd Packets"]
        + chunk["Total Length of Bwd Packets"]
    )

    # ----------------------------------------------------------
    # Average packet size
    # ----------------------------------------------------------

    live_data["avg_packet_size"] = (
        live_data["total_bytes"]
        / live_data["packet_count"].replace(0, 1)
    )

    # ----------------------------------------------------------
    # Flow duration
    #
    # CICIDS2017 Flow Duration is in microseconds.
    # Convert to seconds so that the live feature uses
    # the same time unit as Scapy packet timestamps.
    # ----------------------------------------------------------

    live_data["flow_duration"] = (
        chunk["Flow Duration"] / 1_000_000.0
    )

    # ----------------------------------------------------------
    # Packets per second
    # ----------------------------------------------------------

    duration = (
        live_data["flow_duration"]
        .clip(lower=0.001)
    )

    live_data["packets_per_second"] = (
        live_data["packet_count"]
        / duration
    )

    # ----------------------------------------------------------
    # Bytes per second
    # ----------------------------------------------------------

    live_data["bytes_per_second"] = (
        live_data["total_bytes"]
        / duration
    )

    # ----------------------------------------------------------
    # Label
    # ----------------------------------------------------------

    live_data["Label"] = (
        chunk["Label"]
        .astype(str)
        .str.strip()
    )

    # ----------------------------------------------------------
    # Clean invalid numeric values
    # ----------------------------------------------------------

    live_data = live_data.replace(
        [float("inf"), float("-inf")],
        0
    )

    live_data = live_data.fillna(0)

    return live_data


# ==============================================================
# CREATE LIVE DATASET
# ==============================================================

def create_live_dataset():
    """
    Create a balanced live dataset using all available
    CICIDS2017 classes.
    """

    print("=" * 64)
    print("CREATING AI-NIDS LIVE TRAINING DATASET")
    print("=" * 64)

    print()
    print("Input:")
    print(INPUT_FILE)

    print()
    print("Output:")
    print(OUTPUT_FILE)

    print()
    print("This may take some time...")

    class_data = {}

    # ==========================================================
    # READ LARGE TRAINING DATASET IN CHUNKS
    # ==========================================================

    for chunk_number, chunk in enumerate(
        pd.read_csv(
            INPUT_FILE,
            chunksize=CHUNK_SIZE,
            low_memory=False
        ),
        start=1
    ):

        print(
            f"Processing chunk {chunk_number}..."
        )

        # ------------------------------------------------------
        # CREATE 7 LIVE FEATURES
        # ------------------------------------------------------

        live_data = create_live_features(
            chunk
        )

        # ======================================================
        # COLLECT DATA FOR EACH CLASS
        # ======================================================

        for label in live_data["Label"].unique():

            if label not in class_data:
                class_data[label] = []

            current_count = sum(
                len(part)
                for part in class_data[label]
            )

            remaining = (
                MAX_SAMPLES_PER_CLASS
                - current_count
            )

            if remaining <= 0:
                continue

            label_rows = live_data[
                live_data["Label"] == label
            ]

            if len(label_rows) > remaining:

                label_rows = label_rows.iloc[
                    :remaining
                ]

            class_data[label].append(
                label_rows
            )

    # ==========================================================
    # COMBINE EACH CLASS
    # ==========================================================

    datasets = []

    print()
    print("Class distribution before saving:")
    print("-" * 64)

    for label in sorted(class_data.keys()):

        if not class_data[label]:
            continue

        label_data = pd.concat(
            class_data[label],
            ignore_index=True
        )

        label_data = label_data.iloc[
            :MAX_SAMPLES_PER_CLASS
        ]

        datasets.append(
            label_data
        )

        print(
            f"{label}: {len(label_data)} samples"
        )

    # ==========================================================
    # VALIDATE DATA
    # ==========================================================

    if not datasets:

        raise RuntimeError(
            "No live training data was created."
        )

    # ==========================================================
    # COMBINE ALL CLASSES
    # ==========================================================

    live_dataset = pd.concat(
        datasets,
        ignore_index=True
    )

    # ==========================================================
    # SHUFFLE DATASET
    # ==========================================================

    live_dataset = live_dataset.sample(
        frac=1,
        random_state=42
    ).reset_index(
        drop=True
    )

    # ==========================================================
    # SAVE DATASET
    # ==========================================================

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    live_dataset.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # ==========================================================
    # SUMMARY
    # ==========================================================

    print()
    print("=" * 64)
    print("LIVE DATASET CREATED SUCCESSFULLY")
    print("=" * 64)

    print()
    print(f"Rows    : {len(live_dataset)}")

    print(
        f"Classes : "
        f"{live_dataset['Label'].nunique()}"
    )

    print()
    print("Features:")

    for column in live_dataset.columns:
        if column != "Label":
            print(f"- {column}")

    print()
    print(f"Output:")
    print(OUTPUT_FILE)

    print()
    print("Final class distribution:")
    print(
        live_dataset["Label"].value_counts()
    )

    print()
    print("=" * 64)


# ==============================================================
# RUN
# ==============================================================

if __name__ == "__main__":
    create_live_dataset()