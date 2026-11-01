from pathlib import Path
import json

import joblib
import pandas as pd

from preprocessing.feature_extraction import (
    extract_features,
    FEATURE_COLUMNS,
)
from explainability.shap_explainer import get_top_features
from logs.logger import log_detection


# ==============================================================
# PROJECT PATHS
# ==============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODEL_DIR = PROJECT_ROOT / "saved_models"

SHAP_FILE = PROJECT_ROOT / "logs" / "shap_results.json"


# ==============================================================
# LOAD MODELS
# ==============================================================

def load_models():
    """
    Load the live NIDS models and preprocessing objects.
    """

    isolation_forest = joblib.load(
        MODEL_DIR / "live_isolation_forest.pkl"
    )

    isolation_scaler = joblib.load(
        MODEL_DIR / "live_isolation_scaler.pkl"
    )

    random_forest = joblib.load(
        MODEL_DIR / "live_random_forest.pkl"
    )

    random_forest_scaler = joblib.load(
        MODEL_DIR / "live_random_forest_scaler.pkl"
    )

    random_forest_encoder = joblib.load(
        MODEL_DIR / "live_random_forest_label_encoder.pkl"
    )

    xgboost = joblib.load(
        MODEL_DIR / "live_xgboost.pkl"
    )

    xgboost_scaler = joblib.load(
        MODEL_DIR / "live_xgboost_scaler.pkl"
    )

    xgboost_encoder = joblib.load(
        MODEL_DIR / "live_xgboost_label_encoder.pkl"
    )

    return {
        "isolation_forest": isolation_forest,
        "isolation_scaler": isolation_scaler,

        "random_forest": random_forest,
        "random_forest_scaler": random_forest_scaler,
        "random_forest_encoder": random_forest_encoder,

        "xgboost": xgboost,
        "xgboost_scaler": xgboost_scaler,
        "xgboost_encoder": xgboost_encoder,
    }


# ==============================================================
# SHAP RESULT STORAGE
# ==============================================================

def save_shap_result(
    features,
    attack_class=None,
    predicted_class=None
):
    """
    Generate and save SHAP explanation for an attack.
    """

    models = load_models()

    xgboost = models["xgboost"]

    shap_result = get_top_features(
        xgboost,
        features,
        top_n=7,
        predicted_class=predicted_class,
    )

    feature_list = []

    for _, row in shap_result.iterrows():
        feature_list.append(
            {
                "feature": row["feature"],
                "importance": float(row["importance"]),
            }
        )

    result = {
        "available": True,
        "attack_class": attack_class,
        "features": feature_list,
    }

    SHAP_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        SHAP_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            result,
            file,
            indent=4,
        )


def clear_shap_result():
    """
    Clear the stored SHAP explanation.
    """

    result = {
        "available": False,
        "attack_class": None,
        "features": [],
    }

    SHAP_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        SHAP_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            result,
            file,
            indent=4,
        )


# ==============================================================
# LIVE FLOW DETECTION
# ==============================================================

def detect_flow(flow_packets):
    """
    Detect a network flow using the two-stage AI-NIDS pipeline.

    Stage 1:
        Isolation Forest

        NORMAL
            -> final NORMAL

        SUSPICIOUS
            -> Stage 2

    Stage 2:
        Random Forest + XGBoost

        Both BENIGN
            -> NORMAL

        Otherwise
            -> ATTACK
    """

    # ----------------------------------------------------------
    # FEATURE EXTRACTION
    # ----------------------------------------------------------

    features = extract_features(flow_packets)

    if features is None:
        return {
            "status": "NORMAL",
            "message": "No valid flow features.",
        }

    feature_df = pd.DataFrame(
        [features],
        columns=FEATURE_COLUMNS,
    )

    # ----------------------------------------------------------
    # LOAD MODELS
    # ----------------------------------------------------------

    models = load_models()

    # ==========================================================
    # STAGE 1 — ISOLATION FOREST
    # ==========================================================

    isolation_forest = models["isolation_forest"]

    isolation_scaler = models["isolation_scaler"]

    isolation_input = isolation_scaler.transform(
        feature_df
    )

    isolation_prediction = isolation_forest.predict(
        isolation_input
    )[0]

    # Isolation Forest:
    #
    #  1  = normal
    # -1  = suspicious

    anomaly_score = float(
        isolation_forest.decision_function(
            isolation_input
        )[0]
    )

    # ----------------------------------------------------------
    # NORMAL TRAFFIC
    # ----------------------------------------------------------

    if isolation_prediction == 1:

        status = "NORMAL"

        clear_shap_result()

        log_detection(
            flow_packets[0]["src_ip"],
            flow_packets[0]["dst_ip"],
            status,
        )

        return {
            "status": status,
            "isolation_prediction": int(
                isolation_prediction
            ),
            "anomaly_score": anomaly_score,

            "dst_port": features["dst_port"],
            "packet_count": features["packet_count"],
            "total_bytes": features["total_bytes"],
            "avg_packet_size": features[
                "avg_packet_size"
            ],
            "flow_duration": features[
                "flow_duration"
            ],
            "packets_per_second": features[
                "packets_per_second"
            ],
            "bytes_per_second": features[
                "bytes_per_second"
            ],

            "attack_class": None,
            "shap_explanation": [],
        }

    # ==========================================================
    # STAGE 1 RESULT — SUSPICIOUS
    # ==========================================================

    status = "SUSPICIOUS"

    # ==========================================================
    # STAGE 2 — RANDOM FOREST + XGBOOST
    # ==========================================================

    random_forest = models["random_forest"]

    random_forest_scaler = models[
        "random_forest_scaler"
    ]

    random_forest_encoder = models[
        "random_forest_encoder"
    ]

    xgboost = models["xgboost"]

    xgboost_scaler = models[
        "xgboost_scaler"
    ]

    xgboost_encoder = models[
        "xgboost_encoder"
    ]

    # ----------------------------------------------------------
    # RANDOM FOREST
    # ----------------------------------------------------------

    rf_input = random_forest_scaler.transform(
        feature_df
    )

    rf_prediction = random_forest.predict(
        rf_input
    )[0]

    rf_class = random_forest_encoder.inverse_transform(
        [rf_prediction]
    )[0]

    # ----------------------------------------------------------
    # RANDOM FOREST CONFIDENCE
    # ----------------------------------------------------------

    rf_confidence = None

    if hasattr(
        random_forest,
        "predict_proba",
    ):
        rf_probabilities = random_forest.predict_proba(
            rf_input
        )[0]

        rf_confidence = float(
            max(rf_probabilities)
        )

    # ----------------------------------------------------------
    # XGBOOST
    # ----------------------------------------------------------

    xgb_input = xgboost_scaler.transform(
        feature_df
    )

    xgb_prediction = xgboost.predict(
        xgb_input
    )[0]

    xgb_prediction = int(
        xgb_prediction
    )

    xgb_class = xgboost_encoder.inverse_transform(
        [xgb_prediction]
    )[0]

    # ----------------------------------------------------------
    # XGBOOST CONFIDENCE
    # ----------------------------------------------------------

    xgb_confidence = None

    if hasattr(
        xgboost,
        "predict_proba",
    ):
        xgb_probabilities = xgboost.predict_proba(
            xgb_input
        )[0]

        xgb_confidence = float(
            max(xgb_probabilities)
        )

    # ==========================================================
    # FINAL DECISION
    # ==========================================================

    if (
        rf_class == "BENIGN"
        and
        xgb_class == "BENIGN"
    ):

        status = "NORMAL"

        attack_class = None

        clear_shap_result()

        log_detection(
            flow_packets[0]["src_ip"],
            flow_packets[0]["dst_ip"],
            status,
        )

    else:

        status = "ATTACK"

        # XGBoost is used as the final attack classifier.

        attack_class = xgb_class

        save_shap_result(
            features,
            attack_class=attack_class,
            predicted_class=xgb_prediction,
        )

    # ----------------------------------------------------------
    # LOG ATTACK / SUSPICIOUS RESULT
    # ----------------------------------------------------------

    if status == "ATTACK":

        log_detection(
            flow_packets[0]["src_ip"],
            flow_packets[0]["dst_ip"],
            status,
            attack_class,
        )

    # ==========================================================
    # FINAL RESULT
    # ==========================================================

    return {
        "status": status,

        "isolation_prediction": int(
            isolation_prediction
        ),

        "anomaly_score": anomaly_score,

        "attack_class": attack_class,

        "random_forest": rf_class,

        "xgboost": xgb_class,

        "random_forest_confidence": rf_confidence,

        "xgboost_confidence": xgb_confidence,

        "dst_port": features["dst_port"],

        "packet_count": features["packet_count"],

        "total_bytes": features["total_bytes"],

        "avg_packet_size": features[
            "avg_packet_size"
        ],

        "flow_duration": features[
            "flow_duration"
        ],

        "packets_per_second": features[
            "packets_per_second"
        ],

        "bytes_per_second": features[
            "bytes_per_second"
        ],

        "shap_explanation": (
            get_top_features(
                xgboost,
                features,
                top_n=7,
                predicted_class=xgb_prediction,
            ).to_dict("records")
            if status == "ATTACK"
            else []
        ),
    }


# ==============================================================
# CONTROLLED TEST FUNCTION
# ==============================================================

def test_attack_sample(
    dst_port,
    packet_count,
    total_bytes,
    avg_packet_size,
    flow_duration,
):
    """
    Test the live RF/XGBoost detector directly
    without capturing network traffic.

    This function is intended for controlled
    AI-NIDS evaluation and demonstration.
    """

    # ----------------------------------------------------------
    # CALCULATE RATE FEATURES
    # ----------------------------------------------------------

    duration_for_rate = max(
        float(flow_duration),
        0.001,
    )

    packets_per_second = (
        packet_count / duration_for_rate
    )

    bytes_per_second = (
        total_bytes / duration_for_rate
    )

    # ----------------------------------------------------------
    # BUILD FEATURE DICTIONARY
    # ----------------------------------------------------------

    features = {
        "dst_port": dst_port,
        "packet_count": packet_count,
        "total_bytes": total_bytes,
        "avg_packet_size": avg_packet_size,
        "flow_duration": flow_duration,
        "packets_per_second": packets_per_second,
        "bytes_per_second": bytes_per_second,
    }

    feature_df = pd.DataFrame(
        [features],
        columns=FEATURE_COLUMNS,
    )

    models = load_models()

    # ==========================================================
    # RANDOM FOREST
    # ==========================================================

    random_forest = models["random_forest"]

    random_forest_scaler = models[
        "random_forest_scaler"
    ]

    random_forest_encoder = models[
        "random_forest_encoder"
    ]

    rf_input = random_forest_scaler.transform(
        feature_df
    )

    rf_prediction = random_forest.predict(
        rf_input
    )[0]

    rf_class = random_forest_encoder.inverse_transform(
        [rf_prediction]
    )[0]

    # ==========================================================
    # XGBOOST
    # ==========================================================

    xgboost = models["xgboost"]

    xgboost_scaler = models[
        "xgboost_scaler"
    ]

    xgboost_encoder = models[
        "xgboost_encoder"
    ]

    xgb_input = xgboost_scaler.transform(
        feature_df
    )

    xgb_prediction = xgboost.predict(
        xgb_input
    )[0]

    xgb_prediction = int(
        xgb_prediction
    )

    xgb_class = xgboost_encoder.inverse_transform(
        [xgb_prediction]
    )[0]

    # ==========================================================
    # FINAL DECISION
    # ==========================================================

    if (
        rf_class == "BENIGN"
        and
        xgb_class == "BENIGN"
    ):

        status = "NORMAL"

        attack_class = None

        shap_explanation = []

        clear_shap_result()

    else:

        status = "ATTACK"

        attack_class = xgb_class

        save_shap_result(
            features,
            attack_class=attack_class,
            predicted_class=xgb_prediction,
        )

        shap_explanation = get_top_features(
            xgboost,
            features,
            top_n=7,
            predicted_class=xgb_prediction,
        ).to_dict("records")

    # ==========================================================
    # DISPLAY TEST RESULTS
    # ==========================================================

    print()
    print("=" * 64)
    print("AI-NIDS CONTROLLED TEST")
    print("=" * 64)

    print()
    print("INPUT FEATURES")
    print("-" * 64)

    print(
        f"Destination Port : {dst_port}"
    )

    print(
        f"Packet Count     : {packet_count}"
    )

    print(
        f"Total Bytes      : {total_bytes}"
    )

    print(
        f"Average Packet   : {avg_packet_size}"
    )

    print(
        f"Flow Duration    : {flow_duration}"
    )

    print(
        f"Packets / Second : {packets_per_second:.4f}"
    )

    print(
        f"Bytes / Second   : {bytes_per_second:.4f}"
    )

    print()
    print("MODEL PREDICTIONS")
    print("-" * 64)

    print(
        f"Random Forest    : {rf_class}"
    )

    print(
        f"XGBoost          : {xgb_class}"
    )

    print()
    print("FINAL AI-NIDS DECISION")
    print("-" * 64)

    print(
        f"Status           : {status}"
    )

    print(
        f"Attack Class     : "
        f"{attack_class if attack_class else 'None'}"
    )

    if shap_explanation:

        print()
        print("SHAP EXPLANATION")
        print("-" * 64)

        for item in shap_explanation:

            print(
                f"{item['feature']:24s}"
                f": {float(item['importance']):.4f}"
            )

    else:

        print()
        print("SHAP EXPLANATION")
        print("-" * 64)

        print(
            "No SHAP explanation for NORMAL traffic."
        )

    print()
    print("=" * 64)
    print("CONTROLLED TEST COMPLETE")
    print("=" * 64)
    print()

    return {
        "status": status,

        "attack_class": attack_class,

        "random_forest": rf_class,

        "xgboost": xgb_class,

        "dst_port": dst_port,

        "packet_count": packet_count,

        "total_bytes": total_bytes,

        "avg_packet_size": avg_packet_size,

        "flow_duration": flow_duration,

        "packets_per_second": packets_per_second,

        "bytes_per_second": bytes_per_second,

        "shap_explanation": shap_explanation,
    }


# ==============================================================
# MODULE TEST
# ==============================================================

if __name__ == "__main__":

    print(
        "Live NIDS detector loaded successfully."
    )

    print()
    print("Features used by the detector:")

    for feature in FEATURE_COLUMNS:
        print(f"- {feature}")