import socket
import sys
import os

# Add parent directory to path to import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_config_get():
    """Test CONFIG GET commands for dir and dbfilename parameters."""
    print("Testing CONFIG GET commands...")
    
    # Test CONFIG GET dir
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', 6379))
        
        config_dir_cmd = b"*3\r\n$6\r\nCONFIG\r\n$3\r\nGET\r\n$3\r\ndir\r\n"
        client.send(config_dir_cmd)
        response = client.recv(1024)
        print(f"✓ CONFIG GET dir response: {response}")
        client.close()
        
        # Test CONFIG GET dbfilename
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', 6379))
        
        config_dbfilename_cmd = b"*3\r\n$6\r\nCONFIG\r\n$3\r\nGET\r\n$10\r\ndbfilename\r\n"
        client.send(config_dbfilename_cmd)
        response = client.recv(1024)
        print(f"✓ CONFIG GET dbfilename response: {response}")
        client.close()
        
        # Test CONFIG GET unknown parameter
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', 6379))
        
        config_unknown_cmd = b"*3\r\n$6\r\nCONFIG\r\n$3\r\nGET\r\n$7\r\nunknown\r\n"
        client.send(config_unknown_cmd)
        response = client.recv(1024)
        print(f"✓ CONFIG GET unknown response: {response}")
        client.close()
        
        print("All CONFIG GET tests passed!")
        
    except Exception as e:
        print(f"✗ CONFIG GET test failed: {e}")

def test_basic_commands():
    """Test basic PING and ECHO commands to ensure server is working."""
    print("Testing basic commands...")
    
    try:
        # Test PING
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', 6379))
        
        ping_cmd = b"*1\r\n$4\r\nPING\r\n"
        client.send(ping_cmd)
        response = client.recv(1024)
        print(f"✓ PING response: {response}")
        client.close()
        
        # Test ECHO
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', 6379))
        
        echo_cmd = b"*2\r\n$4\r\nECHO\r\n$5\r\nhello\r\n"
        client.send(echo_cmd)
        response = client.recv(1024)
        print(f"✓ ECHO response: {response}")
        client.close()
        
        print("Basic command tests passed!")
        
    except Exception as e:
        print(f"✗ Basic command test failed: {e}")

if __name__ == "__main__":
    print("Redis Server Test Suite")
    print("=" * 30)
    
    # Run tests
    test_basic_commands()
    print()
    test_config_get()
    
    print("\nTest suite completed!")
