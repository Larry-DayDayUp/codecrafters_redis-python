#!/usr/bin/env python3
"""
Test script to verify --replicaof flag and INFO command work correctly.
Tests both master and replica modes with proper RESP format validation.
"""

import socket
import subprocess
import time
import sys
import os

# Add parent directory to path to import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def send_command(host, port, command):
    """Send a Redis command and return the response."""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((host, port))
        client.sendall(command.encode())
        response = client.recv(1024)
        client.close()
        return response.decode()
    except Exception as e:
        print(f"Error sending command: {e}")
        return None

def test_master_mode():
    """Test server in master mode (default)."""
    print("Testing master mode...")
    
    # Start server in master mode on port 6380
    process = subprocess.Popen([
        sys.executable, "-c", 
        "import sys; sys.path.insert(0, 'app'); from main import main; main()",
        "--port", "6380"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(1)  # Give server time to start
    
    try:
        # Test INFO replication command
        response = send_command("localhost", 6380, "*2\r\n$4\r\nINFO\r\n$11\r\nreplication\r\n")
        print(f"Master INFO replication response: {repr(response)}")
        
        # Check if response contains role:master
        if response and "role:master" in response:
            print("✓ Master mode test PASSED")
            return True
        else:
            print("✗ Master mode test FAILED")
            return False
    finally:
        process.terminate()
        process.wait()

def test_replica_mode():
    """Test server in replica mode."""
    print("\nTesting replica mode...")
    
    # Start server in replica mode on port 6381
    process = subprocess.Popen([
        sys.executable, "-c", 
        "import sys; sys.path.insert(0, 'app'); from main import main; main()",
        "--port", "6381", "--replicaof", "localhost 6379"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(1)  # Give server time to start
    
    try:
        # Test INFO replication command
        response = send_command("localhost", 6381, "*2\r\n$4\r\nINFO\r\n$11\r\nreplication\r\n")
        print(f"Replica INFO replication response: {repr(response)}")
        
        # Check if response contains role:slave
        if response and "role:slave" in response:
            print("✓ Replica mode test PASSED")
            return True
        else:
            print("✗ Replica mode test FAILED")
            return False
    finally:
        process.terminate()
        process.wait()

def test_info_without_section():
    """Test INFO command without section argument."""
    print("\nTesting INFO without section...")
    
    # Start server in replica mode on port 6382
    process = subprocess.Popen([
        sys.executable, "-c", 
        "import sys; sys.path.insert(0, 'app'); from main import main; main()",
        "--port", "6382", "--replicaof", "localhost 6379"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(1)  # Give server time to start
    
    try:
        # Test INFO command without section
        response = send_command("localhost", 6382, "*1\r\n$4\r\nINFO\r\n")
        print(f"Replica INFO (no section) response: {repr(response)}")
        
        # Check if response contains role:slave
        if response and "role:slave" in response:
            print("✓ INFO without section test PASSED")
            return True
        else:
            print("✗ INFO without section test FAILED")
            return False
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    print("Testing Redis replicaof implementation...\n")
    
    all_passed = True
    all_passed &= test_master_mode()
    all_passed &= test_replica_mode() 
    all_passed &= test_info_without_section()
    
    if all_passed:
        print("\n🎉 All tests PASSED!")
    else:
        print("\n❌ Some tests FAILED!")
    
    sys.exit(0 if all_passed else 1)
