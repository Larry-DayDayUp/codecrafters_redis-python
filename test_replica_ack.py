#!/usr/bin/env python3

import socket
import time
import threading
import subprocess
import sys
import os

def test_replica_ack():
    """Test replica ACK handling by simulating master behavior."""
    
    # Start a replica that connects to a fake master port
    print("Starting replica server...")
    replica_process = subprocess.Popen([
        sys.executable, "app/main.py", "--port", "6385", "--replicaof", "localhost 6386"
    ], cwd=".")
    
    time.sleep(0.5)  # Give replica time to start
    
    try:
        # Create a fake master server
        print("Creating fake master server...")
        master_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        master_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        master_socket.bind(('localhost', 6386))
        master_socket.listen(1)
        
        print("Waiting for replica to connect...")
        replica_conn, addr = master_socket.accept()
        print(f"Replica connected from {addr}")
        
        # Handle handshake
        print("Handling handshake...")
        
        # Receive PING
        data = replica_conn.recv(1024)
        print(f"Received: {data}")
        replica_conn.sendall(b"+PONG\r\n")
        
        # Receive REPLCONF listening-port
        data = replica_conn.recv(1024)
        print(f"Received: {data}")
        replica_conn.sendall(b"+OK\r\n")
        
        # Receive REPLCONF capa
        data = replica_conn.recv(1024)
        print(f"Received: {data}")
        replica_conn.sendall(b"+OK\r\n")
        
        # Receive PSYNC
        data = replica_conn.recv(1024)
        print(f"Received: {data}")
        
        # Send FULLRESYNC + empty RDB
        replica_conn.sendall(b"+FULLRESYNC 8371b4fb1155b71f4a04d3e1bc3e18c4a990aeeb 0\r\n")
        
        # Send empty RDB file
        empty_rdb = (b'REDIS0011\xfa\tredis-ver\x057.2.0\xfa\nredis-bits\xc0@'
                     b'\xfe\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00')
        rdb_response = f"${len(empty_rdb)}\r\n".encode() + empty_rdb
        replica_conn.sendall(rdb_response)
        
        time.sleep(1)  # Give time for RDB processing
        
        print("\nTesting ACK commands...")
        
        # Test 1: Initial GETACK should return 0
        print("Test 1: Initial GETACK")
        replica_conn.sendall(b"*3\r\n$8\r\nREPLCONF\r\n$6\r\nGETACK\r\n$1\r\n*\r\n")
        response = replica_conn.recv(1024)
        print(f"GETACK response: {response}")
        
        if b"*3\r\n$8\r\nREPLCONF\r\n$3\r\nACK\r\n$1\r\n0\r\n" == response:
            print("✅ Test 1 passed: Initial offset is 0")
        else:
            print(f"❌ Test 1 failed: Unexpected response {response}")
        
        # Test 2: Send PING and check offset
        print("\nTest 2: PING command tracking")
        ping_command = b"*1\r\n$4\r\nPING\r\n"
        replica_conn.sendall(ping_command)
        time.sleep(0.1)
        
        # Send GETACK
        replica_conn.sendall(b"*3\r\n$8\r\nREPLCONF\r\n$6\r\nGETACK\r\n$1\r\n*\r\n")
        response = replica_conn.recv(1024)
        print(f"GETACK after PING: {response}")
        
        # PING command is 14 bytes
        if b"$2\r\n14\r\n" in response:
            print("✅ Test 2 passed: Offset correctly updated after PING")
        else:
            print(f"❌ Test 2 failed: Expected offset 14 in response")
        
        # Test 3: Send SET command and check offset
        print("\nTest 3: SET command tracking")
        set_command = b"*3\r\n$3\r\nSET\r\n$3\r\nfoo\r\n$1\r\n1\r\n"  # 29 bytes
        replica_conn.sendall(set_command)
        time.sleep(0.1)
        
        # Send GETACK
        replica_conn.sendall(b"*3\r\n$8\r\nREPLCONF\r\n$6\r\nGETACK\r\n$1\r\n*\r\n")
        response = replica_conn.recv(1024)
        print(f"GETACK after SET: {response}")
        
        # Total: 14 (PING) + 29 (SET) = 43
        if b"$2\r\n43\r\n" in response:
            print("✅ Test 3 passed: Offset correctly updated after SET")
        else:
            print(f"❌ Test 3 failed: Expected offset 43 in response")
        
        replica_conn.close()
        master_socket.close()
        
        print("\n✅ Replica ACK test completed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up processes
        try:
            replica_process.terminate()
            time.sleep(1)
            replica_process.kill()
        except:
            pass

if __name__ == "__main__":
    test_replica_ack()
