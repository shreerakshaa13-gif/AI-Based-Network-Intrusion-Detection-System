import pandas as pd

from preprocessing.preprocess import preprocess_data


def test_preprocess_data():
    df = pd.DataFrame({
        "duration": [10, 20, 30],
        "protocol": ["tcp", "udp", "tcp"],
        "Label": ["normal", "attack", "normal"]
    })

    X, y, scaler, label_encoder = preprocess_data(df)

    assert X.shape[0] == 3
    assert X.shape[1] == 1
    assert len(y) == 3
    assert scaler is not None
    assert label_encoder is not None