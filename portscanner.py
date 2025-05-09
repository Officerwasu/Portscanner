import socket
import threading
import time
import sys
from queue import Queue

def scan_port(host, port, open_ports, timeout=3):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((host, port))
        if result == 0:
            open_ports.append(port)
    except socket.error:
        pass
    finally:
        sock.close()

def scan_ports(host, port_start, port_end, num_threads=20, timeout=3):
    open_ports = []
    port_queue = Queue()
    for port in range(port_start, port_end + 1):
        port_queue.put(port)

    def worker():
        while not port_queue.empty():
            port = port_queue.get()
            scan_port(host, port, open_ports, timeout)
            port_queue.task_done()

    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(target=worker)
        threads.append(thread)
        thread.start()

    port_queue.join()
    for thread in threads:
        thread.join()
    return open_ports

def get_host_ip(host):
    try:
        ip_address = socket.gethostbyname(host)
        return ip_address
    except socket.gaierror:
        return None

if __name__ == "__main__":
    target_host = input("Enter the target host (IP address or hostname): ")
    target_ip = get_host_ip(target_host)
    if target_ip is None:
        print("Could not resolve hostname: " + target_host)
        exit(1)
    print("Target IP address: " + target_ip)

    start_port = int(input("Enter the starting port number: "))
    end_port = int(input("Enter the ending port number: "))

    num_threads = int(input("Enter the number of threads (default: 20): ") or 20)
    timeout = int(input("Enter the socket timeout in seconds (default: 3): ") or 3)

    print("Scanning ports " + str(start_port) + " to " + str(end_port) + " on " + target_ip + " using " + str(num_threads) + " threads...")
    start_time = time.time()
    open_ports = scan_ports(target_ip, start_port, end_port, num_threads, timeout)
    end_time = time.time()
    total_time = end_time - start_time

    if open_ports:
        print("Open ports:")
        for port in open_ports:
            print("Port " + str(port) + " is open")
    else:
        print("No open ports found.")
    print("Port scan completed in " + "{:.2f}".format(total_time) + " seconds.")

input("Enter any key to quit.")
sys.exit()
