"""
Test the INFO command implementation with replicaof support
"""
import socket
import subprocess
import time
import sys

def test_info_command_master():
    """Test INFO replication command in master mode"""
    print("Testing INFO replication command (master mode)...")
    
    # Start server on a custom port in master mode (default)
    port = 6392
    process = subprocess.Popen(
        [sys.executable, "app/main.py", "--port", str(port)]
    )
    
    time.sleep(1)  # Give server time to start
    
    try:
        # Connect to server
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("localhost", port))
        
        # Test INFO replication command
        print("Sending INFO replication command...")
        client.send(b"*2\r\n$4\r\nINFO\r\n$11\r\nreplication\r\n")
        response = client.recv(1024).decode()
        print(f"Response: {repr(response)}")
        
        # Parse the response - should be a bulk string containing "role:master"
        if response.startswith("$"):
            # Extract length and content
            lines = response.split("\r\n")
            length = int(lines[0][1:])  # Remove $ and convert to int
            content = lines[1] if len(lines) > 1 else ""
            
            print(f"Content length: {length}")
            print(f"Content: '{content}'")
            
            if content == "role:master":
                print("✅ INFO replication test (master) passed!")
                return True
            else:
                print(f"❌ Expected 'role:master', got '{content}'")
                return False
        else:
            print(f"❌ Expected bulk string response, got: {response}")
            return False
            
        client.close()
        
    except Exception as e:
        print(f"❌ Error in master test: {e}")
        return False
    finally:
        process.terminate()
        process.wait()

def test_info_command_replica():
    """Test INFO replication command in replica mode"""
    print("\nTesting INFO replication command (replica mode)...")
    
    # Start server on a custom port in replica mode
    port = 6393
    process = subprocess.Popen(
        [sys.executable, "app/main.py", "--port", str(port), "--replicaof", "localhost 6379"]
    )
    
    time.sleep(1)  # Give server time to start
    
    try:
        # Connect to server
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("localhost", port))
        
        # Test INFO replication command
        print("Sending INFO replication command...")
        client.send(b"*2\r\n$4\r\nINFO\r\n$11\r\nreplication\r\n")
        response = client.recv(1024).decode()
        print(f"Response: {repr(response)}")
        
        # Parse the response - should be a bulk string containing "role:slave"
        if response.startswith("$"):
            # Extract length and content
            lines = response.split("\r\n")
            length = int(lines[0][1:])  # Remove $ and convert to int
            content = lines[1] if len(lines) > 1 else ""
            
            print(f"Content length: {length}")
            print(f"Content: '{content}'")
            
            if content == "role:slave":
                print("✅ INFO replication test (replica) passed!")
                return True
            else:
                print(f"❌ Expected 'role:slave', got '{content}'")
                return False
        else:
            print(f"❌ Expected bulk string response, got: {response}")
            return False
            
        client.close()
        
    except Exception as e:
        print(f"❌ Error in replica test: {e}")
        return False
    finally:
        process.terminate()
        process.wait()

def test_info_command_no_section():
    """Test INFO command without section argument"""
    print("\nTesting INFO command without section...")
    
    # Start server on a custom port in replica mode
    port = 6394
    process = subprocess.Popen(
        [sys.executable, "app/main.py", "--port", str(port), "--replicaof", "localhost 6379"]
    )
    
    time.sleep(1)  # Give server time to start
    
    try:
        # Connect to server
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("localhost", port))
        
        # Test INFO command without section
        print("Sending INFO command (no section)...")
        client.send(b"*1\r\n$4\r\nINFO\r\n")
        response = client.recv(1024).decode()
        print(f"Response: {repr(response)}")
        
        # Parse the response - should be a bulk string containing "role:slave"
        if response.startswith("$"):
            # Extract length and content
            lines = response.split("\r\n")
            length = int(lines[0][1:])  # Remove $ and convert to int
            content = lines[1] if len(lines) > 1 else ""
            
            print(f"Content length: {length}")
            print(f"Content: '{content}'")
            
            if content == "role:slave":
                print("✅ INFO command (no section) test passed!")
                return True
            else:
                print(f"❌ Expected 'role:slave', got '{content}'")
                return False
        else:
            print(f"❌ Expected bulk string response, got: {response}")
            return False
            
        client.close()
        
    except Exception as e:
        print(f"❌ Error in no section test: {e}")
        return False
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    print("🧪 Testing INFO command with replicaof support")
    print("=" * 50)
    
    passed = 0
    total = 3
    
    if test_info_command_master():
        passed += 1
    if test_info_command_replica():
        passed += 1
    if test_info_command_no_section():
        passed += 1
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All INFO command tests passed!")
        sys.exit(0)
    else:
        print("❌ Some INFO command tests failed!")
        sys.exit(1)
