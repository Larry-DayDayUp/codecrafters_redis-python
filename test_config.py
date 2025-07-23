import socket

def test_config_get():
    # Test CONFIG GET dir
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 6379))
    
    config_dir_cmd = b"*3\r\n$6\r\nCONFIG\r\n$3\r\nGET\r\n$3\r\ndir\r\n"
    client.send(config_dir_cmd)
    response = client.recv(1024)
    print(f"CONFIG GET dir response: {response}")
    client.close()
    
    # Test CONFIG GET dbfilename
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 6379))
    
    config_dbfilename_cmd = b"*3\r\n$6\r\nCONFIG\r\n$3\r\nGET\r\n$10\r\ndbfilename\r\n"
    client.send(config_dbfilename_cmd)
    response = client.recv(1024)
    print(f"CONFIG GET dbfilename response: {response}")
    client.close()

if __name__ == "__main__":
    test_config_get()
