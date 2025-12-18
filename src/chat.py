from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify, session, current_app
)
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
from bson.objectid import ObjectId
from src import socketio
from datetime import datetime
bp = Blueprint('chat', __name__, url_prefix='/chat')
import uuid

# In-memory storage for demo (use database in production)
active_users = {}
chat_rooms = {}

@bp.route('/')
def chat():
    # Get user from session (adjust based on your auth system)
    user_id = session.get('user_id')
    user = current_app.db['Users'].find_one({"_id": ObjectId(user_id)})
    username = user["Username"]
    
    # You might get avatar from database or session
    # avatar = session.get('avatar', 'temp/avatar_animal_00001.png')
    avatar='default'
    # Get messages and players 
    messages = []  # From database
    players = []   # From database
    
    return render_template('chat/chat.html',
                            user_id=user_id,
                            username=username,
                            avatar=avatar,
                            messages=messages,
                            players=players)

@socketio.on('connect')
def handle_connect():
    user_id = request.args.get('user_id') or 'anonymous'
    username = request.args.get('username') or 'anonymous'
    room = request.args.get('room', 'default')
    
    # Store connection info
    active_users[request.sid] = {
        'user_id': user_id,
        'username': username,
        'room': room,
        'avatar': 'default'
    }
    
    join_room(room)
    print(f'User {user_id}:{username} connected to room {room}')
    
    # Notify others in the room
    emit('user_joined', {
        'user_id': user_id,
        'username': username,
        'sid': request.sid,
        'timestamp': datetime.now().isoformat()
    }, room=room, skip_sid=request.sid)
    
    # Send connection confirmation
    emit('connected', {
        'status': 'success',
        'message': 'Connected to chat server',
        'room': room,
        'users_in_room': get_users_in_room(room)
    })

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in active_users:
        user_data = active_users[request.sid]
        room = user_data['room']
        
        # Notify others
        emit('user_left', {
            'user_id': user_data['user_id'],
            'username': user_data['username'],
            'timestamp': datetime.now().isoformat()
        }, room=room)
        
        # Clean up
        del active_users[request.sid]
        print(f'User {user_data["user_id"]} disconnected')

@socketio.on('send_message')
def handle_send_message(data):
    """Handle incoming chat messages"""
    if request.sid not in active_users:
        print("Incoming message on server not in active_users")
        return
    
    user_data = active_users[request.sid]
    room = user_data['room']
    
    # Validate message
    message = data.get('message', '').strip()
    if not message:
        return
    
    # Create message object
    message_obj = {
        'id': str(uuid.uuid4()),
        'user_id': user_data['user_id'],
        'username': user_data['username'],
        'avatar': user_data['avatar'],
        'message': message,
        'timestamp': datetime.now().isoformat(),
        'type': 'incoming',  # For other users
        'room': room
    }
    
    # Save to database here in the future
    
    # Broadcast to room except to sender to display incoming message
    emit('new_message', message_obj, room=room, skip_sid=request.sid)
    
    # Send confimation to sender to display outgoing message
    sender_message = message_obj.copy()
    sender_message['type'] = 'outgoing'
    emit('message_sent', sender_message)

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

def get_users_in_room(room):
    """Get list of users in a room"""
    users = []
    for sid, data in active_users.items():
        if data['room'] == room:
            users.append({
                'user_id': data['user_id'],
                'sid': sid
            })
    return users