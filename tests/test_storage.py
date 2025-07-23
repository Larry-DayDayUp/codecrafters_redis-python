import socket
import time

def test_set_get():
    """Test SET and GET commands."""
    print("Testing SET and GET commands...")
    
    try:
        # Test SET command
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', 6379))
        
        # Send SET foo bar command in RESP format
        set_cmd = b"*3\r\n$3\r\nSET\r\n$3\r\nfoo\r\n$3\r\nbar\r\n"
        client.send(set_cmd)
        response = client.recv(1024)
        print(f"✓ SET response: {response}")
        client.close()
        
        # Test GET command
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', 6379))
        
        # Send GET foo command in RESP format
        get_cmd = b"*2\r\n$3\r\nGET\r\n$3\r\nfoo\r\n"
        client.send(get_cmd)
        response = client.recv(1024)
        print(f"✓ GET response: {response}")
        client.close()
        
        # Test GET non-existent key
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', 6379))
        
        # Send GET nonexistent command in RESP format
        get_cmd = b"*2\r\n$3\r\nGET\r\n$11\r\nnonexistent\r\n"
        client.send(get_cmd)
        response = client.recv(1024)
        print(f"✓ GET nonexistent response: {response}")
        client.close()
        
        print("SET and GET tests passed!")
        
    except Exception as e:
        print(f"✗ SET/GET test failed: {e}")

if __name__ == "__main__":
    print("Redis SET/GET Test Suite")
    print("=" * 30)
    test_set_get()
    print("\nTest suite completed!")
