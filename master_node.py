# master_node.py
import socket
import json
import threading
import time
import os

DEBUG = bool(os.environ.get('DEBUG', False))

class ResultCollector:
    def __init__(self):
        self.results = {}
        self.lock = threading.Lock()

    def add_result(self, worker_id, result):
        with self.lock:
            self.results[worker_id] = result

    def get_results(self):
        with self.lock:
            return dict(self.results)

def debug_print(msg):
    if DEBUG:
        print(f"[MASTER] {msg}")

def handle_client(client_socket, collector):
    try:
        debug_print("New client connection received")
        data = b""
        while True:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            data += chunk
        
        if data:
            debug_print(f"Received data: {data[:100]}...")  # Print first 100 bytes
            result = json.loads(data.decode())
            worker_id = result.get('worker_id')
            debug_print(f"Processing result from worker {worker_id}")
            collector.add_result(worker_id, result)
            client_socket.sendall(b"OK")
    except Exception as e:
        debug_print(f"Error handling client: {str(e)}")
    finally:
        client_socket.close()

def run_server(collector):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 5000))
    server.listen(5)
    
    debug_print("Master server started on port 5000")
    
    while True:
        client_sock, addr = server.accept()
        debug_print(f"Accepted connection from {addr}")
        client_thread = threading.Thread(
            target=handle_client, 
            args=(client_sock, collector)
        )
        client_thread.daemon = True
        client_thread.start()

def main():
    collector = ResultCollector()
    
    # Start server in a separate thread
    server_thread = threading.Thread(target=run_server, args=(collector,))
    server_thread.daemon = True
    server_thread.start()
    
    # Monitor results in main thread
    while True:
        results = collector.get_results()
        debug_print(f"Current results count: {len(results)}")
        if len(results) >= 2:
            debug_print("\nAll results received!")
            for worker_id, result in results.items():
                debug_print(f"\nWorker {worker_id}:")
                debug_print(f"Graph Size: {result['graph_size']}")
                debug_print(f"Distances: {result['distances']}")
            break
        time.sleep(1)

if __name__ == "__main__":
    main()