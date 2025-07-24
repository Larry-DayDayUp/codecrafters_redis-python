@echo off
echo ============================================
echo    Redis Replica Handshake Test (CMD)
echo ============================================
echo.

echo Step 1: Starting master server on port 6379...
start /B python app/main.py --port 6379
timeout /t 2 /nobreak > nul

echo Step 2: Starting replica server on port 6380...
echo This will connect to master and perform handshake
start /B python app/main.py --port 6380 --replicaof "localhost 6379"
timeout /t 3 /nobreak > nul

echo Step 3: Testing master server INFO command...
python -c "import socket; s = socket.socket(); s.connect(('localhost', 6379)); s.send(b'*1\r\n$4\r\nINFO\r\n'); print('Master INFO:', repr(s.recv(1024))); s.close()"
echo.

echo Step 4: Testing replica server INFO command...
python -c "import socket; s = socket.socket(); s.connect(('localhost', 6380)); s.send(b'*1\r\n$4\r\nINFO\r\n'); print('Replica INFO:', repr(s.recv(1024))); s.close()"
echo.

echo Handshake test completed!
echo Check the console output for handshake messages.
pause
