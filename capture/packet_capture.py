from collections import defaultdict
from datetime import datetime
from pathlib import Path
from threading import Lock
import json

from scapy.all import sniff

from capture.flow_generator import generate_flow
from models.live_detector import detect_flow


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

LIVE_FLOWS_FILE = PROJECT_ROOT / "logs" / "live_flows.json"


# ============================================================
# FLOW STORAGE
# ============================================================

# Store packets belonging to the same flow
active_flows = defaultdict(list)

# Store recently completed flows for the dashboard
live_flows = []

# Protect shared flow data
flow_lock = Lock()

# Maximum number of completed flows kept
MAX_LIVE_FLOWS = 50

# Number of packets collected before AI analysis
FLOW_PACKET_LIMIT = 10


# ============================================================
# PROTOCOL NAME
# ============================================================

def get_protocol_name(protocol_number):
    """Convert IP protocol numbers into readable names."""

    protocol_names = {
        1: "ICMP",
        6: "TCP",
        17: "UDP",
        47: "GRE",
        50: "ESP",
        51: "AH"
    }

    return protocol_names.get(
        protocol_number,
        f"Protocol {protocol_number}"
    )


# ============================================================
# SAVE LIVE FLOWS
# ============================================================

def save_live_flows(flows):
    """Save recent completed flows for the Flask dashboard."""

    try:

        LIVE_FLOWS_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        temporary_file = LIVE_FLOWS_FILE.with_suffix(
            ".tmp"
        )

        with open(
            temporary_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                flows,
                file,
                indent=2
            )

        # Replace previous file atomically
        temporary_file.replace(
            LIVE_FLOWS_FILE
        )

    except Exception as error:

        print(
            f"Could not save live flows: {error}"
        )


# ============================================================
# PACKET CALLBACK
# ============================================================

def packet_callback(packet):
    """Add packets to flows and analyze completed flows."""

    flow = generate_flow(packet)

    if flow is None:
        return


    # Create a unique flow key
    key = (
        flow["src_ip"],
        flow["dst_ip"],
        flow["src_port"],
        flow["dst_port"],
        flow["protocol"]
    )


    # Add packet to the active flow
    active_flows[key].append(flow)


    # --------------------------------------------------------
    # Analyze flow after enough packets are collected
    # --------------------------------------------------------

    if len(active_flows[key]) >= FLOW_PACKET_LIMIT:

        flow_packets = active_flows[key]

        result = detect_flow(
            flow_packets
        )


        # ----------------------------------------------------
        # Calculate flow information
        # ----------------------------------------------------

        packet_count = result.get(
            "packet_count",
            len(flow_packets)
        )

        total_bytes = result.get(
            "total_bytes",
            sum(
                packet["packet_size"]
                for packet in flow_packets
            )
        )


        # ----------------------------------------------------
        # Create dashboard flow record
        # ----------------------------------------------------

        dashboard_flow = {

            "time": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

            "source_ip": flow["src_ip"],

            "destination_ip": flow["dst_ip"],

            "src_port": flow["src_port"],

            "dst_port": result.get(
                "dst_port",
                flow["dst_port"]
            ),

            "protocol": get_protocol_name(
                flow["protocol"]
            ),

            "packet_count": packet_count,

            "total_bytes": total_bytes,

            "status": result.get(
                "status",
                "NORMAL"
            ),

            "attack_class": result.get(
                "attack_class"
            )
        }


        # ----------------------------------------------------
        # Store completed flow
        # ----------------------------------------------------

        with flow_lock:

            live_flows.append(
                dashboard_flow
            )

            # Keep only newest flows
            if len(live_flows) > MAX_LIVE_FLOWS:

                del live_flows[
                    :-MAX_LIVE_FLOWS
                ]

            # Copy data before releasing lock
            flows_to_save = list(
                live_flows
            )


        # Save outside the lock
        save_live_flows(
            flows_to_save
        )


        # ----------------------------------------------------
        # Console output
        # ----------------------------------------------------

        print("\n--- NIDS Detection ---")

        print(
            f"Time: {dashboard_flow['time']}"
        )

        print(
            f"Source: "
            f"{dashboard_flow['source_ip']}"
        )

        print(
            f"Destination: "
            f"{dashboard_flow['destination_ip']}"
        )

        print(
            f"Source Port: "
            f"{dashboard_flow['src_port']}"
        )

        print(
            f"Destination Port: "
            f"{dashboard_flow['dst_port']}"
        )

        print(
            f"Protocol: "
            f"{dashboard_flow['protocol']}"
        )

        print(
            f"Packet Count: "
            f"{dashboard_flow['packet_count']}"
        )

        print(
            f"Total Bytes: "
            f"{dashboard_flow['total_bytes']}"
        )

        print(
            f"Status: "
            f"{dashboard_flow['status']}"
        )


        if dashboard_flow["attack_class"]:

            print(
                f"Attack Class: "
                f"{dashboard_flow['attack_class']}"
            )


        if "random_forest" in result:

            print(
                f"Random Forest: "
                f"{result['random_forest']}"
            )


        if "xgboost" in result:

            print(
                f"XGBoost: "
                f"{result['xgboost']}"
            )


        # ----------------------------------------------------
        # Remove completed flow
        # ----------------------------------------------------

        del active_flows[key]


# ============================================================
# GET LIVE FLOWS
# ============================================================

def get_live_flows():
    """Return a safe snapshot of recent completed flows."""

    with flow_lock:

        return list(
            live_flows
        )


# ============================================================
# START PACKET CAPTURE
# ============================================================

def start_capture(interface="enp0s3"):

    print(
        f"Starting AI-NIDS capture on {interface}..."
    )

    print(
        "Packets are grouped into flows."
    )

    print(
        f"Flow analysis occurs every "
        f"{FLOW_PACKET_LIMIT} packets."
    )

    print(
        f"Live flows are saved to: "
        f"{LIVE_FLOWS_FILE}"
    )

    print(
        "Press Ctrl+C to stop."
    )


    sniff(
        iface=interface,
        prn=packet_callback,
        store=False
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    start_capture()