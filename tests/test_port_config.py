"""
Test the port configuration feature for Redis server
"""
import subprocess
import time
import socket
import sys

def test_port_with_connection(port):
    """Start server on specified port and test connection"""
    print(f"Starting server on port {port}...")
    
    # Start server
    process = subprocess.Popen(
        [sys.executable, "app/main.py", "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    time.sleep(1)  # Give server time to start
    
    try:
        # Test connection
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(3)
        client.connect(("localhost", port))
        
        # Send PING
        client.send(b"*1\r\n$4\r\nPING\r\n")
        response = client.recv(1024)
        client.close()
        
        success = response == b"+PONG\r\n"
        print(f"✅ Port {port}: {'PASSED' if success else 'FAILED'}")
        return success
        
    except Exception as e:
        print(f"❌ Port {port}: Connection failed - {e}")
        return False
    finally:
        process.terminate()
        process.wait()

def main():
    print("Testing Redis server port configuration...\n")
    
    # Test default port (should still work)
    print("1. Testing default behavior (no --port specified):")
    process = subprocess.Popen(
        [sys.executable, "app/main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(1)
    
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("localhost", 6379))
        client.send(b"*1\r\n$4\r\nPING\r\n")
        response = client.recv(1024)
        client.close()
        
        if response == b"+PONG\r\n":
            print("✅ Default port 6379: PASSED")
        else:
            print("❌ Default port 6379: FAILED")
    except Exception as e:
        print(f"❌ Default port 6379: FAILED - {e}")
    finally:
        process.terminate()
        process.wait()
    
    print("\n2. Testing custom ports:")
    # Test various custom ports
    test_ports = [6380, 6381, 7000, 8080]
    for port in test_ports:
        test_port_with_connection(port)
    
    print("\n✅ Port configuration testing complete!")

if __name__ == "__main__":
    main()
