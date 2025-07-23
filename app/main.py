import socket  # noqa: F401
import threading

BUF_SIZE = 4096


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