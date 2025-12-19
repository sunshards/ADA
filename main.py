#!/usr/bin/env python3
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import create_app, socketio

app = create_app()

if __name__ == "__main__":
    socketio.run(app, debug=True, port=5004)