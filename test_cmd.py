#!/usr/bin/env python3
import socket

def test_info_command():
    """Test INFO command using socket connection"""
    try:
        s = socket.socket()
        s.connect(('localhost', 6379))
        
        # Send INFO command in RESP format
        s.send(b'*1\r\n$4\r\nINFO\r\n')
        
        # Receive response
        response = s.recv(1024)
        print("Raw response:", repr(response))
        print("Decoded response:", response.decode())
        
        s.close()
        print("Test completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_info_command()
