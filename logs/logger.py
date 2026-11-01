import csv
from pathlib import Path
from datetime import datetime


PROJECT_ROOT = Path(__file__).resolve().parent.parent

LOG_FILE = PROJECT_ROOT / "logs" / "detections.csv"


def log_detection(
    src_ip,
    dst_ip,
    status,
    attack_class=None
):
    """Log a NIDS detection with its attack class."""

    file_exists = (
        LOG_FILE.exists()
        and LOG_FILE.stat().st_size > 0
    )

    with open(
        LOG_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        if not file_exists:

            writer.writerow([
                "time",
                "source_ip",
                "destination_ip",
                "status",
                "attack_class"
            ])

        writer.writerow([
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            src_ip,
            dst_ip,
            status,
            attack_class if attack_class else ""
        ])


if __name__ == "__main__":

    print(
        "NIDS detection logger loaded successfully."
    )