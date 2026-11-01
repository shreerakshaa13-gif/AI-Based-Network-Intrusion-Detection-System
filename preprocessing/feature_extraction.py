import pandas as pd


FEATURE_COLUMNS = [
    "dst_port",
    "packet_count",
    "total_bytes",
    "avg_packet_size",
    "flow_duration",
    "packets_per_second",
    "bytes_per_second",
]


def extract_features(flow_packets):
    if not flow_packets:
        return None

    packet_count = len(flow_packets)

    total_bytes = sum(
        packet["packet_size"]
        for packet in flow_packets
    )

    avg_packet_size = (
        total_bytes / packet_count
        if packet_count > 0
        else 0.0
    )

    timestamps = [
        packet.get("timestamp")
        for packet in flow_packets
        if packet.get("timestamp") is not None
    ]

    if len(timestamps) >= 2:
        flow_duration = max(timestamps) - min(timestamps)
    else:
        flow_duration = 0.0

    duration_for_rate = max(flow_duration, 0.001)

    packets_per_second = (
        packet_count / duration_for_rate
    )

    bytes_per_second = (
        total_bytes / duration_for_rate
    )

    first_packet = flow_packets[0]

    return {
        "dst_port": first_packet["dst_port"],
        "packet_count": packet_count,
        "total_bytes": total_bytes,
        "avg_packet_size": avg_packet_size,
        "flow_duration": flow_duration,
        "packets_per_second": packets_per_second,
        "bytes_per_second": bytes_per_second,
    }


def features_to_dataframe(flow_packets):
    features = extract_features(flow_packets)

    if features is None:
        return pd.DataFrame(columns=FEATURE_COLUMNS)

    return pd.DataFrame(
        [features],
        columns=FEATURE_COLUMNS
    )


if __name__ == "__main__":
    print("Live feature extraction module loaded.")
    print("Features:")

    for feature in FEATURE_COLUMNS:
        print(f"- {feature}")