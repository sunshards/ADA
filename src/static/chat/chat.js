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

    // Initialize
    initChat();
    
    function initChat() {
        // data in window passed from jinja template
        currentUser = {
            id: window.userId,
            username: window.username,
            avatar: 'default.png' // window.avatar
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
                user_id: currentUser.id,
                room: currentRoom,
                username: currentUser.username
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
        refreshPlayerCards(data.active_users)
    }

    function handleNewMessage(data) {
        // Add incoming message to chat
        addMessageToChat(data, 'incoming');
        playNotificationSound();
    }

    function handleMessageSent(data) {
        // Add outgoing message to chat (already added locally, but ensures delivery)
        addMessageToChat(data, 'outgoing');
        messageTextarea.value = ''; // Clear input
    }

    function handleUserJoined(data) {
        // Show user joined notification
        showSystemMessage(`${data.username} joined the chat`, 'info');
        refreshPlayerCards(data.active_users)
        // Update users list, fetch updated list or update locally
    }

    function handleUserLeft(data) {
        // Show user left notification
        showSystemMessage(`${data.username} left the chat`, 'info');
        removePlayerCard(data.username)
    }

    function handleUserTyping(data) {
        // Show typing indicator
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
        
        // // Add message locally immediately for UX
        // const tempMessage = {
        //     id: 'temp_' + Date.now(),
        //     user_id: currentUser.id,
        //     username: currentUser.username,
        //     avatar: currentUser.avatar,
        //     message: message,
        //     timestamp: new Date().toISOString(),
        //     type: 'outgoing'
        // };
        
        //addMessageToChat(tempMessage, 'outgoing');

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

    function addMessageToChat(messageData, type) {
        // Remove temporary message if exists
        // const tempMessage = document.querySelector(`[data-message-id="${messageData.id}"]`);
        // if (tempMessage) {
        //     tempMessage.remove();
        // }
        
        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = `d-flex mb-3 ${type === 'outgoing' ? 'flex-row-reverse' : ''}`;
        messageDiv.setAttribute('data-message-id', messageData.id);
        
        // Format timestamp
        const timestamp = new Date(messageData.timestamp);
        const timeString = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        // Avatar
        const avatarImg = document.createElement('img');
        avatarImg.className = 'rounded-circle me-2';
        avatarImg.width = 40;
        avatarImg.height = 40;
        avatarImg.alt = messageData.username;
        avatarImg.src = messageData.avatar.startsWith('http') 
            ? messageData.avatar 
            : `/static/${messageData.avatar}`;
        
        // Message bubble
        const messageBubble = document.createElement('div');
        messageBubble.className = `message ${type === 'outgoing' ? 'message-out me-2' : 'message-in'}`;
        
        // Message content
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = messageData.message;
        
        // Message meta (username and time)
        const messageMeta = document.createElement('div');
        messageMeta.className = `message-meta small text-muted ${type === 'outgoing' ? 'text-end' : ''}`;
        messageMeta.innerHTML = `
            <span class="username fw-bold">${messageData.username}</span>
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

    // currently not used 
    function loadExistingMessages() {
        // Load previous messages via AJAX (optional)
        fetch(`/api/chat/messages?room=${currentRoom}`)
            .then(response => response.json())
            .then(messages => {
                messages.forEach(msg => {
                    const type = msg.user_id === currentUser.id ? 'outgoing' : 'incoming';
                    addMessageToChat(msg, type);
                });
            })
            .catch(error => {
                console.error('Failed to load messages:', error);
            });
    }

    function playNotificationSound() {
        // Optional: Play sound for new messages
        const audio = new Audio('/static/notification.mp3');
        audio.play().catch(e => console.log('Audio play failed:', e));
    }

    function updateUsersList(users) {
        // Update player list with active users
        // Implement based on your player-box structure
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


function addPlayerCard(username, avatar_src, life_percentage=100) {

        // Create HTML elements
    
        const playerCard = document.createElement('div');
        playerCard.className = 'mb-4 player-card rounded-1';
        playerCard.id = username; //used for removal
    
        const playerAvatar = document.createElement('img')
        playerAvatar.className = "card-img-top player-avatar"
        playerAvatar.setAttribute('alt', 'Player Avatar')
        playerAvatar.setAttribute('src', avatar_src)

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

function removePlayerCard(username) {
    const playerCard = document.getElementById(username);
    playerCard.remove();
}

function refreshPlayerCards(users) {
    player_cards = document.getElementsByClassName('player-card')
    for (card of player_cards) {
        card.remove()
    }
    for ([sid, user] of Object.entries(users)) {
        addPlayerCard(user["username"], user["avatar"], 100)
    }
}