import socket  # noqa: F401
import threading
import time

BUF_SIZE = 4096

# Global data store for key-value pairs and expiration times
data_store = {}
expiry_store = {}  # key -> expiration timestamp in seconds
data_store_lock = threading.Lock()


def parse_resp(data: bytes):
    """Parse RESP (Redis Serialization Protocol) format."""
    lines = data.decode().split('\r\n')
    if not lines[0].startswith('*'):
        return []
    
    num_elements = int(lines[0][1:])
    elements = []
    line_idx = 1
    
    for _ in range(num_elements):
        if line_idx >= len(lines) or not lines[line_idx].startswith('$'):
            break
        length = int(lines[line_idx][1:])
        line_idx += 1
        if line_idx < len(lines):
            elements.append(lines[line_idx])
        line_idx += 1
    
    return elements


def is_key_expired(key):
    """Check if a key has expired."""
    if key not in expiry_store:
        return False
    return time.time() > expiry_store[key]


def cleanup_expired_key(key):
    """Remove expired key from both stores."""
    if key in data_store:
        del data_store[key]
    if key in expiry_store:
        del expiry_store[key]


def handle_command(client: socket.socket):
    while chunk := client.recv(BUF_SIZE):
        if chunk == b"":
            break
        
        # print(f"[CHUNK] ```\n{chunk.decode()}\n```")
        
        # Parse the Redis command
        try:
            command_parts = parse_resp(chunk)
            if not command_parts:
                continue
                
            command = command_parts[0].upper()
            
            if command == "PING":
                client.sendall(b"+PONG\r\n")
            elif command == "ECHO":
                if len(command_parts) > 1:
                    echo_arg = command_parts[1]
                    # Return as RESP bulk string: $<length>\r\n<string>\r\n
                    response = f"${len(echo_arg)}\r\n{echo_arg}\r\n".encode()
                    client.sendall(response)
                else:
                    # No argument provided
                    client.sendall(b"-ERR wrong number of arguments for 'echo' command\r\n")
            elif command == "SET":
                if len(command_parts) >= 3:
                    key = command_parts[1]
                    value = command_parts[2]
                    
                    # Check for PX argument (expiry in milliseconds)
                    expiry_time = None
                    if len(command_parts) >= 5 and command_parts[3].upper() == "PX":
                        try:
                            expiry_ms = int(command_parts[4])
                            expiry_time = time.time() + (expiry_ms / 1000.0)  # Convert to seconds
                        except ValueError:
                            client.sendall(b"-ERR value is not an integer or out of range\r\n")
                            continue
                    
                    # Store the key-value pair
                    with data_store_lock:
                        data_store[key] = value
                        if expiry_time:
                            expiry_store[key] = expiry_time
                        elif key in expiry_store:
                            # Remove any existing expiry if setting without PX
                            del expiry_store[key]
                    
                    # Return OK as RESP simple string
                    client.sendall(b"+OK\r\n")
                else:
                    # Wrong number of arguments
                    client.sendall(b"-ERR wrong number of arguments for 'set' command\r\n")
            elif command == "GET":
                if len(command_parts) >= 2:
                    key = command_parts[1]
                    
                    # Check and retrieve the value
                    with data_store_lock:
                        # Check if key has expired
                        if is_key_expired(key):
                            cleanup_expired_key(key)
                            value = None
                        else:
                            value = data_store.get(key)
                    
                    if value is not None:
                        # Return as RESP bulk string: $<length>\r\n<string>\r\n
                        response = f"${len(value)}\r\n{value}\r\n".encode()
                        client.sendall(response)
                    else:
                        # Key doesn't exist or has expired, return null bulk string
                        client.sendall(b"$-1\r\n")
                else:
                    # Wrong number of arguments
                    client.sendall(b"-ERR wrong number of arguments for 'get' command\r\n")
            else:
                # Unknown command
                client.sendall(f"-ERR unknown command '{command.lower()}'\r\n".encode())
                
        except Exception as e:
            # print(f"Error parsing command: {e}")
            client.sendall(b"-ERR protocol error\r\n")


def main():
    server_socket = socket.create_server(("localhost", 6379))
    while True:
        client_socket, client_addr = server_socket.accept()
        threading.Thread(target=handle_command, args=(client_socket,)).start()
    

if __name__ == "__main__":
    main()