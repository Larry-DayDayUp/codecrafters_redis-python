#!/usr/bin/env python3
import subprocess
import time
import socket
import sys

def start_replica_and_test():
    """Start replica server and monitor handshake"""
    print("Starting replica server on port 6380...")
    print("This will connect to master at localhost:6379")
    print("-" * 50)
    
    # Start replica server
    replica_process = subprocess.Popen([
        sys.executable, "app/main.py", 
        "--port", "6380", 
        "--replicaof", "localhost 6379"
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    # Give it some time to connect and handshake
    time.sleep(3)
    
    print("\nReplica server output:")
    # Read any available output
    try:
        output, _ = replica_process.communicate(timeout=1)
        print(output)
    except subprocess.TimeoutExpired:
        # Server is still running, which is expected
        pass
    
    # Test if replica server is responding
    print("\nTesting replica server INFO command...")
    try:
        s = socket.socket()
        s.connect(('localhost', 6380))
        s.send(b'*1\r\n$4\r\nINFO\r\n')
        resp = s.recv(1024)
        print("Replica INFO Response:", repr(resp))
        print("Replica role detected:", "slave" if b"role:slave" in resp else "unknown")
        s.close()
        
        if b"role:slave" in resp:
            print("✅ Replica server correctly identifies as slave")
        else:
            print("❌ Replica server role not correct")
            
    except Exception as e:
        print(f"Error testing replica: {e}")
    
    # Clean up
    try:
        replica_process.terminate()
        replica_process.wait(timeout=2)
    except:
        replica_process.kill()
    
    print("\nReplica test completed!")

if __name__ == "__main__":
    start_replica_and_test()
