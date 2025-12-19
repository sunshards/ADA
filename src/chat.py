from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify, session, current_app
)
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
from bson.objectid import ObjectId
from src import socketio
from datetime import datetime
import uuid

from src.brain import main_modular

#TODO
# refactor with classes: es. message_obj should be class Message with get method that returns the object...
# safe for active_users there should be a User class
# in general you're relying too much on objects that don't have a defined structure and this will bite back

bp = Blueprint('chat', __name__, url_prefix='/chat')

# In-memory storage for demo (use database in production)
active_users = {}
chat_rooms = {}

class Message:
    def __init__(self, text, type, room, sid=None):
        self.message_id = str(uuid.uuid4())
        self.timestamp = datetime.now().isoformat()
        self.sid = sid
        self.text = text
        self.type = type
        self.room = room
    
    def getJSON(self):
        return {
            'message_id': self.message_id,
            'message': self.text,
            'sid': self.sid,
            'timestamp': self.timestamp,
            'type': self.type,
            'room': self.room
        }

SERVER_SID = 'SERVER_SID'

@bp.route('/')
def chat():
    user_id = session.get('user_id')
    character_id = session.get('character_id')
    return render_template('chat/chat.html', user_id=user_id, character_id=character_id)

@socketio.on('connect')
def handle_connect():
    user_id = request.args.get('user_id')
    character_id = request.args.get('character_id')

    user = current_app.db['Users'].find_one({"_id": ObjectId(user_id)})
    character = current_app.db['Characters'].find_one({"_id": ObjectId(character_id)})
    
    if (not user):
        print("User not found in handle_connect")
        return
    if (not character):
        print("Character not found in handle_connect")
        return
    username = user["Username"]
    avatar = character["avatar_base64"]
    room = request.args.get('room', 'default')
    
    # Store connection info
    active_users[request.sid] = {
        'user_id': user_id,
        'character_id' : character_id,
        'username': username,
        'room': room,
        'avatar_base64': avatar,
        'life_percentage' : 100
    }
    
    join_room(room)
    print(f'User {user_id}:{username} connected to room {room}')
    
    # Notify others in the room
    emit('user_joined', {
        'timestamp': datetime.now().isoformat(),
        'sid': request.sid,
        'user_id': user_id,
        'username': username,
        'active_users' : active_users
    }, room=room, skip_sid=request.sid)
    
    # Send connection confirmation
    emit('connected', {
        'status': 'success',
        'message': 'Connected to chat server',
        'room': room,
        'active_users' : active_users
    })

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in active_users:
        user_data = active_users[request.sid]
        room = user_data['room']
        
        del active_users[request.sid]

        emit('user_left', {
            'active_users': active_users,
            'username': user_data['username'],
            'timestamp': datetime.now().isoformat()
        }, room=room)
        
        print(f'User {user_data["user_id"]} disconnected')
    
@socketio.on('send_message')
def handle_send_message(data):
    """Handle incoming chat messages"""
    if request.sid not in active_users:
        print("Incoming message on server not in active_users")
        return
    
    user_data = active_users[request.sid]
    room = user_data['room']
    
    message = data.get('message', '').strip()
    if not message:
        return
    
    message = Message(text=message, sid=request.sid, type='incoming', room=room)
    message_obj = message.getJSON()
    
    # Save to database here in the future
    
    # Broadcast to room except to sender to display incoming message
    emit('new_message', message_obj, room=room, skip_sid=request.sid)
    
    # Send confimation to sender to display outgoing message
    sender_message = message_obj.copy()
    sender_message['type'] = 'outgoing'
    emit('message_sent', sender_message)

    # This forces the server to actually send the data above to the browser 
    # BEFORE starting the heavy AI logic.
    socketio.sleep(0.01)

    # Generate ADA response to input and send
    responses = generate_response(message.text, user_data["character_id"])
    for response in responses:
        server_send_message(text=response, room='default')

@socketio.on('typing')
def handle_typing(data):
    """Handle typing indicators"""
    if request.sid not in active_users:
        return
    
    user_data = active_users[request.sid]
    emit('user_typing', {
        'user_id': user_data['user_id'],
        'username': user_data['username'],
        'is_typing': data.get('is_typing', False)
    }, room=user_data['room'], skip_sid=request.sid)

# currently not used ?
@socketio.on('join_room')
def handle_join_room(data):
    room = data.get('room', 'default')
    user_id = data.get('user_id', 'anonymous')

    # Leave previous room
    if request.sid in active_users:
        old_room = active_users[request.sid]['room']
        leave_room(old_room)
        emit('user_left_room', {
            'user_id': user_id,
            'room': old_room
        }, room=old_room)
    
    # Join new room
    join_room(room)
    active_users[request.sid]['room'] = room
    
    emit('room_joined', {
        'room': room,
        'user_id': user_id,
        'message': f'Joined room: {room}'
    })

def server_send_message(text: str, room):
    message = Message(text=text, type='server', room=room, sid=SERVER_SID)
    message_obj = message.getJSON()
    # Save to database here in the future
    
    emit('new_message', message_obj, room=room)

def generate_response(user_input, character_id):
    return main_modular(character_id=character_id, user_input=user_input)

# def get_users_in_room(room):
#     """Get list of users in a room"""
#     users = []
#     for sid, data in active_users.items():
#         if data['room'] == room:
#             users.append({
#                 'user_id': data['user_id'],
#                 'sid': sid
#             })
#     return users