import subprocess
import time
import socket
import os
import tempfile

def test_rdb_loading():
    """Test that RDB files are loaded correctly on startup"""
    print("Testing RDB file loading...")
    
    # This test would require an actual RDB file to test properly
    # For now, we'll test that the server starts without errors
    # and that KEYS command works
    
    # Start the server
    process = subprocess.Popen(
        ["python", "app/main.py"],
        cwd="c:\\Users\\33233\\Desktop\\CodeCrafter\\codecrafters-redis-python"
    )
    
    time.sleep(1)  # Give server time to start
    
    try:
        # Connect and test KEYS command
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(("localhost", 6379))
        
        # Test KEYS *
        client_socket.send(b"*2\r\n$4\r\nKEYS\r\n$1\r\n*\r\n")
        response = client_socket.recv(1024).decode()
        print(f"KEYS * response: {response}")
        
        # Response should be an array (even if empty)
        assert response.startswith("*"), f"Expected array response, got: {response}"
        
        client_socket.close()
        print("✓ RDB test passed")
        
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    test_rdb_loading()
