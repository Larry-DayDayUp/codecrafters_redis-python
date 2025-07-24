# Redis Server Test Suite

这个目录包含了 Redis 服务器实现的所有测试文件。

## 测试文件说明

### 基础测试
- **`test_basic.py`** - 基础命令测试 (PING, ECHO, 并发连接)
- **`test_storage.py`** - 存储命令测试 (SET, GET)
- **`test_expiry.py`** - 键过期测试 (PX 参数)
- **`test_config.py`** - 配置命令测试 (CONFIG GET)

### 高级功能测试
- **`test_rdb.py`** - RDB 持久化测试
- **`test_port_config.py`** - 端口配置测试
- **`test_info_command.py`** - INFO 命令测试
- **`test_replicaof.py`** - 复制模式测试 (--replicaof 标志)
- **`test_resp_format.py`** - RESP 协议格式验证测试

### 测试运行器
- **`run_all_tests.py`** - 主测试运行器，执行所有测试

## 运行测试

### 运行所有测试
```bash
cd tests
python run_all_tests.py
```

### 运行单个测试
```bash
cd tests
python test_basic.py
python test_replicaof.py
# ... 等等
```

## 测试覆盖范围

✅ **基础 Redis 命令**
- PING/PONG 响应
- ECHO 命令
- SET/GET 键值操作
- 并发客户端连接

✅ **高级功能**
- 键过期 (PX 参数)
- RDB 文件加载
- 配置参数 (--dir, --dbfilename, --port)
- INFO 命令 (replication 节)

✅ **复制功能**
- Master 模式 (默认)
- Replica 模式 (--replicaof 标志)
- 正确的 role 报告 (master/slave)
- RESP 协议格式验证

## CodeCrafters 阶段支持

所有测试都针对 CodeCrafters Redis 挑战的各个阶段进行了验证：
- Stage #JM1: 绑定端口
- Stage #RG2: 响应 PING
- Stage #WY1: 多次 PING 响应
- Stage #ZU2: 处理并发客户端
- Stage #QQ0: ECHO 命令实现
- Stage #LA7: SET & GET 命令
- Stage #YZ1: 键过期
- Stage #ZG5: RDB 文件配置
- Stage #JZ6, #GC6, #DQ3, #SM4: RDB 持久化
- Stage #BW1: 端口配置
- Stage #YE5: INFO 命令
- Stage #HC6: 复制模式的 INFO 命令

## 注意事项

- 测试需要 Python 3.6+ 运行
- 确保端口 6379-6395 可用（测试使用这些端口）
- 测试会自动启动和停止 Redis 服务器实例
- 所有测试都独立运行，互不干扰

---

*原始 README 内容保留在下方：*

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

# Test key expiration
python tests/test_expiry.py

# Test configuration
python tests/test_config.py
```

## Test Coverage:

✅ **Basic Redis Commands**
- PING command with PONG response
- ECHO command with argument echo
- Concurrent client handling

✅ **Storage Operations**  
- SET command for storing key-value pairs
- GET command for retrieving values
- Non-existent key handling

✅ **Advanced Features**
- Key expiration with PX parameter
- Automatic cleanup of expired keys
- CONFIG GET for server configuration

## Notes:

- Tests require a running Redis server on localhost:6379
- Each test module can be run independently
- The main test runner (`run_all_tests.py`) provides comprehensive coverage
- All tests use proper Redis RESP protocol formatting
- Tests verify both successful operations and error conditions
