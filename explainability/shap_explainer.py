import pandas as pd
import shap

from preprocessing.feature_extraction import FEATURE_COLUMNS


def create_explainer(model):
    """Create a SHAP TreeExplainer for a tree-based model."""
    return shap.TreeExplainer(model)


def _prepare_features(features):
    """
    Convert feature input into a DataFrame using the
    exact 7 live features expected by the models.
    """

    if isinstance(features, dict):
        features = pd.DataFrame(
            [[features[column] for column in FEATURE_COLUMNS]],
            columns=FEATURE_COLUMNS
        )
    else:
        features = features[FEATURE_COLUMNS].copy()

    return features


def explain_prediction(model, features):
    """
    Generate a SHAP explanation for one prediction.
    """

    features = _prepare_features(features)

    explainer = create_explainer(model)

    return explainer(features)


def get_feature_importance(
    model,
    features,
    predicted_class=None
):
    """
    Calculate SHAP feature importance.

    Handles multiclass XGBoost output with shape:

        (samples, features, classes)
    """

    features = _prepare_features(features)

    explainer = create_explainer(model)

    explanation = explainer(features)

    shap_values = explanation.values

    # ---------------------------------------------------------
    # Multiclass SHAP output
    # Shape = (samples, features, classes)
    # ---------------------------------------------------------
    if shap_values.ndim == 3:

        number_of_classes = shap_values.shape[2]

        if predicted_class is not None:

            # Make absolutely sure the class index is an integer.
            class_index = int(predicted_class)

            # Prevent invalid class indexes.
            if class_index < 0 or class_index >= number_of_classes:
                class_index = 0

            importance = abs(
                shap_values[0, :, class_index]
            )

        else:

            # Average importance across all classes.
            importance = (
                abs(shap_values)
                .mean(axis=2)[0]
            )

    # ---------------------------------------------------------
    # Binary / single-output SHAP
    # Shape = (samples, features)
    # ---------------------------------------------------------
    elif shap_values.ndim == 2:

        importance = abs(
            shap_values[0]
        )

    # ---------------------------------------------------------
    # Fallback
    # ---------------------------------------------------------
    else:

        importance = abs(
            shap_values
        )

        if hasattr(importance, "ndim") and importance.ndim > 1:
            importance = importance[0]

    # Convert to a simple list/array.
    importance = list(importance)

    # Safety check.
    if len(importance) != len(FEATURE_COLUMNS):
        raise ValueError(
            f"SHAP returned {len(importance)} feature values, "
            f"but the system expects {len(FEATURE_COLUMNS)} features."
        )

    result = pd.DataFrame(
        {
            "feature": FEATURE_COLUMNS,
            "importance": importance
        }
    )

    result = result.sort_values(
        by="importance",
        ascending=False
    ).reset_index(drop=True)

    return result


def get_top_features(
    model,
    features,
    top_n=7,
    predicted_class=None
):
    """
    Return the top SHAP features.
    """

    importance = get_feature_importance(
        model,
        features,
        predicted_class=predicted_class
    )

    return importance.head(top_n)


if __name__ == "__main__":

    print(
        "Live SHAP explainer loaded successfully."
    )

    print("Features used by SHAP:")

    for feature in FEATURE_COLUMNS:
        print(f"- {feature}")