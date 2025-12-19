// static/chat/chat.js
document.addEventListener('DOMContentLoaded', function() {

    // DOM Elements
    const messagesContainer = document.querySelector('.card-body');
    const messageTextarea = document.querySelector('textarea.form-control');
    const sendButton = document.getElementById('sendButton');

    let socket = null;
    let currentUser = null;
    let currentRoom = 'default';
    let isTyping = false;
    let typingTimeout = null;
    const SERVER_SID = 'SERVER_SID'

    // sid: user_id, character_id, username, room, avatar_base64, life_percentage
    let active_users = null;

    // Initialize
    initChat();
    
    function initChat() {
        // data in window passed from jinja template
        currentUser = {
            user_id: window.user_id,
            character_id : window.character_id,
        };
        
        // Connect to Socket.IO
        connectSocket();
        
        // Setup event listeners
        setupEventListeners();
        
        // Load existing messages (optional)
        // loadExistingMessages();
    }

    function connectSocket() {
        // Disconnect existing socket if any
        if (socket) {
            socket.disconnect();
        }
        
        // Connect to server with query parameters
        socket = io({
            query: {
                user_id: currentUser.user_id,
                character_id : currentUser.character_id,
                room: currentRoom,
            },
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionAttempts: 5
        });
        
        // Socket event handlers
        socket.on('connect', handleSocketConnect);
        socket.on('disconnect', handleSocketDisconnect);
        socket.on('connected', handleConnected);
        socket.on('new_message', handleNewMessage);
        socket.on('message_sent', handleMessageSent);
        socket.on('user_joined', handleUserJoined);
        socket.on('user_left', handleUserLeft);
        socket.on('user_typing', handleUserTyping);
        socket.on('room_joined', handleRoomJoined);
    }

    function setupEventListeners() {
        // Send message on Enter (without Shift)
        messageTextarea.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            } else {
                handleTyping();
            }
        });
        
        // Send button in chat
        sendButton.addEventListener('click', sendMessage);
        
        // Typing indicator
        messageTextarea.addEventListener('input', handleTyping);
        
        // Clear typing indicator when textarea loses focus
        messageTextarea.addEventListener('blur', function() {
            if (isTyping) {
                emitTyping(false);
            }
        });
    }

    function handleSocketConnect() {
        console.log('Attempting to connect to chat server...');
        updateConnectionStatus('Connecting...', 'warning');
    }

    function handleSocketDisconnect() {
        console.log('Disconnected from chat server');
        updateConnectionStatus('Disconnected', 'danger');
    }

    function handleConnected(data) {
        console.log('Successfully connected:', data);
        updateConnectionStatus('Connected', 'success');
        refreshActivePlayers(data.active_users)
    }

    function handleNewMessage(data) {
        // Handles incoming messages
        addMessageToChat(data);
        playNotificationSound();
    }

    function handleMessageSent(data) {
        // Handles outgoing messages
        addMessageToChat(data);
    }

    function handleUserJoined(data) {
        showSystemMessage(`${data.username} joined the chat`, 'info');
        refreshActivePlayers(data.active_users)
    }

    function handleUserLeft(data) {
        showSystemMessage(`${data.username} left the chat`, 'info');
        refreshActivePlayers(data.active_users)
    }

    function handleUserTyping(data) {
        showTypingIndicator(data.username, data.is_typing);
    }

    function handleRoomJoined(data) {
        console.log(`Joined room: ${data.room}`);
        currentRoom = data.room;
        clearMessages(); // Clear chat for new room
        showSystemMessage(`You joined room: ${data.room}`, 'success');
    }

    function sendMessage() {
        const message = messageTextarea.value.trim();

        if (!message) {
            return;
        }
        
        if (!socket || !socket.connected) {
            alert('Not connected to chat server. Please refresh the page.');
            return;
        }

        messageTextarea.value = '';

        // Clear typing indicator
        emitTyping(false);
        
        // Send to server
        socket.emit('send_message', {
            message: message,
        });
    }

    function handleTyping() {
        if (!socket || !socket.connected) return;
        
        // Clear existing timeout
        if (typingTimeout) {
            clearTimeout(typingTimeout);
        }
        
        // Start typing indicator
        if (!isTyping) {
            isTyping = true;
            emitTyping(true);
        }
        
        // Set timeout to stop typing indicator after 1 second of inactivity
        typingTimeout = setTimeout(() => {
            isTyping = false;
            emitTyping(false);
        }, 1000);
    }

    function emitTyping(isTypingFlag) {
        if (!socket || !socket.connected) return;
        
        socket.emit('typing', {
            username: currentUser.username,
            is_typing: isTypingFlag
        });
    }

    function addMessageToChat(messageData) {
        let avatar_base64 = null
        let username = null
        console.log(messageData.type)
        if (messageData.type == 'server') {
            avatar_base64 = "data:image/png;base64,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"
            username = "ADA"
        } else {
            avatar_base64 = "data:image/jpeg;base64," + active_users[messageData.sid]['avatar_base64']
            username = active_users[messageData.sid]['username']
        }

        //ingoing or outgoing
        type = messageData.type // might create problems ? check if orientation is alright

        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = `d-flex mb-3 ${type === 'outgoing' ? 'flex-row-reverse' : ''}`;
        messageDiv.setAttribute('data-message-id', messageData.message_id);
        
        // Format timestamp
        const timestamp = new Date(messageData.timestamp);
        const timeString = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        // Avatar
        const avatarImg = document.createElement('img');
        avatarImg.className = 'rounded-circle me-2';
        avatarImg.width = 40;
        avatarImg.height = 40;
        avatarImg.alt = "Chat Avatar Image";
        avatarImg.src = avatar_base64
        
        // Message bubble
        const messageBubble = document.createElement('div');
        messageBubble.className = `message me-2 ${type === 'outgoing' ? 'message-out' : 'message-in'}`;
        
        // Message content
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = messageData.message;
        
        // Message meta (username and time)
        const messageMeta = document.createElement('div');
        messageMeta.className = `message-meta small text-muted ${type === 'outgoing' ? 'text-end' : ''}`;
        messageMeta.innerHTML = `
            <span class="username fw-bold">${username}</span>
            <span class="time ms-2">${timeString}</span>
        `;
        
        // Assemble
        messageBubble.appendChild(messageContent);
        messageBubble.appendChild(messageMeta);
        messageDiv.appendChild(avatarImg);
        messageDiv.appendChild(messageBubble);
        
        // Add to container
        messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        scrollToBottom();
    }

    function showSystemMessage(text, type = 'info') {
        const systemDiv = document.createElement('div');
        systemDiv.className = `system-message text-center my-2 text-${type}`;
        systemDiv.innerHTML = `
            <span class="badge bg-${type}">${text}</span>
        `;
        messagesContainer.appendChild(systemDiv);
        scrollToBottom();
    }

    function showTypingIndicator(username, isTyping) {
        // Find existing typing indicator
        let indicator = document.querySelector('.typing-indicator');
        
        if (isTyping) {
            if (!indicator) {
                indicator = document.createElement('div');
                indicator.className = 'typing-indicator text-muted small';
                messagesContainer.appendChild(indicator);
            }
            indicator.textContent = `${username} is typing...`;
        } else if (indicator) {
            indicator.remove();
        }
    }

    function updateConnectionStatus(status, type) {
        // Add a status indicator to your UI
        let statusIndicator = document.querySelector('#connection-status');
        
        if (!statusIndicator) {
            statusIndicator = document.createElement('div');
            statusIndicator.id = 'connection-status';
            statusIndicator.className = 'position-fixed bottom-0 end-0 m-3';
            document.body.appendChild(statusIndicator);
        }
        
        statusIndicator.innerHTML = `
            <span class="badge bg-${type}">${status}</span>
        `;
    }

    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function clearMessages() {
        messagesContainer.innerHTML = '';
    }

    function playNotificationSound() {
        // Optional: Play sound for new messages
        const audio = new Audio('/static/notification.mp3');
        audio.play().catch(e => console.log('Audio play failed:', e));
    }

    function addPlayerCard(user_sid) {

        const username = active_users[user_sid]["username"]
        const avatar_base64 = "data:image/jpeg;base64," + active_users[user_sid]['avatar_base64']
        const life_percentage = active_users[user_sid]['life_percentage']

        // Create HTML elements
    
        const playerCard = document.createElement('div');
        playerCard.className = 'mb-4 player-card rounded-1';
        playerCard.id = username; //used for removal
        
        const playerAvatar = document.createElement('img')
        playerAvatar.className = "card-img-top player-avatar"
        playerAvatar.setAttribute('alt', 'Player Avatar')
        playerAvatar.setAttribute('src', avatar_base64)

        const playerInfo = document.createElement('div');
        playerInfo.className = 'player-info';     
        
        const playerName = document.createElement('span');
        playerName.className = 'player-name';
        playerName.innerHTML = username;

        const lifebarContainer = document.createElement('div');
        lifebarContainer.className = 'progress lifebar-container'
        lifebarContainer.setAttribute('role', 'lifebar')
        lifebarContainer.setAttribute('aria-label', 'Lifebar')
        lifebarContainer.setAttribute('aria-valuenow',  String(life_percentage))
        lifebarContainer.setAttribute('aria-valuemin', '0')
        lifebarContainer.setAttribute('aria-valuemax', '100')

        const lifebarHealth = document.createElement('div');
        lifebarHealth.className = "progress-bar lifebar-health"
        lifebarHealth.setAttribute('style', `width: ${life_percentage}%`)

        // Assemble
        const playerContainer = document.getElementById('player-container')
        playerContainer.appendChild(playerCard)

        playerCard.appendChild(playerAvatar)
        playerCard.appendChild(playerInfo)

        playerInfo.appendChild(playerName)
        playerInfo.appendChild(lifebarContainer)

        lifebarContainer.appendChild(lifebarHealth)
    }

    function refreshPlayerCards(users_sid) {
        const player_cards = document.querySelectorAll('.player-card');
        player_cards.forEach(card => card.remove());
        
        for (sid of users_sid) {
            addPlayerCard(sid)
        }
    }

    function refreshActivePlayers(users) {
        active_users = users
        refreshPlayerCards(Object.keys(active_users)) 
    }

    function removeActivePlayer(sid_to_remove) {
        active_users.remove(sid_to_remove)
        refreshPlayerCards(Object.keys(active_users)) 
    }

        
    // Expose functions for debugging
    window.chat = {
        connect: connectSocket,
        disconnect: () => socket.disconnect(),
        sendMessage: sendMessage,
        joinRoom: (room) => {
            if (socket && socket.connected) {
                socket.emit('join_room', { room: room });
            }
        }
    };
});


