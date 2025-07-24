@echo off
echo ============================================
echo    Complete Redis Handshake Test Suite
echo ============================================
echo.

echo Cleaning up any existing Redis processes...
taskkill /F /IM python.exe 2>nul
timeout /t 1 /nobreak > nul

echo Step 1: Starting Master Server on port 6379...
start /B cmd /c "cd codecrafters-redis-python && python app/main.py --port 6379 > master.log 2>&1"
timeout /t 2 /nobreak > nul

echo Step 2: Testing Master Server with INFO command...
python -c "import socket; s = socket.socket(); s.connect(('localhost', 6379)); s.send(b'*1\r\n$4\r\nINFO\r\n'); resp = s.recv(1024); print('Master INFO Response Length:', len(resp)); print('Master Role:', 'master' if b'role:master' in resp else 'unknown'); s.close()"
echo.

echo Step 3: Starting Replica Server on port 6380...
echo This will perform the complete handshake: PING, REPLCONF x2, PSYNC
start /B cmd /c "cd codecrafters-redis-python && python app/main.py --port 6380 --replicaof \"localhost 6379\" > replica.log 2>&1"
timeout /t 3 /nobreak > nul

echo Step 4: Testing Replica Server with INFO command...
python -c "import socket; s = socket.socket(); s.connect(('localhost', 6380)); s.send(b'*1\r\n$4\r\nINFO\r\n'); resp = s.recv(1024); print('Replica INFO Response Length:', len(resp)); print('Replica Role:', 'slave' if b'role:slave' in resp else 'unknown'); s.close()"
echo.

echo Step 5: Checking handshake logs...
if exist codecrafters-redis-python\replica.log (
    echo === REPLICA LOG ===
    type codecrafters-redis-python\replica.log
    echo.
)

echo Step 6: Testing master server handles REPLCONF...
python -c "import socket; s = socket.socket(); s.connect(('localhost', 6379)); s.send(b'*3\r\n$8\r\nREPLCONF\r\n$14\r\nlistening-port\r\n$4\r\n6380\r\n'); resp = s.recv(1024); print('REPLCONF Response:', repr(resp)); s.close()"

echo Step 7: Testing master server handles PSYNC...
python -c "import socket; s = socket.socket(); s.connect(('localhost', 6379)); s.send(b'*3\r\n$5\r\nPSYNC\r\n$1\r\n?\r\n$2\r\n-1\r\n'); resp = s.recv(1024); print('PSYNC Response:', repr(resp)); s.close()"
echo.

echo ============================================
echo Test completed! Check the responses above.
echo ============================================
pause
