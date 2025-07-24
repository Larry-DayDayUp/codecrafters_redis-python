#!/usr/bin/env python3
"""Quick manual test for INFO command"""

import socket

def test_info_manual():
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("localhost", 6390))
        
        # Send INFO replication command
        client.sendall(b"*2\r\n$4\r\nINFO\r\n$11\r\nreplication\r\n")
        response = client.recv(1024)
        client.close()
        
        print(f"Raw response: {repr(response)}")
        print(f"Decoded: {response.decode()}")
        
        # Test if it contains all required fields
        response_str = response.decode()
        if "role:master" in response_str and "master_replid:" in response_str and "master_repl_offset:" in response_str:
            print("✅ All required fields present!")
            return True
        else:
            print("❌ Missing required fields")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_info_manual()
