#!/usr/bin/env python3

"""
Test script to verify ACK handling with proper offset tracking.
This script simulates a master server to test the replica's ACK functionality.
"""

import socket
import time
import threading

def create_fake_master():
    """Create a fake master server for testing ACK functionality."""
    
    # Create server socket
    master_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    master_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    master_socket.bind(('localhost', 6379))
    master_socket.listen(1)
    
    print("🔧 Fake master server listening on port 6379...")
    
    try:
        # Accept connection from replica
        replica_conn, replica_addr = master_socket.accept()
        print(f"✅ Replica connected from {replica_addr}")
        
        # Handle replica handshake
        handle_replica_handshake(replica_conn)
        
        # Test ACK functionality
        test_ack_tracking(replica_conn)
        
    except Exception as e:
        print(f"❌ Error in fake master: {e}")
    finally:
        master_socket.close()

def handle_replica_handshake(replica_conn):
    """Handle the replication handshake with replica."""
    print("\n🤝 Starting replication handshake...")
    
    # Step 1: Expect PING from replica
    data = replica_conn.recv(1024)
    print(f"📩 Received: {data}")
    if b"PING" in data:
        replica_conn.sendall(b"+PONG\r\n")
        print("📤 Sent: +PONG")
    
    # Step 2: Expect REPLCONF listening-port
    data = replica_conn.recv(1024)
    print(f"📩 Received: {data}")
    if b"REPLCONF" in data and b"listening-port" in data:
        replica_conn.sendall(b"+OK\r\n")
        print("📤 Sent: +OK")
    
    # Step 3: Expect REPLCONF capa
    data = replica_conn.recv(1024)
    print(f"📩 Received: {data}")
    if b"REPLCONF" in data and b"capa" in data:
        replica_conn.sendall(b"+OK\r\n")
        print("📤 Sent: +OK")
    
    # Step 4: Expect PSYNC
    data = replica_conn.recv(1024)
    print(f"📩 Received: {data}")
    if b"PSYNC" in data:
        # Send FULLRESYNC
        fullresync_response = b"+FULLRESYNC 8371b4fb1155b71f4a04d3e1bc3e18c4a990aeeb 0\r\n"
        replica_conn.sendall(fullresync_response)
        print("📤 Sent: +FULLRESYNC...")
        
        # Send empty RDB file
        empty_rdb = b'REDIS0011\xfa\x09redis-ver\x057.2.0\xfa\x0aredis-bits\xc0@\xfe\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00'
        rdb_response = f"${len(empty_rdb)}\r\n".encode() + empty_rdb
        replica_conn.sendall(rdb_response)
        print(f"📤 Sent RDB file ({len(empty_rdb)} bytes)")
    
    print("✅ Handshake completed!\n")

def test_ack_tracking(replica_conn):
    """Test ACK tracking with various commands."""
    print("🧪 Testing ACK functionality...\n")
    
    # Test 1: Initial GETACK (should be 0)
    print("Test 1: Initial GETACK")
    getack_cmd = b"*3\r\n$8\r\nREPLCONF\r\n$6\r\nGETACK\r\n$1\r\n*\r\n"
    replica_conn.sendall(getack_cmd)
    print(f"📤 Sent GETACK: {getack_cmd}")
    
    response = replica_conn.recv(1024)
    print(f"📩 Received ACK: {response}")
    
    if b"REPLCONF" in response and b"ACK" in response and b"0" in response:
        print("✅ Test 1 passed: Initial offset is 0\n")
    else:
        print("❌ Test 1 failed: Expected ACK 0\n")
        return
    
    time.sleep(0.1)
    
    # Test 2: Send PING command and check offset
    print("Test 2: PING command tracking")
    ping_cmd = b"*1\r\n$4\r\nPING\r\n"
    replica_conn.sendall(ping_cmd)
    print(f"📤 Sent PING: {ping_cmd} ({len(ping_cmd)} bytes)")
    
    time.sleep(0.1)
    
    # Send GETACK to check offset
    replica_conn.sendall(getack_cmd)
    print("📤 Sent GETACK")
    
    response = replica_conn.recv(1024)
    print(f"📩 Received ACK: {response}")
    
    # Should be 14 bytes (length of PING command)
    if b"14" in response:
        print("✅ Test 2 passed: Offset correctly updated after PING (14 bytes)\n")
    else:
        print(f"❌ Test 2 failed: Expected ACK 14, got {response}\n")
    
    time.sleep(0.1)
    
    # Test 3: Send SET command and check cumulative offset
    print("Test 3: SET command tracking")
    set_cmd = b"*3\r\n$3\r\nSET\r\n$3\r\nfoo\r\n$3\r\nbar\r\n"
    replica_conn.sendall(set_cmd)
    print(f"📤 Sent SET: {set_cmd} ({len(set_cmd)} bytes)")
    
    time.sleep(0.1)
    
    # Send GETACK to check cumulative offset
    replica_conn.sendall(getack_cmd)
    print("📤 Sent GETACK")
    
    response = replica_conn.recv(1024)
    print(f"📩 Received ACK: {response}")
    
    # Should be 14 + 29 = 43 bytes total
    expected_offset = 14 + len(set_cmd)  # 14 (PING) + 29 (SET) = 43
    if str(expected_offset).encode() in response:
        print(f"✅ Test 3 passed: Offset correctly updated after SET ({expected_offset} bytes total)\n")
    else:
        print(f"❌ Test 3 failed: Expected ACK {expected_offset}, got {response}\n")
    
    print("🎉 ACK testing completed!")

def main():
    """Main test function."""
    print("🚀 Starting ACK handling test...\n")
    
    # Start fake master in a separate thread
    master_thread = threading.Thread(target=create_fake_master, daemon=True)
    master_thread.start()
    
    # Give master time to start
    time.sleep(0.5)
    
    # Wait for master thread to complete
    master_thread.join(timeout=30)
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    main()
