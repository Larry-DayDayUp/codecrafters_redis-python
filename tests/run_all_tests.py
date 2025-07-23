#!/usr/bin/env python3
"""
Redis Server Test Suite - Main Runner
Run all tests for the Redis server implementation.

Usage: python run_all_tests.py
"""

import sys
import os

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
    print("Checking Redis server connection...")
    if not check_server_connection():
        print("❌ Error: Redis server is not running on localhost:6379")
        print("Please start the server first with:")
        print("python app/main.py")
        sys.exit(1)
    
    print("✅ Server connection verified!")
    run_all_tests()
