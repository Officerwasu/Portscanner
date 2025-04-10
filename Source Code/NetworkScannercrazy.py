import subprocess
import ipaddress
import threading
import queue
import platform

def ping_host(host_ip, results_queue):
    """Pings a single host and adds the result to the queue."""
    try:
        system = platform.system().lower()
        if system == 'windows':
            cmd = ['ping', '-n', '1', '-w', '200', host_ip]
        elif system in ['darwin', 'linux']:
            cmd = ['ping', '-c', '1', '-W', '2', host_ip]
        else:
            print(f"[!] Unsupported OS: {system}")
            return

        response = subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Pinging {host_ip}... {'✔️ Active' if response == 0 else '❌ No response'}")

        if response == 0:
            results_queue.put(host_ip)

    except Exception as e:
        print(f"[!] Error pinging {host_ip}: {e}")

def scan_network_threaded(network_address, start_host, end_host, num_threads=256):
    """Scans a network for active hosts using ping with threading."""
    try:
        network = ipaddress.ip_network(network_address, strict=False)
    except ValueError:
        print("[!] Invalid network address.")
        return []

    results_queue = queue.Queue()
    threads = []

    print(f"Scanning {network_address} from host {start_host} to {end_host}")

    for host_num in range(start_host, end_host + 1):
        if host_num >= len(network):
            break
        host_ip = str(network[host_num])
        thread = threading.Thread(target=ping_host, args=(host_ip, results_queue))
        threads.append(thread)
        thread.start()

        if len(threads) >= num_threads:
            for t in threads:
                t.join()
            threads = []

    for t in threads:
        t.join()

    active_hosts = []
    while not results_queue.empty():
        active_hosts.append(results_queue.get())

    return active_hosts

def get_default_gateway():
    """Retrieves the default gateway IP address."""
    try:
        system = platform.system().lower()
        if system == 'windows':
            output = subprocess.check_output(['ipconfig'], text=True)
            print("ipconfig output:\n", output)
            for line in output.splitlines():
                if 'Default Gateway' in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        gateway = parts[-1].strip()
                        if gateway:
                            return gateway
        elif system in ['darwin', 'linux']:
            output = subprocess.check_output('ip route show default', shell=True, text=True)
            print("Route output:\n", output)
            for line in output.splitlines():
                if 'default via' in line:
                    parts = line.split()
                    if 'via' in parts:
                        gateway = parts[parts.index('via') + 1]
                        return gateway
        else:
            print(f"[!] Unsupported OS: {system}")
            return None
    except Exception as e:
        print(f"[!] Failed to get default gateway: {e}")
        return None

def get_network_range(gateway_ip):
    """Gets the /24 network range of the provided gateway IP."""
    if gateway_ip:
        try:
            network = str(ipaddress.ip_network(gateway_ip + "/24", strict=False))
            return network
        except ValueError as e:
            print(f"[!] Invalid gateway IP: {e}")
            return None
    return None

if __name__ == "__main__":
    gateway = get_default_gateway()
    if gateway:
        print(f"Default Gateway: {gateway}")
        network_range = get_network_range(gateway)
        if network_range:
            print(f"Network Range: {network_range}")
            start_host = 1
            end_host = 254
            active_hosts = scan_network_threaded(network_range, start_host, end_host)
            if active_hosts:
                print("\n✅ Active hosts found:")
                for host in active_hosts:
                    print(f" - {host}")
            else:
                print("❌ No active hosts found.")
        else:
            print("❌ Could not determine network range.")
    else:
        print("❌ Could not retrieve default gateway.")
