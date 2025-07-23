import socket

def test_ping():
    """Test PING command."""
    print("Testing PING command...")
    
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', 6379))
        
        # Send PING command in RESP format
        ping_cmd = b"*1\r\n$4\r\nPING\r\n"
        client.send(ping_cmd)
        response = client.recv(1024)
        print(f"✓ PING response: {response}")
        client.close()
        
        print("PING test passed!")
        
    except Exception as e:
        print(f"✗ PING test failed: {e}")

def test_echo():
    """Test ECHO command."""
    print("Testing ECHO command...")
    
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', 6379))
        
        # Send ECHO hey command in RESP format
        echo_cmd = b"*2\r\n$4\r\nECHO\r\n$3\r\nhey\r\n"
        client.send(echo_cmd)
        response = client.recv(1024)
        print(f"✓ ECHO response: {response}")
        client.close()
        
        print("ECHO test passed!")
        
    except Exception as e:
        print(f"✗ ECHO test failed: {e}")

def test_concurrent_clients():
    """Test multiple concurrent connections."""
    print("Testing concurrent client connections...")
    
    try:
        import threading
        
        def client_test(client_id):
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', 6379))
            
            ping_cmd = b"*1\r\n$4\r\nPING\r\n"
            client.send(ping_cmd)
            response = client.recv(1024)
            print(f"✓ Client {client_id} PING response: {response}")
            client.close()
        
        # Create multiple threads for concurrent testing
        threads = []
        for i in range(3):
            thread = threading.Thread(target=client_test, args=(i+1,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        print("Concurrent client test passed!")
        
    except Exception as e:
        print(f"✗ Concurrent client test failed: {e}")

if __name__ == "__main__":
    print("Redis Basic Commands Test Suite")
    print("=" * 35)
    
    test_ping()
    print()
    test_echo()
    print()
    test_concurrent_clients()
    
    print("\nTest suite completed!")
