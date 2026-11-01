from models.live_detector import detect_flow


def test_live_detector():
    flow_packets = []

    for _ in range(10):
        flow_packets.append({
            "src_ip": "10.0.2.2",
            "dst_ip": "10.0.2.15",
            "src_port": 50000,
            "dst_port": 443,
            "protocol": 6,
            "packet_size": 1200
        })

    result = detect_flow(flow_packets)

    assert result["status"] in ["NORMAL", "ATTACK"]

    assert result["dst_port"] == 443
    assert result["packet_count"] == 10
    assert result["total_bytes"] == 12000
    assert result["avg_packet_size"] == 1200.0

    assert "isolation_prediction" in result

    if result["status"] == "ATTACK":
        assert "random_forest" in result
        assert "xgboost" in result
        assert "shap_explanation" in result