import socket

def test_set_get():
    # Test SET command
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 6379))
    
    # Send SET foo bar command in RESP format
    set_cmd = b"*3\r\n$3\r\nSET\r\n$3\r\nfoo\r\n$3\r\nbar\r\n"
    client.send(set_cmd)
    response = client.recv(1024)
    print(f"SET response: {response}")
    client.close()
    
    # Test GET command
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 6379))
    
    # Send GET foo command in RESP format
    get_cmd = b"*2\r\n$3\r\nGET\r\n$3\r\nfoo\r\n"
    client.send(get_cmd)
    response = client.recv(1024)
    print(f"GET response: {response}")
    client.close()
    
    # Test GET non-existent key
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 6379))
    
    # Send GET nonexistent command in RESP format
    get_cmd = b"*2\r\n$3\r\nGET\r\n$11\r\nnonexistent\r\n"
    client.send(get_cmd)
    response = client.recv(1024)
    print(f"GET nonexistent response: {response}")
    client.close()

if __name__ == "__main__":
    test_set_get()
