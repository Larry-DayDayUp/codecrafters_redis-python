import socket

def test_redis_commands():
    # Test PING command
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 6379))
    
    # Send PING command in RESP format
    ping_cmd = b"*1\r\n$4\r\nPING\r\n"
    client.send(ping_cmd)
    response = client.recv(1024)
    print(f"PING response: {response}")
    client.close()
    
    # Test ECHO command
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 6379))
    
    # Send ECHO hey command in RESP format
    echo_cmd = b"*2\r\n$4\r\nECHO\r\n$3\r\nhey\r\n"
    client.send(echo_cmd)
    response = client.recv(1024)
    print(f"ECHO response: {response}")
    client.close()

if __name__ == "__main__":
    test_redis_commands()
