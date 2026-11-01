
from pathlib import Path
import csv
import json

from flask import Flask, render_template, jsonify


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

LOG_FILE = PROJECT_ROOT / "logs" / "detections.csv"
SHAP_FILE = PROJECT_ROOT / "logs" / "shap_results.json"
LIVE_FLOWS_FILE = PROJECT_ROOT / "logs" / "live_flows.json"
ATTACK_HISTORY_FILE = PROJECT_ROOT / "logs" / "attack_history.json"


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(
    __name__,
    template_folder="dashboard/templates",
    static_folder="dashboard/static",
    static_url_path="/static"
)


# ============================================================
# HELPER: READ DETECTION HISTORY
# ============================================================

def read_detections():
    """Read all available detection records from the CSV file."""

    records = []

    if not LOG_FILE.exists():
        return records

    with LOG_FILE.open(
        "r",
        encoding="utf-8",
        newline=""
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            records.append({
                "time": row.get("time", ""),
                "source_ip": row.get("source_ip", ""),
                "destination_ip": row.get("destination_ip", ""),
                "status": (row.get("status") or "").strip().upper(),
                "attack_class": row.get("attack_class", "")
            })

    return records


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():
    return jsonify({
        "status": "running"
    })


# ============================================================
# DETECTIONS SUMMARY AND RECENT DETECTIONS
# ============================================================

@app.route("/detections")
def detections():
    try:
        all_records = read_detections()

    except (OSError, csv.Error) as error:
        app.logger.exception("Could not read detections")
        return jsonify({
            "normal": 0,
            "suspicious": 0,
            "attacks": 0,
            "detections": [],
            "error": str(error)
        }), 500

    normal_count = sum(
        record["status"] == "NORMAL"
        for record in all_records
    )

    suspicious_count = sum(
        record["status"] == "SUSPICIOUS"
        for record in all_records
    )

    attack_count = sum(
        record["status"] == "ATTACK"
        for record in all_records
    )

    # Return the latest 20 records, newest first.
    recent_records = list(reversed(all_records[-20:]))

    return jsonify({
        "normal": normal_count,
        "suspicious": suspicious_count,
        "attacks": attack_count,
        "detections": recent_records
    }), 200, {
        "Cache-Control": "no-store"
    }


# ============================================================
# COMPLETE ATTACK HISTORY
# ============================================================

@app.route("/attack-history")
def attack_history():
    """
    Return every ATTACK record stored in detections.csv.

    Existing records are retained in the CSV.
    Future ATTACK records appear automatically when
    the detector appends them to the same CSV file.
    """

    try:
        all_records = read_detections()

        attacks = [
            record
            for record in all_records
            if record["status"] == "ATTACK"
        ]

        # Newest first; do not limit the history to 20 records.
        attacks.reverse()

        return jsonify({
            "total": len(attacks),
            "attacks": attacks
        }), 200, {
            "Cache-Control": "no-store"
        }

    except (OSError, csv.Error) as error:
        app.logger.exception("Could not load attack history")

        return jsonify({
            "total": 0,
            "attacks": [],
            "error": str(error)
        }), 500, {
            "Cache-Control": "no-store"
        }


# ============================================================
# SHAP EXPLANATION
# ============================================================

@app.route("/shap")
def shap_explanation():
    response = {
        "available": False,
        "features": [],
        "attack_class": None,
        "message": "No SHAP explanation available."
    }

    if not SHAP_FILE.exists():
        response["message"] = "SHAP results file does not exist."

        return jsonify(response), 200, {
            "Cache-Control": "no-store"
        }

    try:
        with SHAP_FILE.open(
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError(
                "SHAP results must contain a JSON object."
            )

        features = data.get("features", [])
        attack_class = data.get("attack_class")
        available = data.get("available", False)

        if not isinstance(features, list):
            raise ValueError(
                "'features' must be a JSON list."
            )

        available = bool(
            available and features and attack_class
        )

        response = {
            "available": available,
            "features": features if available else [],
            "attack_class": attack_class if available else None,
            "message": (
                "SHAP explanation loaded."
                if available
                else "No SHAP explanation is currently available."
            )
        }

        return jsonify(response), 200, {
            "Cache-Control": "no-store"
        }

    except (OSError, json.JSONDecodeError, ValueError) as error:
        app.logger.exception(
            "Could not load SHAP results"
        )

        response["message"] = (
            f"Could not load SHAP results: {error}"
        )

        return jsonify(response), 500, {
            "Cache-Control": "no-store"
        }


# ============================================================
# LIVE NETWORK FLOWS
# ============================================================

@app.route("/live-flows")
def live_flows():
    if not LIVE_FLOWS_FILE.exists():
        return jsonify({
            "status": "waiting",
            "flows": []
        }), 200, {
            "Cache-Control": "no-store"
        }

    try:
        with LIVE_FLOWS_FILE.open(
            "r",
            encoding="utf-8"
        ) as file:
            flows = json.load(file)

        if not isinstance(flows, list):
            raise ValueError(
                "Live flows must contain a JSON list."
            )

        latest_flows = list(
            reversed(flows[-20:])
        )

        return jsonify({
            "status": "running",
            "flows": latest_flows
        }), 200, {
            "Cache-Control": "no-store"
        }

    except (OSError, json.JSONDecodeError, ValueError) as error:
        app.logger.exception(
            "Could not load live flows"
        )

        return jsonify({
            "status": "error",
            "flows": [],
            "message": (
                f"Could not load live flows: {error}"
            )
        }), 500, {
            "Cache-Control": "no-store"
        }


# ============================================================
# START FLASK
# ============================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
