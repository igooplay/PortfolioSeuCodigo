#!/usr/bin/env python3
import os
import eventlet
eventlet.monkey_patch()

# Execute o arquivo main.py com configurações para WebSocket
from app import socketio, app
print("Iniciando servidor com Socket.IO...")
socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)