[![progress-banner](https://backend.codecrafters.io/progress/redis/8979aa7a-341e-4816-8065-6fb22e30dccb)](https://app.codecrafters.io/users/codecrafters-bot?r=2qF)

# Redis Server Implementation

🚀 A Redis server implementation built for the [CodeCrafters Redis Challenge](https://codecrafters.io/challenges/redis).

This is a Python solution to the "Build Your Own Redis" Challenge. In this challenge, I built a Redis clone capable of handling basic commands like `PING`, `SET`, `GET`, and more advanced features like key expiration and concurrent client handling.

## ✅ Implemented Features

### Core Commands
- **PING** - Basic connectivity test  
- **ECHO** - Echo back messages
- **SET** - Store key-value pairs (with optional PX expiry)
- **GET** - Retrieve values by key
- **CONFIG GET** - Retrieve server configuration

### Advanced Features  
- **🔄 Concurrent Client Support** - Multi-threaded client handling
- **⏰ Key Expiration** - TTL support with millisecond precision
- **⚙️ Configuration Management** - Command-line arguments for dir/dbfilename
- **🗂️ RDB File Config** - Redis Database file configuration support

## 🏗️ Project Structure

```
codecrafters-redis-python/
├── app/
│   └── main.py              # Main Redis server implementation
├── tests/
│   ├── test_basic.py        # Basic command tests
│   ├── test_storage.py      # SET/GET tests  
│   ├── test_expiry.py       # Key expiration tests
│   ├── test_config.py       # Configuration tests
│   └── run_all_tests.py     # Complete test runner
├── push_both.ps1            # Script to push to both repos
└── README.md
```

## 🚀 Quick Start

### Start the Redis Server
```bash
python app/main.py --dir /tmp/redis-data --dbfilename dump.rdb
```

### Test with Redis CLI  
```bash
redis-cli PING
redis-cli SET mykey myvalue
redis-cli GET mykey
redis-cli SET tempkey tempvalue PX 5000  # Expires in 5 seconds
redis-cli CONFIG GET dir
```

### Run Comprehensive Tests
```bash
python tests/run_all_tests.py
```

## 📊 CodeCrafters Progress

- ✅ Stage #JM1: Bind to a port
- ✅ Stage #RG2: Respond to PING
- ✅ Stage #WY1: Respond to multiple PINGs  
- ✅ Stage #ZU2: Handle concurrent clients
- ✅ Stage #QQ0: Implement the ECHO command
- ✅ Stage #LA7: Implement the SET & GET commands
- ✅ Stage #YZ1: Key expiration (Expiry)
- ✅ Stage #ZG5: RDB file configuration

**Note**: If you're viewing this repo on GitHub, head over to
[codecrafters.io](https://codecrafters.io) to try the challenge.

# Passing the first stage

The entry point for your Redis implementation is in `app/main.py`. Study and
uncomment the relevant code, and push your changes to pass the first stage:

```sh
git commit -am "pass 1st stage" # any msg
git push origin master
```

That's all!

# Stage 2 & beyond

Note: This section is for stages 2 and beyond.

1. Ensure you have `python (3.13)` installed locally
1. Run `./your_program.sh` to run your Redis server, which is implemented in
   `app/main.py`.
1. Commit your changes and run `git push origin master` to submit your solution
   to CodeCrafters. Test output will be streamed to your terminal.

# Troubleshooting

## module `socket` has no attribute `create_server`

When running your server locally, you might see an error like this:

```
Traceback (most recent call last):
  File "/.../python3.7/runpy.py", line 193, in _run_module_as_main
    "__main__", mod_spec)
  File "/.../python3.7/runpy.py", line 85, in _run_code
    exec(code, run_globals)
  File "/app/app/main.py", line 11, in <module>
    main()
  File "/app/app/main.py", line 6, in main
    s = socket.create_server(("localhost", 6379), reuse_port=True)
AttributeError: module 'socket' has no attribute 'create_server'
```

This is because `socket.create_server` was introduced in Python 3.8, and you
might be running an older version.

You can fix this by installing Python 3.8 locally and using that.

If you'd like to use a different version of Python, change the `language_pack`
value in `codecrafters.yml`.
