import socket
import time

def test_expiry():
    # Test SET with PX (expiry)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 6379))
    
    # Send SET foo bar PX 200 command (200ms expiry)
    set_cmd = b"*5\r\n$3\r\nSET\r\n$3\r\nfoo\r\n$3\r\nbar\r\n$2\r\nPX\r\n$3\r\n200\r\n"
    client.send(set_cmd)
    response = client.recv(1024)
    print(f"SET with PX response: {response}")
    client.close()
    
    # Immediately test GET (should return the value)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 6379))
    
    get_cmd = b"*2\r\n$3\r\nGET\r\n$3\r\nfoo\r\n"
    client.send(get_cmd)
    response = client.recv(1024)
    print(f"GET immediate response: {response}")
    client.close()
    
    # Wait for expiry and test GET again (should return null)
    print("Waiting 300ms for key to expire...")
    time.sleep(0.3)  # 300ms - longer than 200ms expiry
    
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 6379))
    
    client.send(get_cmd)
    response = client.recv(1024)
    print(f"GET after expiry response: {response}")
    client.close()

if __name__ == "__main__":
    test_expiry()
