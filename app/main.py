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

# Replication state
replicas = []  # List of connected replica sockets
replicas_lock = threading.Lock()
pending_acks = {}  # offset -> list of replica sockets waiting for ACK
pending_acks_lock = threading.Lock()

# Configuration parameters
config = {
    'dir': '/tmp/redis-data',
    'dbfilename': 'dump.rdb',
    'port': 6379,
    'replicaof': None,  # None for master, (host, port) tuple for replica
    'master_replid': '8371b4fb1155b71f4a04d3e1bc3e18c4a990aeeb',  # 40 char replication ID
    'master_repl_offset': 0  # Replication offset, starts at 0
}


def create_empty_rdb():
    """Create an empty RDB file content."""
    # Empty RDB file: REDIS header + version + EOF
    # This is a minimal valid RDB file with no data
    rdb_content = b'REDIS0011'  # Header with version
    rdb_content += b'\xfa'  # Auxiliary field marker
    rdb_content += b'\x09redis-ver\x05'  # redis-ver key
    rdb_content += b'7.2.0'  # version value
    rdb_content += b'\xfa'  # Auxiliary field marker  
    rdb_content += b'\x0aredis-bits\xc0@'  # redis-bits 64
    rdb_content += b'\xfe\x00'  # Database selector DB 0
    rdb_content += b'\xff'  # EOF marker
    # Add checksum (8 bytes) - using zeros for simplicity
    rdb_content += b'\x00\x00\x00\x00\x00\x00\x00\x00'
    return rdb_content


def add_replica(client_socket):
    """Add a replica socket to the list of connected replicas."""
    with replicas_lock:
        replicas.append(client_socket)
        print(f"Added replica. Total replicas: {len(replicas)}")


def handle_replica(client):
    """Handle commands from a replica connection."""
    try:
        while True:
            # Receive data from replica
            data = client.recv(1024)
            if not data:
                break
            
            # Parse the command
            command_parts = parse_resp(data)
            if not command_parts:
                continue
                
            command = command_parts[0].upper()
            
            if command == "REPLCONF" and len(command_parts) >= 3:
                subcommand = command_parts[1].upper()
                if subcommand == "ACK":
                    # Handle ACK response from replica
                    offset = int(command_parts[2])
                    
                    # Process this ACK for any pending WAIT commands
                    with pending_acks_lock:
                        for pending_offset in list(pending_acks.keys()):
                            waiting_list = pending_acks[pending_offset]
                            if client in waiting_list:
                                # Remove this replica from waiting list
                                waiting_list.remove(client)
                                break
                # We don't need to respond to ACK commands
                    
    except Exception as e:
        print(f"Error handling replica: {e}")
    finally:
        # Remove from replicas list when disconnected
        with replicas_lock:
            if client in replicas:
                replicas.remove(client)
                print(f"Removed replica. Total replicas: {len(replicas)}")
        try:
            client.close()
        except:
            pass


def remove_replica(client_socket):
    """Remove a replica socket from the list of connected replicas."""
    with replicas_lock:
        if client_socket in replicas:
            replicas.remove(client_socket)
            print(f"Removed replica. Total replicas: {len(replicas)}")


def handle_replica_ack(client_socket, ack_offset):
    """Handle ACK from replica - update pending ACKs."""
    with pending_acks_lock:
        # Find and notify any waiting WAIT commands
        for offset, waiting_replicas in list(pending_acks.items()):
            if ack_offset >= offset and client_socket in waiting_replicas:
                waiting_replicas.remove(client_socket)
                if not waiting_replicas:
                    # All required replicas have ACKed
                    del pending_acks[offset]


def propagate_command_to_replicas(command_bytes):
    """Send a command to all connected replicas."""
    with replicas_lock:
        disconnected_replicas = []
        for replica in replicas[:]:  # Create a copy to avoid modification during iteration
            try:
                replica.sendall(command_bytes)
            except Exception as e:
                print(f"Error sending to replica: {e}")
                # Mark for removal
                disconnected_replicas.append(replica)
        
        # Remove disconnected replicas
        for replica in disconnected_replicas:
            if replica in replicas:
                replicas.remove(replica)
        
        # Update replication offset only once if we have replicas
        if replicas:
            config['master_repl_offset'] += len(command_bytes)


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


def parse_resp_with_consumed(data: bytes):
    """Parse RESP format and return both elements and consumed bytes."""
    try:
        original_data = data
        lines = data.decode().split('\r\n')
        
        if not lines[0].startswith('*'):
            return [], 0
        
        num_elements = int(lines[0][1:])
        elements = []
        line_idx = 1
        consumed_bytes = len(lines[0]) + 2  # +2 for \r\n
        
        for _ in range(num_elements):
            if line_idx >= len(lines) or not lines[line_idx].startswith('$'):
                return [], 0  # Incomplete command
                
            length = int(lines[line_idx][1:])
            consumed_bytes += len(lines[line_idx]) + 2  # +2 for \r\n
            line_idx += 1
            
            if line_idx >= len(lines):
                return [], 0  # Incomplete command
                
            if len(lines[line_idx]) != length:
                return [], 0  # Incomplete command
                
            elements.append(lines[line_idx])
            consumed_bytes += len(lines[line_idx]) + 2  # +2 for \r\n
            line_idx += 1
        
        return elements, consumed_bytes
    except (UnicodeDecodeError, ValueError, IndexError):
        return [], 0


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
    try:
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
                        
                        # Propagate command to replicas BEFORE responding to client
                        if config['replicaof'] is None:  # Only masters propagate
                            # Build proper RESP command to propagate
                            if len(command_parts) >= 5 and command_parts[3].upper() == "PX":
                                # Include PX arguments
                                resp_command = f"*5\r\n$3\r\nSET\r\n${len(key)}\r\n{key}\r\n${len(value)}\r\n{value}\r\n$2\r\nPX\r\n${len(command_parts[4])}\r\n{command_parts[4]}\r\n".encode()
                            else:
                                # Simple SET command
                                resp_command = f"*3\r\n$3\r\nSET\r\n${len(key)}\r\n{key}\r\n${len(value)}\r\n{value}\r\n".encode()
                            propagate_command_to_replicas(resp_command)
                        
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
                            role = "slave" if config['replicaof'] is not None else "master"
                            
                            # Build replication info with role, replid, and offset
                            if role == "master":
                                info_content = f"role:{role}\r\nmaster_replid:{config['master_replid']}\r\nmaster_repl_offset:{config['master_repl_offset']}"
                            else:
                                # For slave, still include role (may add more slave-specific info later)
                                info_content = f"role:{role}"
                            
                            response = f"${len(info_content)}\r\n{info_content}\r\n"
                            client.sendall(response.encode())
                        else:
                            # Unsupported section, return empty bulk string
                            client.sendall(b"$0\r\n\r\n")
                    else:
                        # No section specified, return all sections (for now just replication)
                        role = "slave" if config['replicaof'] is not None else "master"
                        
                        # Build replication info with role, replid, and offset
                        if role == "master":
                            info_content = f"role:{role}\r\nmaster_replid:{config['master_replid']}\r\nmaster_repl_offset:{config['master_repl_offset']}"
                        else:
                            # For slave, still include role (may add more slave-specific info later)
                            info_content = f"role:{role}"
                        
                        response = f"${len(info_content)}\r\n{info_content}\r\n"
                        client.sendall(response.encode())
                elif command == "REPLCONF":
                    # Handle REPLCONF command for replication configuration
                    if len(command_parts) >= 3:
                        subcommand = command_parts[1].lower()
                        if subcommand == "listening-port":
                            # Replica is notifying us of its listening port
                            port = command_parts[2]
                            # For now, just acknowledge with OK
                            client.sendall(b"+OK\r\n")
                        elif subcommand == "capa":
                            # Replica is notifying us of its capabilities
                            capability = command_parts[2]
                            # For now, just acknowledge with OK
                            client.sendall(b"+OK\r\n")
                        elif subcommand == "ack":
                            # Replica is acknowledging replication offset
                            if len(command_parts) >= 3:
                                ack_offset = int(command_parts[2])
                                # Handle ACK - this is typically used by WAIT command
                                handle_replica_ack(client, ack_offset)
                            client.sendall(b"+OK\r\n")
                        elif subcommand == "getack":
                            # Master is requesting ACK from replica
                            if config['replicaof'] is not None:  # We are a replica
                                # Send our current offset back to master
                                current_offset = config.get('replica_offset', 0)
                                offset_str = str(current_offset)
                                ack_response = "*3\r\n$8\r\nREPLCONF\r\n$3\r\nACK\r\n$" + str(len(offset_str)) + "\r\n" + offset_str + "\r\n"
                                client.sendall(ack_response.encode())
                                # GETACK command itself should increment offset after responding
                                # Calculate the byte length of the GETACK command
                                getack_bytes = len(chunk)
                                config['replica_offset'] = config.get('replica_offset', 0) + getack_bytes
                        else:
                            # Unknown REPLCONF subcommand
                            client.sendall(b"-ERR unknown REPLCONF subcommand\r\n")
                    else:
                        # Wrong number of arguments
                        client.sendall(b"-ERR wrong number of arguments for 'replconf' command\r\n")
                elif command == "PSYNC":
                    # Handle PSYNC command for replication synchronization
                    if len(command_parts) >= 3:
                        repl_id = command_parts[1]
                        offset = command_parts[2]
                        
                        # For full resynchronization (first time connecting)
                        if repl_id == "?" and offset == "-1":
                            # Send FULLRESYNC response with our replication ID and offset
                            response = f"+FULLRESYNC {config['master_replid']} {config['master_repl_offset']}\r\n"
                            client.sendall(response.encode())
                            
                            # Send empty RDB file
                            empty_rdb = create_empty_rdb()
                            rdb_response = f"${len(empty_rdb)}\r\n".encode() + empty_rdb
                            client.sendall(rdb_response)
                            
                            # Add this replica to our list for command propagation
                            add_replica(client)
                            
                            # Start handling replica-specific commands (break from main loop)
                            handle_replica(client)
                            return  # Exit this client handler
                        else:
                            # For now, only support full resync
                            client.sendall(b"-ERR partial resync not supported\r\n")
                    else:
                        # Wrong number of arguments
                        client.sendall(b"-ERR wrong number of arguments for 'psync' command\r\n")
                elif command == "WAIT":
                    # Handle WAIT command for replication synchronization
                    if len(command_parts) >= 3:
                        try:
                            num_replicas = int(command_parts[1])
                            timeout_ms = int(command_parts[2])
                            
                            # If no replicas are required, return immediately
                            if num_replicas == 0:
                                client.sendall(b":0\r\n")
                            else:
                                # Check current number of replicas
                                with replicas_lock:
                                    current_replica_count = len(replicas)
                                
                                # If we have no replicas, return 0
                                if current_replica_count == 0:
                                    client.sendall(b":0\r\n")
                                # If no commands have been sent (offset is 0), all replicas are up to date
                                elif config['master_repl_offset'] == 0:
                                    # Return the actual number of connected replicas, not limited by num_replicas
                                    acked_count = current_replica_count
                                    response = f":{acked_count}\r\n"
                                    client.sendall(response.encode())
                                else:
                                    # Send GETACK to all replicas and wait for responses
                                    getack_command = b"*3\r\n$8\r\nREPLCONF\r\n$6\r\nGETACK\r\n$1\r\n*\r\n"
                                    
                                    # Track which replicas we're waiting for
                                    current_offset = config['master_repl_offset']
                                    waiting_replicas = []
                                    
                                    with replicas_lock:
                                        # Send GETACK to ALL replicas, not limited by num_replicas
                                        for replica in replicas[:]:
                                            try:
                                                replica.sendall(getack_command)
                                                waiting_replicas.append(replica)
                                            except Exception:
                                                pass  # Skip disconnected replicas
                                    
                                    if not waiting_replicas:
                                        client.sendall(b":0\r\n")
                                    else:
                                        # Store the pending ACK request
                                        with pending_acks_lock:
                                            pending_acks[current_offset] = waiting_replicas[:]
                                        
                                        # Wait for ACKs with timeout
                                        start_time = time.time()
                                        timeout_seconds = timeout_ms / 1000.0
                                        
                                        while time.time() - start_time < timeout_seconds:
                                            with pending_acks_lock:
                                                remaining = pending_acks.get(current_offset, [])
                                                acked_count = len(waiting_replicas) - len(remaining)
                                                
                                                # Break if we have enough ACKs or all replicas have responded
                                                if acked_count >= num_replicas or not remaining:
                                                    break
                                            time.sleep(0.001)  # Small sleep to avoid busy waiting
                                        
                                        # Calculate final acked count
                                        with pending_acks_lock:
                                            remaining = pending_acks.get(current_offset, [])
                                            acked_count = len(waiting_replicas) - len(remaining)
                                            if current_offset in pending_acks:
                                                del pending_acks[current_offset]
                                        
                                        response = f":{acked_count}\r\n"
                                        client.sendall(response.encode())
                        except ValueError:
                            client.sendall(b"-ERR invalid number format\r\n")
                    else:
                        # Wrong number of arguments
                        client.sendall(b"-ERR wrong number of arguments for 'wait' command\r\n")
                else:
                    # Unknown command
                    client.sendall(f"-ERR unknown command '{command.lower()}'\r\n".encode())
                    
            except Exception as e:
                # print(f"Error parsing command: {e}")
                client.sendall(b"-ERR protocol error\r\n")
    except ConnectionResetError:
        # Client disconnected
        remove_replica(client)
    except Exception as e:
        print(f"Error in handle_command: {e}")
    finally:
        # Always remove from replicas list when connection closes
        remove_replica(client)


def parse_arguments():
    """Parse command line arguments for dir, dbfilename, port, and replicaof."""
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
        elif args[i] == '--replicaof' and i + 1 < len(args):
            # Parse replicaof argument: "host port"
            replicaof_arg = args[i + 1]
            try:
                host, port_str = replicaof_arg.split(' ', 1)
                port = int(port_str)
                config['replicaof'] = (host, port)
            except (ValueError, IndexError):
                print(f"Error: Invalid replicaof argument '{replicaof_arg}'. Expected format: 'host port'")
                sys.exit(1)
            i += 2
        else:
            i += 1


def connect_to_master():
    """Connect to master server and perform handshake if this is a replica."""
    if config['replicaof'] is None:
        return  # Not a replica, nothing to do
    
    master_host, master_port = config['replicaof']
    
    try:
        # Connect to master
        master_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        master_socket.connect((master_host, master_port))
        print(f"Connected to master at {master_host}:{master_port}")
        
        # Step 1: Send PING command
        ping_command = b"*1\r\n$4\r\nPING\r\n"
        master_socket.send(ping_command)
        response = master_socket.recv(1024)
        print(f"PING response: {response}")
        
        # Step 2: Send REPLCONF listening-port <PORT>
        port_str = str(config['port'])
        replconf_port_command = f"*3\r\n$8\r\nREPLCONF\r\n$14\r\nlistening-port\r\n${len(port_str)}\r\n{port_str}\r\n".encode()
        master_socket.send(replconf_port_command)
        response = master_socket.recv(1024)
        print(f"REPLCONF listening-port response: {response}")
        
        # Step 3: Send REPLCONF capa psync2
        replconf_capa_command = b"*3\r\n$8\r\nREPLCONF\r\n$4\r\ncapa\r\n$6\r\npsync2\r\n"
        master_socket.send(replconf_capa_command)
        response = master_socket.recv(1024)
        print(f"REPLCONF capa response: {response}")
        
        # Step 4: Send PSYNC ? -1
        psync_command = b"*3\r\n$5\r\nPSYNC\r\n$1\r\n?\r\n$2\r\n-1\r\n"
        master_socket.send(psync_command)
        response = master_socket.recv(4096)  # Larger buffer for RDB data
        print(f"PSYNC response: {response[:100]}...")  # Only show first 100 bytes
        
        # Initialize replica offset
        config['replica_offset'] = 0
        
        # Start listening for commands from master
        threading.Thread(target=handle_master_commands, args=(master_socket,), daemon=True).start()
        
    except Exception as e:
        print(f"Error connecting to master: {e}")


def handle_master_commands(master_socket):
    """Handle commands received from master server."""
    # Process commands and track offset properly
    buffer = b""
    rdb_received = False
    
    try:
        while True:
            data = master_socket.recv(4096)
            if not data:
                break
            
            buffer += data
            
            # First, handle RDB file if not yet received
            if not rdb_received:
                # Check if buffer starts with RDB bulk string format
                if buffer.startswith(b'$'):
                    # Find the end of the length specification
                    try:
                        crlf_pos = buffer.find(b'\r\n')
                        if crlf_pos == -1:
                            continue  # Need more data for length
                        
                        rdb_length = int(buffer[1:crlf_pos])
                        total_rdb_size = crlf_pos + 2 + rdb_length  # $len\r\n + data
                        
                        if len(buffer) >= total_rdb_size:
                            # We have the complete RDB file, skip it
                            buffer = buffer[total_rdb_size:]  # Remove RDB data from buffer
                            rdb_received = True
                        else:
                            continue  # Need more data for complete RDB
                    except ValueError:
                        print("Error parsing RDB length")
                        break
                else:
                    # No RDB file expected, mark as received
                    rdb_received = True
            
            # Process all complete commands in the buffer
            while buffer and rdb_received:
                # Try to parse one command from buffer
                try:
                    command_parts, consumed_bytes = parse_resp_with_consumed(buffer)
                    if not command_parts or consumed_bytes == 0:
                        break  # Need more data
                    
                    # Remove consumed bytes from buffer
                    buffer = buffer[consumed_bytes:]
                    
                    # Process the command
                    command = command_parts[0].upper()
                    
                    if command == "REPLCONF":
                        if len(command_parts) >= 2 and command_parts[1].upper() == "GETACK":
                            # Master is requesting ACK - send our current offset
                            current_offset = config.get('replica_offset', 0)
                            offset_str = str(current_offset)
                            ack_response = "*3\r\n$8\r\nREPLCONF\r\n$3\r\nACK\r\n$" + str(len(offset_str)) + "\r\n" + offset_str + "\r\n"
                            try:
                                master_socket.sendall(ack_response.encode())
                                # GETACK command itself DOES count towards offset for future commands
                                config['replica_offset'] += consumed_bytes
                            except Exception as e:
                                print(f"Error sending ACK: {e}")
                                break
                        else:
                            # Other REPLCONF commands (not GETACK) should increment offset
                            config['replica_offset'] += consumed_bytes
                    elif command == "PING":
                        # Handle PING command from master (keepalive)
                        # No response needed, just update offset
                        config['replica_offset'] += consumed_bytes
                    elif command == "SET":
                        # Execute SET command from master
                        if len(command_parts) >= 3:
                            key = command_parts[1]
                            value = command_parts[2]
                            
                            # Handle PX argument if present
                            expiry_time = None
                            if len(command_parts) >= 5 and command_parts[3].upper() == "PX":
                                try:
                                    expiry_ms = int(command_parts[4])
                                    expiry_time = time.time() + (expiry_ms / 1000.0)
                                except ValueError:
                                    pass
                            
                            # Store the key-value pair (no response back to master)
                            with data_store_lock:
                                data_store[key] = value
                                if expiry_time:
                                    expiry_store[key] = expiry_time
                                elif key in expiry_store:
                                    del expiry_store[key]
                        
                        # Update replica offset with the consumed bytes
                        config['replica_offset'] += consumed_bytes
                    elif command == "GET":
                        # Process GET command (though masters usually don't send these)
                        # Just update offset, no response needed
                        config['replica_offset'] += consumed_bytes
                    elif command == "DEL":
                        # Handle DEL command from master
                        if len(command_parts) >= 2:
                            with data_store_lock:
                                for i in range(1, len(command_parts)):
                                    key = command_parts[i]
                                    if key in data_store:
                                        del data_store[key]
                                    if key in expiry_store:
                                        del expiry_store[key]
                        
                        # Update replica offset
                        config['replica_offset'] += consumed_bytes
                    elif command == "INCR":
                        # Handle INCR command from master
                        if len(command_parts) >= 2:
                            key = command_parts[1]
                            with data_store_lock:
                                try:
                                    current_value = int(data_store.get(key, "0"))
                                    data_store[key] = str(current_value + 1)
                                    # Remove expiry if key exists
                                    if key in expiry_store:
                                        del expiry_store[key]
                                except ValueError:
                                    # If current value is not a number, treat as 0
                                    data_store[key] = "1"
                                    if key in expiry_store:
                                        del expiry_store[key]
                        
                        # Update replica offset
                        config['replica_offset'] += consumed_bytes
                    else:
                        # For any other command, just update offset
                        config['replica_offset'] += consumed_bytes
                        
                except Exception as e:
                    print(f"Error parsing command from master: {e}")
                    break  # Break inner loop to get more data
                
    except Exception as e:
        print(f"Error handling master commands: {e}")
    finally:
        master_socket.close()


def main():
    parse_arguments()
    
    # Load RDB file if it exists
    rdb_path = os.path.join(config['dir'], config['dbfilename'])
    parse_rdb_file(rdb_path)
    
    # If this is a replica, connect to master and perform handshake
    if config['replicaof'] is not None:
        threading.Thread(target=connect_to_master, daemon=True).start()
    
    port = config['port']
    print(f"Starting Redis server on port {port}...")
    server_socket = socket.create_server(("localhost", port))
    while True:
        client_socket, client_addr = server_socket.accept()
        threading.Thread(target=handle_command, args=(client_socket,)).start()
    

if __name__ == "__main__":
    main()