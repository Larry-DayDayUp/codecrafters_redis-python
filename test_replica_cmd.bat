@echo off
echo ============================================
echo     Redis Replica Mode CMD Test
echo ============================================
echo.

echo Starting Redis server in replica mode on port 6380...
echo Connecting to master at localhost:6379
echo.

start /B python app/main.py --port 6380 --replicaof "localhost 6379"

timeout /t 2 /nobreak > nul

echo Testing replica server INFO command...
python -c "import socket; s = socket.socket(); s.connect(('localhost', 6380)); s.send(b'*1\r\n$4\r\nINFO\r\n'); print('Replica INFO Response:', repr(s.recv(1024))); s.close()"
echo.

echo Testing replica server INFO replication command...
python -c "import socket; s = socket.socket(); s.connect(('localhost', 6380)); s.send(b'*2\r\n$4\r\nINFO\r\n$11\r\nreplication\r\n'); print('Replica INFO replication Response:', repr(s.recv(1024))); s.close()"
echo.

echo Replica test completed!
pause
