#!/usr/bin/env python3

import socket
import time
import threading
import subprocess
import sys
import os

def send_command(sock, command):
    """Send a Redis command and return the response."""
    sock.sendall(command.encode())
    response = sock.recv(4096)
    return response

def test_command_processing():
    """Test command processing on replica."""
    
    # Start master server
    print("Starting master server...")
    master_process = subprocess.Popen([
        sys.executable, "app/main.py", "--port", "6381"
    ], cwd=".")
    
    time.sleep(1)  # Give master time to start
    
    try:
        # Start replica server
        print("Starting replica server...")
        replica_process = subprocess.Popen([
            sys.executable, "app/main.py", "--port", "6382", "--replicaof", "localhost 6381"
        ], cwd=".")
        
        time.sleep(2)  # Give replica time to complete handshake
        
        # Connect to master and send commands
        print("Connecting to master...")
        master_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        master_sock.connect(('localhost', 6381))
        
        # Send commands to master (these should be propagated to replica)
        print("Sending SET commands to master...")
        send_command(master_sock, "*3\r\n$3\r\nSET\r\n$3\r\nfoo\r\n$1\r\n1\r\n")
        send_command(master_sock, "*3\r\n$3\r\nSET\r\n$3\r\nbar\r\n$1\r\n2\r\n")
        send_command(master_sock, "*3\r\n$3\r\nSET\r\n$3\r\nbaz\r\n$1\r\n3\r\n")
        
        time.sleep(1)  # Give time for propagation
        
        # Connect to replica and check if commands were processed
        print("Connecting to replica to check processed commands...")
        replica_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        replica_sock.connect(('localhost', 6382))
        
        # Test GET commands on replica
        print("Testing GET foo on replica...")
        response = send_command(replica_sock, "*2\r\n$3\r\nGET\r\n$3\r\nfoo\r\n")
        print(f"GET foo response: {response}")
        
        print("Testing GET bar on replica...")
        response = send_command(replica_sock, "*2\r\n$3\r\nGET\r\n$3\r\nbar\r\n")
        print(f"GET bar response: {response}")
        
        print("Testing GET baz on replica...")
        response = send_command(replica_sock, "*2\r\n$3\r\nGET\r\n$3\r\nbaz\r\n")
        print(f"GET baz response: {response}")
        
        master_sock.close()
        replica_sock.close()
        
        print("✅ Command processing test completed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        # Clean up processes
        try:
            master_process.terminate()
            replica_process.terminate()
            time.sleep(1)
            master_process.kill()
            replica_process.kill()
        except:
            pass

if __name__ == "__main__":
    test_command_processing()
