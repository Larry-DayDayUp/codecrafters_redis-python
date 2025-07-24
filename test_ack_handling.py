#!/usr/bin/env python3

import socket
import time
import threading
import subprocess
import sys
import os

def send_command(sock, command_bytes):
    """Send a Redis command as bytes and return the response."""
    sock.sendall(command_bytes)
    response = sock.recv(4096)
    return response

def test_ack_handling():
    """Test ACK handling and offset tracking."""
    
    # Start master server
    print("Starting master server...")
    master_process = subprocess.Popen([
        sys.executable, "app/main.py", "--port", "6383"
    ], cwd=".")
    
    time.sleep(1)  # Give master time to start
    
    try:
        # Start replica server
        print("Starting replica server...")
        replica_process = subprocess.Popen([
            sys.executable, "app/main.py", "--port", "6384", "--replicaof", "localhost 6383"
        ], cwd=".")
        
        time.sleep(2)  # Give replica time to complete handshake
        
        # Connect to replica (as master) and send commands
        print("Connecting to replica to test ACK handling...")
        replica_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        replica_sock.connect(('localhost', 6384))
        
        # Perform handshake
        print("Performing handshake with replica...")
        
        # PING
        response = send_command(replica_sock, b"*1\r\n$4\r\nPING\r\n")
        print(f"PING response: {response}")
        
        # REPLCONF listening-port
        response = send_command(replica_sock, b"*3\r\n$8\r\nREPLCONF\r\n$14\r\nlistening-port\r\n$4\r\n6384\r\n")
        print(f"REPLCONF listening-port response: {response}")
        
        # REPLCONF capa
        response = send_command(replica_sock, b"*3\r\n$8\r\nREPLCONF\r\n$4\r\ncapa\r\n$6\r\npsync2\r\n")
        print(f"REPLCONF capa response: {response}")
        
        # PSYNC
        response = send_command(replica_sock, b"*3\r\n$5\r\nPSYNC\r\n$1\r\n?\r\n$2\r\n-1\r\n")
        print(f"PSYNC response: {response[:100]}...")
        
        time.sleep(1)  # Give time for RDB processing
        
        # Now test ACK handling
        print("\nTesting ACK handling...")
        
        # Test 1: Initial GETACK should return 0
        print("Test 1: Initial GETACK")
        response = send_command(replica_sock, b"*3\r\n$8\r\nREPLCONF\r\n$6\r\nGETACK\r\n$1\r\n*\r\n")
        print(f"GETACK response: {response}")
        expected = b"*3\r\n$8\r\nREPLCONF\r\n$3\r\nACK\r\n$1\r\n0\r\n"
        if response == expected:
            print("✅ Test 1 passed: Initial offset is 0")
        else:
            print(f"❌ Test 1 failed: Expected {expected}, got {response}")
        
        # Test 2: Send PING and check offset
        print("\nTest 2: PING command tracking")
        ping_command = b"*1\r\n$4\r\nPING\r\n"
        replica_sock.sendall(ping_command)  # Don't wait for response
        time.sleep(0.1)
        
        response = send_command(replica_sock, b"*3\r\n$8\r\nREPLCONF\r\n$6\r\nGETACK\r\n$1\r\n*\r\n")
        print(f"GETACK after PING: {response}")
        # PING command is 14 bytes: *1\r\n$4\r\nPING\r\n
        expected_offset = 14
        if b"$2\r\n14\r\n" in response:
            print(f"✅ Test 2 passed: Offset correctly updated to {expected_offset}")
        else:
            print(f"❌ Test 2 failed: Expected offset {expected_offset} in response {response}")
        
        # Test 3: Send SET commands and check offset
        print("\nTest 3: SET command tracking")
        set_command1 = b"*3\r\n$3\r\nSET\r\n$3\r\nfoo\r\n$1\r\n1\r\n"  # 29 bytes
        set_command2 = b"*3\r\n$3\r\nSET\r\n$3\r\nbar\r\n$1\r\n2\r\n"  # 29 bytes
        
        replica_sock.sendall(set_command1)
        replica_sock.sendall(set_command2)
        time.sleep(0.1)
        
        response = send_command(replica_sock, b"*3\r\n$8\r\nREPLCONF\r\n$6\r\nGETACK\r\n$1\r\n*\r\n")
        print(f"GETACK after SET commands: {response}")
        # Total: 14 (PING) + 29 (SET foo) + 29 (SET bar) = 72
        expected_offset = 72
        if b"$2\r\n72\r\n" in response:
            print(f"✅ Test 3 passed: Offset correctly updated to {expected_offset}")
        else:
            print(f"❌ Test 3 failed: Expected offset {expected_offset} in response {response}")
        
        replica_sock.close()
        
        print("\n✅ ACK handling test completed")
        
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
    test_ack_handling()
