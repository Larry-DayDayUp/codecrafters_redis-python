#!/usr/bin/env python3
import socket
import time

def test_master_info():
    """Test master server INFO command"""
    try:
        s = socket.socket()
        s.connect(('localhost', 6379))
        s.send(b'*1\r\n$4\r\nINFO\r\n')
        resp = s.recv(1024)
        print("Master INFO Response:", repr(resp))
        print("Master role detected:", "master" if b"role:master" in resp else "unknown")
        s.close()
        return True
    except Exception as e:
        print(f"Error testing master: {e}")
        return False

def test_replconf():
    """Test REPLCONF command"""
    try:
        s = socket.socket()
        s.connect(('localhost', 6379))
        s.send(b'*3\r\n$8\r\nREPLCONF\r\n$14\r\nlistening-port\r\n$4\r\n6380\r\n')
        resp = s.recv(1024)
        print("REPLCONF Response:", repr(resp))
        s.close()
        return resp == b'+OK\r\n'
    except Exception as e:
        print(f"Error testing REPLCONF: {e}")
        return False

def test_psync():
    """Test PSYNC command"""
    try:
        s = socket.socket()
        s.connect(('localhost', 6379))
        s.send(b'*3\r\n$5\r\nPSYNC\r\n$1\r\n?\r\n$2\r\n-1\r\n')
        resp = s.recv(1024)
        print("PSYNC Response:", repr(resp))
        s.close()
        return resp.startswith(b'+FULLRESYNC')
    except Exception as e:
        print(f"Error testing PSYNC: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Redis Handshake Command Tests")
    print("=" * 50)
    
    print("\n1. Testing Master INFO command...")
    if test_master_info():
        print("✅ Master INFO test passed")
    else:
        print("❌ Master INFO test failed")
    
    print("\n2. Testing REPLCONF command...")
    if test_replconf():
        print("✅ REPLCONF test passed")
    else:
        print("❌ REPLCONF test failed")
    
    print("\n3. Testing PSYNC command...")
    if test_psync():
        print("✅ PSYNC test passed")
    else:
        print("❌ PSYNC test failed")
    
    print("\n" + "=" * 50)
    print("All handshake command tests completed!")
    print("=" * 50)
