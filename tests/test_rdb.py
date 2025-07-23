import subprocess
import time
import socket
import os
import tempfile

def create_test_rdb_file(filepath):
    """Create a simple RDB file for testing"""
    # This is a minimal RDB file with a single key-value pair: "testkey" -> "testvalue"
    rdb_data = bytes([
        # Header: REDIS0011
        0x52, 0x45, 0x44, 0x49, 0x53, 0x30, 0x30, 0x31, 0x31,
        # Metadata section - redis version
        0xFA, 0x09, 0x72, 0x65, 0x64, 0x69, 0x73, 0x2D, 0x76, 0x65, 0x72, 
        0x05, 0x37, 0x2E, 0x32, 0x2E, 0x30,
        # Database selector - database 0
        0xFE, 0x00,
        # Hash table size info
        0xFB, 0x01, 0x00,
        # Key-value pair: "testkey" -> "testvalue" (no expiry)
        0x00,  # String type
        0x07, 0x74, 0x65, 0x73, 0x74, 0x6B, 0x65, 0x79,  # key: "testkey"
        0x09, 0x74, 0x65, 0x73, 0x74, 0x76, 0x61, 0x6C, 0x75, 0x65,  # value: "testvalue"
        # End of file
        0xFF,
        # CRC64 checksum (8 bytes) - simplified for testing
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    ])
    
    with open(filepath, 'wb') as f:
        f.write(rdb_data)

def test_rdb_loading():
    """Test that RDB files are loaded correctly on startup"""
    print("Testing RDB file loading...")
    
    # Create a temporary directory for our test RDB file
    with tempfile.TemporaryDirectory() as temp_dir:
        rdb_file = os.path.join(temp_dir, "test.rdb")
        create_test_rdb_file(rdb_file)
        
        print(f"Created test RDB file: {rdb_file}")
        
        # Start the server with our test RDB file
        process = subprocess.Popen(
            ["python", "app/main.py", "--dir", temp_dir, "--dbfilename", "test.rdb", "--port", "6391"],
            cwd="c:\\Users\\33233\\Desktop\\CodeCrafter\\codecrafters-redis-python"
        )
        
        time.sleep(2)  # Give server time to start and load RDB
        
        try:
            # Connect and test KEYS command
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(("localhost", 6391))
            
            # Test KEYS * - should return the key from RDB file
            client_socket.send(b"*2\r\n$4\r\nKEYS\r\n$1\r\n*\r\n")
            response = client_socket.recv(1024).decode()
            print(f"KEYS * response: {response}")
            
            # Should return array with "testkey"
            assert response.startswith("*1"), f"Expected array with 1 item, got: {response}"
            assert "testkey" in response, f"Expected 'testkey' in response, got: {response}"
            
            # Test GET command for the loaded key
            client_socket.send(b"*2\r\n$3\r\nGET\r\n$7\r\ntestkey\r\n")
            get_response = client_socket.recv(1024).decode()
            print(f"GET testkey response: {get_response}")
            
            # Should return the value "testvalue"
            assert "testvalue" in get_response, f"Expected 'testvalue' in response, got: {get_response}"
            
            client_socket.close()
            print("✓ RDB test passed - key loaded from RDB file successfully")
            
        except Exception as e:
            print(f"❌ RDB test failed: {e}")
            raise
        finally:
            process.terminate()
            process.wait()

if __name__ == "__main__":
    test_rdb_loading()
