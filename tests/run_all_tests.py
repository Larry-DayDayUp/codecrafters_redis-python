#!/usr/bin/env python3
"""
Redis Server Test Suite - Main Runner
Run all tests for the Redis server implementation.

Usage: python run_all_tests.py
"""

import sys
import os
import subprocess
import time

# Add parent directory to path to import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_basic import test_ping, test_echo, test_concurrent_clients
from test_storage import test_set_get
from test_expiry import test_expiry
from test_config import test_config_get, test_basic_commands

def run_all_tests():
    """Run all Redis server tests."""
    print("🚀 Redis Server Comprehensive Test Suite")
    print("=" * 50)
    
    try:
        # Test 1: Basic Commands (PING, ECHO, Concurrency)
        print("\n📋 TEST 1: Basic Commands")
        print("-" * 25)
        test_ping()
        print()
        test_echo()
        print()
        test_concurrent_clients()
        
        # Test 2: Storage Commands (SET, GET)
        print("\n📋 TEST 2: Storage Commands")
        print("-" * 27)
        test_set_get()
        
        # Test 3: Key Expiration
        print("\n📋 TEST 3: Key Expiration")
        print("-" * 25)
        test_expiry()
        
        # Test 4: Configuration
        print("\n📋 TEST 4: Configuration")
        print("-" * 24)
        test_config_get()
        
        # Test 5: RDB Loading
        print("\n📋 TEST 5: RDB Loading")
        print("-" * 22)
        print("Running RDB test...")
        result = subprocess.run([sys.executable, "test_rdb.py"], 
                              capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if result.returncode == 0:
            print("✓ RDB test passed")
        else:
            print("❌ RDB test failed")
            print(f"Error: {result.stderr}")
            raise Exception("RDB test failed")
        
        # Test 6: Port Configuration
        print("\n📋 TEST 6: Port Configuration")
        print("-" * 30)
        print("Running port configuration test...")
        result = subprocess.run([sys.executable, "test_port_config.py"], 
                              capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if result.returncode == 0:
            print("✓ Port configuration test passed")
        else:
            print("❌ Port configuration test failed")
            print(f"Error: {result.stderr}")
            raise Exception("Port configuration test failed")
        
        # Test 7: INFO Command
        print("\n📋 TEST 7: INFO Command")
        print("-" * 24)
        print("Running INFO command test...")
        result = subprocess.run([sys.executable, "test_info_command.py"], 
                              capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if result.returncode == 0:
            print("✓ INFO command test passed")
        else:
            print("❌ INFO command test failed")
            print(f"Error: {result.stderr}")
            raise Exception("INFO command test failed")
        
        # Test 8: Replicaof Flag
        print("\n📋 TEST 8: Replicaof Flag")
        print("-" * 26)
        print("Running replicaof flag test...")
        result = subprocess.run([sys.executable, "test_replicaof.py"], 
                              capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if result.returncode == 0:
            print("✓ Replicaof flag test passed")
        else:
            print("❌ Replicaof flag test failed")
            print(f"Error: {result.stderr}")
            raise Exception("Replicaof flag test failed")
        
        # Test 9: RESP Format Validation
        print("\n📋 TEST 9: RESP Format Validation")
        print("-" * 34)
        print("Running RESP format validation test...")
        result = subprocess.run([sys.executable, "test_resp_format.py"], 
                              capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if result.returncode == 0:
            print("✓ RESP format validation test passed")
        else:
            print("❌ RESP format validation test failed")
            print(f"Error: {result.stderr}")
            raise Exception("RESP format validation test failed")
        
        # Summary
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print("✅ Redis server is working correctly!")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)

def check_server_connection():
    """Check if Redis server is running before starting tests."""
    import socket
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(1)
        client.connect(('localhost', 6379))
        client.close()
        return True
    except:
        return False

if __name__ == "__main__":
    # Start server if not running
    server_process = None
    if not check_server_connection():
        print("Starting Redis server...")
        server_process = subprocess.Popen(
            ["python", "app/main.py"],
            cwd="c:\\Users\\33233\\Desktop\\CodeCrafter\\codecrafters-redis-python",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(2)  # Give server time to start
        
        if not check_server_connection():
            print("❌ Failed to start Redis server")
            if server_process:
                server_process.terminate()
            sys.exit(1)
    
    try:
        print("✅ Server connection verified!")
        run_all_tests()
    finally:
        # Clean up server if we started it
        if server_process:
            server_process.terminate()
            server_process.wait()
