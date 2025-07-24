#!/usr/bin/env python3
"""
Test script to verify master_replid and master_repl_offset in INFO command.
"""

import socket
import subprocess
import time
import sys
import os

# Add parent directory to path to import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_info_replication_master_details():
    """Test INFO replication command with master_replid and master_repl_offset"""
    print("Testing INFO replication with master details...")
    
    # Start server in master mode
    process = subprocess.Popen([
        sys.executable, "../app/main.py", "--port", "6383"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(1)  # Give server time to start
    
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("localhost", 6383))
        
        # Send INFO replication command
        command = "*2\r\n$4\r\nINFO\r\n$11\r\nreplication\r\n"
        client.sendall(command.encode())
        
        # Read response
        response = client.recv(1024)
        client.close()
        
        print(f"Raw response: {repr(response)}")
        response_str = response.decode()
        print(f"Decoded response: {response_str}")
        
        # Parse the bulk string response
        if response_str.startswith("$"):
            lines = response_str.split("\r\n")
            if len(lines) >= 2:
                length = int(lines[0][1:])  # Remove $ and convert to int
                # The content is everything after the length line, joined back
                content = "\r\n".join(lines[1:len(lines)-1])  # Exclude the last empty line
                
                print(f"Content length: {length}")
                print(f"Content: '{content}'")
                
                # Check if all required fields are present
                required_fields = ["role:master", "master_replid:", "master_repl_offset:0"]
                all_present = all(field in content for field in required_fields)
                
                if all_present:
                    print("✓ All required fields found:")
                    
                    # Extract and validate specific values
                    content_lines = content.split('\r\n')
                    for line in content_lines:
                        if line.startswith('role:'):
                            role = line.split(':', 1)[1]
                            print(f"  - Role: {role}")
                        elif line.startswith('master_replid:'):
                            replid = line.split(':', 1)[1]
                            print(f"  - Master Replication ID: {replid}")
                            if len(replid) == 40:
                                print(f"    ✓ Replication ID length is correct (40 chars)")
                            else:
                                print(f"    ✗ Replication ID length is {len(replid)}, expected 40")
                        elif line.startswith('master_repl_offset:'):
                            offset = line.split(':', 1)[1]
                            print(f"  - Master Replication Offset: {offset}")
                    
                    print("✅ Master INFO replication test PASSED!")
                    return True
                else:
                    print(f"❌ Missing required fields in response: {content}")
                    return False
            else:
                print(f"❌ Invalid response format: {response_str}")
                return False
        else:
            print(f"❌ Expected bulk string response, got: {response_str}")
            return False
            
    except Exception as e:
        print(f"❌ Error in test: {e}")
        return False
    finally:
        process.terminate()
        process.wait()

def test_info_replication_slave_mode():
    """Test INFO replication command in slave mode (should still work)"""
    print("\nTesting INFO replication in slave mode...")
    
    # Start server in slave mode
    process = subprocess.Popen([
        sys.executable, "../app/main.py", "--port", "6384", "--replicaof", "localhost 6379"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(1)  # Give server time to start
    
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("localhost", 6384))
        
        # Send INFO replication command
        command = "*2\r\n$4\r\nINFO\r\n$11\r\nreplication\r\n"
        client.sendall(command.encode())
        
        # Read response
        response = client.recv(1024)
        client.close()
        
        print(f"Raw response: {repr(response)}")
        response_str = response.decode()
        print(f"Decoded response: {response_str}")
        
        # For slave mode, should still contain role:slave
        if "role:slave" in response_str:
            print("✅ Slave INFO replication test PASSED!")
            return True
        else:
            print(f"❌ Expected role:slave in response: {response_str}")
            return False
            
    except Exception as e:
        print(f"❌ Error in slave test: {e}")
        return False
    finally:
        process.terminate()
        process.wait()

def test_info_without_section():
    """Test INFO command without section argument (should include replication info)"""
    print("\nTesting INFO without section...")
    
    # Start server in master mode
    process = subprocess.Popen([
        sys.executable, "../app/main.py", "--port", "6385"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(1)  # Give server time to start
    
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("localhost", 6385))
        
        # Send INFO command without section
        command = "*1\r\n$4\r\nINFO\r\n"
        client.sendall(command.encode())
        
        # Read response
        response = client.recv(1024)
        client.close()
        
        print(f"Raw response: {repr(response)}")
        response_str = response.decode()
        print(f"Decoded response: {response_str}")
        
        # Should contain master replication info
        if "role:master" in response_str and "master_replid:" in response_str and "master_repl_offset:" in response_str:
            print("✅ INFO without section test PASSED!")
            return True
        else:
            print(f"❌ Missing master replication info in response: {response_str}")
            return False
            
    except Exception as e:
        print(f"❌ Error in no section test: {e}")
        return False
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    print("🧪 Testing INFO command with master replication details")
    print("=" * 60)
    
    passed = 0
    total = 3
    
    if test_info_replication_master_details():
        passed += 1
    if test_info_replication_slave_mode():
        passed += 1
    if test_info_without_section():
        passed += 1
        
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All master replication INFO tests PASSED!")
        sys.exit(0)
    else:
        print("❌ Some master replication INFO tests FAILED!")
        sys.exit(1)
