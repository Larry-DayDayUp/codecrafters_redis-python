#!/usr/bin/env python3
import socket
import time
import threading
import subprocess
import sys

def test_empty_rdb_transfer():
    """Test that master sends empty RDB file during PSYNC"""
    print("Testing Empty RDB Transfer...")
    
    try:
        # Connect as a replica would
        s = socket.socket()
        s.connect(('localhost', 6379))
        
        # Send PING
        s.send(b'*1\r\n$4\r\nPING\r\n')
        response = s.recv(1024)
        print(f"PING response: {repr(response)}")
        
        # Send REPLCONF listening-port
        s.send(b'*3\r\n$8\r\nREPLCONF\r\n$14\r\nlistening-port\r\n$4\r\n6380\r\n')
        response = s.recv(1024)
        print(f"REPLCONF port response: {repr(response)}")
        
        # Send REPLCONF capa
        s.send(b'*3\r\n$8\r\nREPLCONF\r\n$4\r\ncapa\r\n$6\r\npsync2\r\n')
        response = s.recv(1024)
        print(f"REPLCONF capa response: {repr(response)}")
        
        # Send PSYNC
        s.send(b'*3\r\n$5\r\nPSYNC\r\n$1\r\n?\r\n$2\r\n-1\r\n')
        response = s.recv(4096)
        print(f"PSYNC response length: {len(response)}")
        print(f"PSYNC response starts with: {repr(response[:50])}")
        
        if b'FULLRESYNC' in response and b'REDIS' in response:
            print("✅ Empty RDB transfer test PASSED")
            return True
        else:
            print("❌ Empty RDB transfer test FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Empty RDB transfer test ERROR: {e}")
        return False
    finally:
        s.close()

def test_command_propagation():
    """Test that commands are propagated to replicas"""
    print("\nTesting Command Propagation...")
    
    try:
        # Start a replica process
        replica_process = subprocess.Popen([
            sys.executable, "app/main.py", 
            "--port", "6381", 
            "--replicaof", "localhost 6379"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        time.sleep(2)  # Let replica connect
        
        # Send SET command to master
        master_socket = socket.socket()
        master_socket.connect(('localhost', 6379))
        master_socket.send(b'*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$5\r\nvalue\r\n')
        response = master_socket.recv(1024)
        print(f"Master SET response: {repr(response)}")
        master_socket.close()
        
        time.sleep(1)  # Let command propagate
        
        # Check if replica has the key
        replica_socket = socket.socket()
        replica_socket.connect(('localhost', 6381))
        replica_socket.send(b'*2\r\n$3\r\nGET\r\n$3\r\nkey\r\n')
        response = replica_socket.recv(1024)
        print(f"Replica GET response: {repr(response)}")
        replica_socket.close()
        
        if b'value' in response:
            print("✅ Command propagation test PASSED")
            return True
        else:
            print("❌ Command propagation test FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Command propagation test ERROR: {e}")
        return False
    finally:
        try:
            replica_process.terminate()
            replica_process.wait(timeout=2)
        except:
            replica_process.kill()

def test_wait_command():
    """Test WAIT command functionality"""
    print("\nTesting WAIT Command...")
    
    try:
        # Start a replica process
        replica_process = subprocess.Popen([
            sys.executable, "app/main.py", 
            "--port", "6382", 
            "--replicaof", "localhost 6379"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        time.sleep(2)  # Let replica connect
        
        # Test WAIT with no replicas required
        master_socket = socket.socket()
        master_socket.connect(('localhost', 6379))
        master_socket.send(b'*3\r\n$4\r\nWAIT\r\n$1\r\n0\r\n$4\r\n1000\r\n')
        response = master_socket.recv(1024)
        print(f"WAIT 0 response: {repr(response)}")
        
        # Test WAIT with 1 replica
        master_socket.send(b'*3\r\n$4\r\nWAIT\r\n$1\r\n1\r\n$4\r\n1000\r\n')
        response = master_socket.recv(1024)
        print(f"WAIT 1 response: {repr(response)}")
        
        master_socket.close()
        
        if b':' in response:  # Integer response
            print("✅ WAIT command test PASSED")
            return True
        else:
            print("❌ WAIT command test FAILED")
            return False
            
    except Exception as e:
        print(f"❌ WAIT command test ERROR: {e}")
        return False
    finally:
        try:
            replica_process.terminate()
            replica_process.wait(timeout=2)
        except:
            replica_process.kill()

def main():
    print("=" * 60)
    print("Redis Replication Complete Feature Test Suite")
    print("=" * 60)
    
    # Start master server
    master_process = subprocess.Popen([
        sys.executable, "app/main.py", "--port", "6379"
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    time.sleep(2)  # Let master start
    
    try:
        tests_passed = 0
        total_tests = 3
        
        if test_empty_rdb_transfer():
            tests_passed += 1
        
        if test_command_propagation():
            tests_passed += 1
            
        if test_wait_command():
            tests_passed += 1
        
        print("\n" + "=" * 60)
        print(f"Test Results: {tests_passed}/{total_tests} tests passed")
        print("=" * 60)
        
        if tests_passed == total_tests:
            print("🎉 All replication features working correctly!")
        else:
            print("⚠️  Some tests failed. Check implementation.")
            
    finally:
        # Clean up master process
        try:
            master_process.terminate()
            master_process.wait(timeout=2)
        except:
            master_process.kill()

if __name__ == "__main__":
    main()
