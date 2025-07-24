"""
Manual test to verify exact response format for INFO command
"""
import socket
import subprocess
import time
import sys

def manual_test_info():
    """Manual test with exact output verification"""
    print("Manual INFO command test...")
    
    port = 6394
    process = subprocess.Popen(
        [sys.executable, "app/main.py", "--port", str(port)]
    )
    
    time.sleep(1)
    
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("localhost", port))
        
        # Send exactly what CodeCrafters will send
        print("Sending: INFO replication")
        client.send(b"*2\r\n$4\r\nINFO\r\n$11\r\nreplication\r\n")
        
        response = client.recv(1024)
        print(f"Raw response bytes: {response}")
        print(f"Response as string: {repr(response.decode())}")
        
        # Verify it's the expected format: $11\r\nrole:master\r\n
        expected = b"$11\r\nrole:master\r\n"
        if response == expected:
            print("✅ Response matches expected format exactly!")
        else:
            print(f"❌ Response doesn't match!")
            print(f"Expected: {expected}")
            print(f"Got:      {response}")
        
        # Also test with redis-cli format to see what it should look like
        print("\nResponse breakdown:")
        print(f"- Bulk string indicator: '{response[0:1]}'")
        print(f"- Length: '{response[1:3]}'")
        print(f"- CRLF: '{response[3:5]}'")
        print(f"- Content: '{response[5:16]}'")
        print(f"- Final CRLF: '{response[16:18]}'")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()
        process.terminate()
        process.wait()

if __name__ == "__main__":
    manual_test_info()
