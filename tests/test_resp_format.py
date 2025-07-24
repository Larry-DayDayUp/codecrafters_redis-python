#!/usr/bin/env python3
"""Manual test to verify exact RESP format for INFO command."""

import socket
import subprocess
import time
import sys

def test_info_command_resp_format():
    """Test exact RESP format for INFO replication command."""
    print("Testing exact RESP format for INFO replication...")
    
    # Start server in replica mode
    process = subprocess.Popen([
        sys.executable, "../app/main.py", "--port", "6381", "--replicaof", "localhost 6379"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(1)  # Give server time to start
    
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("localhost", 6381))
        
        # Send INFO replication command
        command = "*2\r\n$4\r\nINFO\r\n$11\r\nreplication\r\n"
        client.sendall(command.encode())
        
        # Read response
        response = client.recv(1024)
        client.close()
        
        print(f"Raw response: {repr(response)}")
        print(f"Decoded response: {response.decode()}")
        
        # Check expected format: $10\r\nrole:slave\r\n
        expected = b"$10\r\nrole:slave\r\n"
        if response == expected:
            print("✓ Exact RESP format test PASSED")
            return True
        else:
            print(f"✗ Expected: {repr(expected)}")
            print(f"✗ Got:      {repr(response)}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        process.terminate()
        process.wait()

def test_info_command_master_resp_format():
    """Test exact RESP format for INFO replication command in master mode."""
    print("\nTesting exact RESP format for INFO replication (master)...")
    
    # Start server in master mode
    process = subprocess.Popen([
        sys.executable, "../app/main.py", "--port", "6382"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(1)  # Give server time to start
    
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("localhost", 6382))
        
        # Send INFO replication command
        command = "*2\r\n$4\r\nINFO\r\n$11\r\nreplication\r\n"
        client.sendall(command.encode())
        
        # Read response
        response = client.recv(1024)
        client.close()
        
        print(f"Raw response: {repr(response)}")
        print(f"Decoded response: {response.decode()}")
        
        # Check expected format: $11\r\nrole:master\r\n
        expected = b"$11\r\nrole:master\r\n"
        if response == expected:
            print("✓ Exact RESP format test PASSED")
            return True
        else:
            print(f"✗ Expected: {repr(expected)}")
            print(f"✗ Got:      {repr(response)}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    print("Testing exact RESP format for INFO command...\n")
    
    passed = 0
    total = 2
    
    if test_info_command_master_resp_format():
        passed += 1
    if test_info_command_resp_format():
        passed += 1
        
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All RESP format tests PASSED!")
    else:
        print("❌ Some RESP format tests FAILED!")
