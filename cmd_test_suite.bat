@echo off
echo ============================================
echo        Redis Server CMD Test Suite
echo ============================================
echo.

echo Test 1: INFO command
python -c "import socket; s = socket.socket(); s.connect(('localhost', 6379)); s.send(b'*1\r\n$4\r\nINFO\r\n'); print('INFO Response:', repr(s.recv(1024))); s.close()"
echo.

echo Test 2: PING command  
python -c "import socket; s = socket.socket(); s.connect(('localhost', 6379)); s.send(b'*1\r\n$4\r\nPING\r\n'); print('PING Response:', repr(s.recv(1024))); s.close()"
echo.

echo Test 3: SET and GET commands
python -c "import socket; s = socket.socket(); s.connect(('localhost', 6379)); s.send(b'*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$5\r\nvalue\r\n'); s.recv(1024); s.send(b'*2\r\n$3\r\nGET\r\n$3\r\nkey\r\n'); print('GET Response:', repr(s.recv(1024))); s.close()"
echo.

echo Test 4: INFO replication command
python -c "import socket; s = socket.socket(); s.connect(('localhost', 6379)); s.send(b'*2\r\n$4\r\nINFO\r\n$11\r\nreplication\r\n'); print('INFO replication Response:', repr(s.recv(1024))); s.close()"
echo.

echo All tests completed!
pause
