# worker_node.py
from mpi4py import MPI
import numpy as np
import socket
import json
import sys
import time
import os

DEBUG = bool(os.environ.get('DEBUG', False))

def debug_print(msg):
    if DEBUG:
        print(f"[WORKER] {msg}")

def parallel_bfs(adjacency_matrix, start_node):
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    
    debug_print(f"Starting BFS with rank {rank} of {size}")
    
    n = len(adjacency_matrix)
    if rank == 0:
        distances = np.full(n, np.inf)
        distances[start_node] = 0
    else:
        distances = None
    
    distances = comm.bcast(distances, root=0)
    
    while True:
        changes = comm.allreduce(0, op=MPI.SUM)
        if changes == 0:
            break
            
        local_changes = 0
        for i in range(rank, n, size):
            for j in range(n):
                if (adjacency_matrix[i][j] == 1 and 
                    distances[j] > distances[i] + 1):
                    distances[j] = distances[i] + 1
                    local_changes += 1
        
        changes = comm.allreduce(local_changes, op=MPI.SUM)
    
    return distances

def send_result_to_master(worker_id, result_data):
    debug_print(f"Worker {worker_id} preparing to send results")
    
    retries = 3
    for attempt in range(retries):
        try:
            # Wait for a bit before trying to connect
            time.sleep(5 * (attempt + 1))
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)
            debug_print(f"Connecting to master (attempt {attempt + 1})")
            sock.connect(('master', 5000))
            
            data = {
                'worker_id': worker_id,
                'graph_size': len(result_data),
                'distances': result_data.tolist()
            }
            
            json_data = json.dumps(data).encode()
            debug_print(f"Sending {len(json_data)} bytes of data")
            sock.sendall(json_data)
            
            response = sock.recv(1024)
            debug_print(f"Received response: {response}")
            
            if response == b"OK":
                debug_print("Successfully sent results")
                return True
                
        except Exception as e:
            debug_print(f"Error on attempt {attempt + 1}: {str(e)}")
            if attempt < retries - 1:
                continue
        finally:
            sock.close()
    
    return False

if __name__ == "__main__":
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    
    worker_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    debug_print(f"Worker {worker_id} starting with rank {rank}")
    
    # Different graph for each worker
    if worker_id == 1:
        graph = np.array([
            [0, 1, 0, 0, 1],
            [1, 0, 1, 0, 0],
            [0, 1, 0, 1, 0],
            [0, 0, 1, 0, 1],
            [1, 0, 0, 1, 0]
        ])
    else:
        graph = np.array([
            [0, 1, 1, 0, 0, 0],
            [1, 0, 0, 1, 0, 0],
            [1, 0, 0, 0, 1, 0],
            [0, 1, 0, 0, 0, 1],
            [0, 0, 1, 0, 0, 1],
            [0, 0, 0, 1, 1, 0]
        ])
    
    if rank == 0:
        debug_print(f"Worker {worker_id} computing distances")
        distances = parallel_bfs(graph, 0)
        debug_print(f"Worker {worker_id} finished computing")
        
        success = send_result_to_master(worker_id, distances)
        if not success:
            debug_print(f"Worker {worker_id} failed to send results after all retries")