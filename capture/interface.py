from scapy.all import get_if_list


def get_network_interfaces():
    """Return available network interfaces."""
    return get_if_list()


def get_capture_interface():
    """Return the interface used for NIDS packet capture."""
    interfaces = get_network_interfaces()

    if "enp0s3" in interfaces:
        return "enp0s3"

    raise RuntimeError("NIDS network interface 'enp0s3' was not found.")


if __name__ == "__main__":
    interfaces = get_network_interfaces()

    print("Available network interfaces:")

    for interface in interfaces:
        print(f"- {interface}")

    print(f"\nNIDS capture interface: {get_capture_interface()}")
