# Test files for the Redis implementation

This folder contains test scripts to verify the functionality of the Redis server implementation.

## Test Files:

### Individual Test Modules:
- `test_basic.py` - Tests PING, ECHO commands and concurrent client connections
- `test_storage.py` - Tests SET, GET commands and key-value storage
- `test_expiry.py` - Tests key expiration with PX parameter
- `test_config.py` - Tests CONFIG GET commands for server configuration

### Main Test Runner:
- `run_all_tests.py` - Comprehensive test suite that runs all tests

## How to Run Tests:

### Run All Tests:
```bash
# Start the Redis server first
python app/main.py --dir /tmp/test-dir --dbfilename test.rdb

# In another terminal, run the complete test suite
python tests/run_all_tests.py
```

### Run Individual Tests:
```bash
# Test basic commands
python tests/test_basic.py

# Test storage functionality  
python tests/test_storage.py

# Test expiration mechanism
python tests/test_expiry.py

# Test configuration commands
python tests/test_config.py
```

## Test Coverage:

✅ **Stage #JM1**: Bind to a port  
✅ **Stage #RG2**: Respond to PING  
✅ **Stage #WY1**: Respond to multiple PINGs  
✅ **Stage #ZU2**: Handle concurrent clients  
✅ **Stage #QQ0**: Implement the ECHO command  
✅ **Stage #LA7**: Implement the SET & GET commands  
✅ **Stage #YZ1**: Expiry  
✅ **Stage #ZG5**: RDB Persistence - RDB file config
