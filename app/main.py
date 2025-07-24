import socket  # noqa: F401
import threading
import time
import sys
import os
import struct

BUF_SIZE = 4096

# Global data store for key-value pairs and expiration times
data_store = {}
expiry_store = {}  # key -> expiration timestamp in seconds
data_store_lock = threading.Lock()

# Configuration parameters
config = {
    'dir': '/tmp/redis-data',
    'dbfilename': 'dump.rdb',
    'port': 6379
}


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


def read_size_encoding(data, offset):
    """Read size-encoded value from RDB data."""
    if offset >= len(data):
        return 0, offset
    
    first_byte = data[offset]
    first_two_bits = (first_byte & 0xC0) >> 6  # Get first 2 bits
    
    if first_two_bits == 0b00:  # 00: size is remaining 6 bits
        size = first_byte & 0x3F
        return size, offset + 1
    elif first_two_bits == 0b01:  # 01: size is next 14 bits (big-endian)
        if offset + 1 >= len(data):
            return 0, offset + 1
        size = ((first_byte & 0x3F) << 8) | data[offset + 1]
        return size, offset + 2
    elif first_two_bits == 0b10:  # 10: size is next 4 bytes (big-endian)
        if offset + 4 >= len(data):
            return 0, offset + 4
        size = struct.unpack('>I', data[offset + 1:offset + 5])[0]
        return size, offset + 5
    else:  # 11: special string encoding
        return first_byte, offset + 1


def read_string_encoding(data, offset):
    """Read string-encoded value from RDB data."""
    size_info, new_offset = read_size_encoding(data, offset)
    
    # Check if it's a special string encoding (first 2 bits are 11)
    if isinstance(size_info, int) and (size_info & 0xC0) == 0xC0:
        encoding_type = size_info & 0x3F
        
        if encoding_type == 0:  # 8-bit integer
            if new_offset >= len(data):
                return "", new_offset
            value = str(struct.unpack('b', data[new_offset:new_offset + 1])[0])
            return value, new_offset + 1
        elif encoding_type == 1:  # 16-bit integer (little-endian)
            if new_offset + 1 >= len(data):
                return "", new_offset + 2
            value = str(struct.unpack('<h', data[new_offset:new_offset + 2])[0])
            return value, new_offset + 2
        elif encoding_type == 2:  # 32-bit integer (little-endian)
            if new_offset + 3 >= len(data):
                return "", new_offset + 4
            value = str(struct.unpack('<i', data[new_offset:new_offset + 4])[0])
            return value, new_offset + 4
        else:
            # Unsupported encoding, skip
            return "", new_offset
    else:
        # Regular string: size followed by string data
        string_length = size_info
        if new_offset + string_length > len(data):
            return "", new_offset + string_length
        
        try:
            string_value = data[new_offset:new_offset + string_length].decode('utf-8')
            return string_value, new_offset + string_length
        except UnicodeDecodeError:
            # If decode fails, return empty string
            return "", new_offset + string_length


def parse_rdb_file(file_path):
    """Parse RDB file and load keys into data store."""
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
    except (FileNotFoundError, IOError):
        # File doesn't exist or can't be read, treat database as empty
        return
    
    if len(data) < 9:
        # File too short to contain header
        return
    
    offset = 0
    
    # Check header: should be "REDIS0011"
    header = data[offset:offset + 9]
    if not header.startswith(b'REDIS'):
        return
    offset += 9
    
    # Skip metadata and auxiliary sections
    while offset < len(data):
        if offset >= len(data):
            break
            
        opcode = data[offset]
        offset += 1
        
        if opcode == 0xFF:  # End of file
            break
        elif opcode == 0xFE:  # Database selector
            # Read database index (size encoded)
            db_index, offset = read_size_encoding(data, offset)
            # We only care about database 0
        elif opcode == 0xFB:  # Hash table sizes
            # Read hash table size info
            total_keys, offset = read_size_encoding(data, offset)
            expires_keys, offset = read_size_encoding(data, offset)
        elif opcode == 0xFA:  # Metadata
            # Skip metadata key-value pair
            key, offset = read_string_encoding(data, offset)
            value, offset = read_string_encoding(data, offset)
        elif opcode == 0xFC:  # Expire time in milliseconds
            if offset + 7 >= len(data):
                break
            # Read 8-byte timestamp (little-endian)
            timestamp_ms = struct.unpack('<Q', data[offset:offset + 8])[0]
            offset += 8
            expire_time = timestamp_ms / 1000.0  # Convert to seconds
            
            # Read value type
            if offset >= len(data):
                break
            value_type = data[offset]
            offset += 1
            
            # Read key
            key, offset = read_string_encoding(data, offset)
            
            # Read value (assuming string for now)
            if value_type == 0:  # String type
                value, offset = read_string_encoding(data, offset)
                with data_store_lock:
                    data_store[key] = value
                    expiry_store[key] = expire_time
        elif opcode == 0xFD:  # Expire time in seconds
            if offset + 3 >= len(data):
                break
            # Read 4-byte timestamp (little-endian)
            timestamp_s = struct.unpack('<I', data[offset:offset + 4])[0]
            offset += 4
            
            # Read value type
            if offset >= len(data):
                break
            value_type = data[offset]
            offset += 1
            
            # Read key
            key, offset = read_string_encoding(data, offset)
            
            # Read value (assuming string for now)
            if value_type == 0:  # String type
                value, offset = read_string_encoding(data, offset)
                with data_store_lock:
                    data_store[key] = value
                    expiry_store[key] = float(timestamp_s)
        elif opcode == 0x00:  # String value type (no expiry)
            # Read key
            key, offset = read_string_encoding(data, offset)
            
            # Read value
            value, offset = read_string_encoding(data, offset)
            
            with data_store_lock:
                data_store[key] = value
        else:
            # Unknown opcode, try to skip
            break


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
            elif command == "CONFIG":
                if len(command_parts) >= 3 and command_parts[1].upper() == "GET":
                    param_name = command_parts[2].lower()
                    if param_name in config:
                        param_value = config[param_name]
                        # Return as RESP array with 2 elements: [param_name, param_value]
                        response = f"*2\r\n${len(param_name)}\r\n{param_name}\r\n${len(param_value)}\r\n{param_value}\r\n".encode()
                        client.sendall(response)
                    else:
                        # Unknown configuration parameter
                        client.sendall(b"*0\r\n")  # Empty array for unknown config
                else:
                    # Wrong subcommand or arguments
                    client.sendall(b"-ERR wrong number of arguments for 'config' command\r\n")
            elif command == "KEYS":
                if len(command_parts) >= 2:
                    pattern = command_parts[1]
                    
                    # Get all keys (for now, only support "*" pattern)
                    with data_store_lock:
                        # Clean up expired keys first
                        expired_keys = []
                        current_time = time.time()
                        for key, expire_time in expiry_store.items():
                            if current_time > expire_time:
                                expired_keys.append(key)
                        
                        for key in expired_keys:
                            cleanup_expired_key(key)
                        
                        # Get remaining keys
                        if pattern == "*":
                            keys = list(data_store.keys())
                        else:
                            # For now, only support "*" pattern
                            keys = list(data_store.keys())
                    
                    # Return as RESP array
                    response = f"*{len(keys)}\r\n"
                    for key in keys:
                        response += f"${len(key)}\r\n{key}\r\n"
                    
                    client.sendall(response.encode())
                else:
                    # Wrong number of arguments
                    client.sendall(b"-ERR wrong number of arguments for 'keys' command\r\n")
            elif command == "INFO":
                if len(command_parts) >= 2:
                    section = command_parts[1].lower()
                    if section == "replication":
                        # Return replication info as bulk string
                        info_content = "role:master"
                        response = f"${len(info_content)}\r\n{info_content}\r\n"
                        client.sendall(response.encode())
                    else:
                        # Unsupported section, return empty bulk string
                        client.sendall(b"$0\r\n\r\n")
                else:
                    # No section specified, return all sections (for now just replication)
                    info_content = "role:master"
                    response = f"${len(info_content)}\r\n{info_content}\r\n"
                    client.sendall(response.encode())
            else:
                # Unknown command
                client.sendall(f"-ERR unknown command '{command.lower()}'\r\n".encode())
                
        except Exception as e:
            # print(f"Error parsing command: {e}")
            client.sendall(b"-ERR protocol error\r\n")


def parse_arguments():
    """Parse command line arguments for dir, dbfilename, and port."""
    args = sys.argv[1:]  # Skip the script name
    i = 0
    while i < len(args):
        if args[i] == '--dir' and i + 1 < len(args):
            config['dir'] = args[i + 1]
            i += 2
        elif args[i] == '--dbfilename' and i + 1 < len(args):
            config['dbfilename'] = args[i + 1]
            i += 2
        elif args[i] == '--port' and i + 1 < len(args):
            try:
                config['port'] = int(args[i + 1])
            except ValueError:
                print(f"Error: Invalid port number '{args[i + 1]}'")
                sys.exit(1)
            i += 2
        else:
            i += 1


def main():
    parse_arguments()
    
    # Load RDB file if it exists
    rdb_path = os.path.join(config['dir'], config['dbfilename'])
    parse_rdb_file(rdb_path)
    
    port = config['port']
    print(f"Starting Redis server on port {port}...")
    server_socket = socket.create_server(("localhost", port))
    while True:
        client_socket, client_addr = server_socket.accept()
        threading.Thread(target=handle_command, args=(client_socket,)).start()
    

if __name__ == "__main__":
    main()