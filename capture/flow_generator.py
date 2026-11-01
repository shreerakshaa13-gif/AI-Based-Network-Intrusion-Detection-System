from collections import defaultdict
from scapy.all import IP, TCP, UDP


def generate_flow(packet):
    if not packet.haslayer(IP):
        return None

    ip = packet[IP]

    src_port = 0
    dst_port = 0

    if packet.haslayer(TCP):
        src_port = packet[TCP].sport
        dst_port = packet[TCP].dport

    elif packet.haslayer(UDP):
        src_port = packet[UDP].sport
        dst_port = packet[UDP].dport

    return {
        "src_ip": ip.src,
        "dst_ip": ip.dst,
        "src_port": src_port,
        "dst_port": dst_port,
        "protocol": ip.proto,
        "packet_size": len(packet),
        "timestamp": float(packet.time),
    }


def get_flow_key(packet):
    flow = generate_flow(packet)

    if flow is None:
        return None

    return (
        flow["src_ip"],
        flow["dst_ip"],
        flow["src_port"],
        flow["dst_port"],
        flow["protocol"],
    )


def group_flows(packets):
    flows = defaultdict(list)

    for packet in packets:
        key = get_flow_key(packet)

        if key is None:
            continue

        flow = generate_flow(packet)
        flows[key].append(flow)

    return flows