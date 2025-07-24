"""
Test the INFO command implementation
"""
import socket
import subprocess
import time
import sys

def test_info_command():
    """Test INFO replication command"""
    print("Testing INFO replication command...")
    
    # Start server on a custom port
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
                print("✅ INFO replication test passed!")
                return True
            else:
                print(f"❌ Expected 'role:master', got '{content}'")
                return False
        else:
            print(f"❌ Expected bulk string response, got: {response}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    finally:
        client.close()
        process.terminate()
        process.wait()

def test_info_no_args():
    """Test INFO command without arguments"""
    print("\nTesting INFO command without arguments...")
    
    port = 6393
    process = subprocess.Popen(
        [sys.executable, "app/main.py", "--port", str(port)]
    )
    
    time.sleep(1)
    
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("localhost", port))
        
        # Send INFO without arguments
        client.send(b"*1\r\n$4\r\nINFO\r\n")
        response = client.recv(1024).decode()
        print(f"Response: {repr(response)}")
        
        # Should still return role:master
        if "$11\r\nrole:master\r\n" in response:
            print("✅ INFO without args test passed!")
            return True
        else:
            print(f"❌ Unexpected response: {response}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    finally:
        client.close()
        process.terminate()
        process.wait()

if __name__ == "__main__":
    print("🚀 Testing INFO command implementation")
    print("=" * 50)
    
    success1 = test_info_command()
    success2 = test_info_no_args()
    
    if success1 and success2:
        print("\n🎉 All INFO command tests passed!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
