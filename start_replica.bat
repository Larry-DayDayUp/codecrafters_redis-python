@echo off
cd codecrafters-redis-python
python app/main.py --port 6380 --replicaof "localhost 6379"
