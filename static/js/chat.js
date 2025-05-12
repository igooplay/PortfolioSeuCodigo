// Chat functionality for SeuCodigo with Socket.IO

document.addEventListener('DOMContentLoaded', function() {
  const chatContainer = document.querySelector('.chat-container');
  const messageForm = document.getElementById('message-form');
  const messageInput = document.getElementById('content');
  const partnerId = document.getElementById('partner-id')?.value;
  
  // Scroll chat to bottom
  function scrollChatToBottom() {
    if (chatContainer) {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  }
  
  // Initialize chat scroll position
  scrollChatToBottom();

  // Initialize Socket.IO connection
  let socket;
  if (typeof io !== 'undefined' && document.querySelector('[data-socket-enabled="true"]')) {
    socket = io();

    // Handle connection
    socket.on('connect', function() {
      console.log('Connected to Socket.IO server');
      
      // Join chat room with partner
      if (partnerId) {
        socket.emit('join_chat', { partner_id: partnerId });
      }
    });
    
    // Handle disconnection
    socket.on('disconnect', function() {
      console.log('Disconnected from Socket.IO server');
    });
    
    // Handle new messages
    socket.on('new_message', function(message) {
      console.log('New message received:', message);
      addMessageToChat(message);
      scrollChatToBottom();
    });
    
    // Handle message notifications
    socket.on('new_message_notification', function(message) {
      console.log('New message notification received:', message);
      // Could add notification logic here for unread messages
      // If we're not in the current chat, we could display a notification
    });
  }
  
  // Send message form handler
  if (messageForm && partnerId) {
    messageForm.addEventListener('submit', function(e) {
      e.preventDefault();
      
      const content = messageInput.value.trim();
      if (!content) return;
      
      if (socket && socket.connected) {
        // Send via Socket.IO
        socket.emit('send_message', {
          content: content,
          recipient_id: parseInt(partnerId)
        });
        
        // Clear the input
        messageInput.value = '';
      } else {
        // Fallback to AJAX
        fetch('/api/messages', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            content: content,
            recipient_id: parseInt(partnerId)
          }),
        })
        .then(response => {
          if (!response.ok) {
            throw new Error('Network response was not ok');
          }
          return response.json();
        })
        .then(data => {
          // Add the new message to the chat
          addMessageToChat(data);
          
          // Clear the input
          messageInput.value = '';
          
          // Scroll to the bottom of the chat
          scrollChatToBottom();
        })
        .catch(error => {
          console.error('Error sending message:', error);
          alert('Erro ao enviar mensagem. Por favor, tente novamente.');
        });
      }
    });
  }
  
  // Add message to the chat interface
  function addMessageToChat(message) {
    if (!chatContainer) return;
    
    const messageElement = document.createElement('div');
    
    // Get current user ID from data attribute
    const currentUserId = parseInt(chatContainer.dataset.currentUser);
    
    // Check if message is from current user
    const isFromCurrentUser = message.sender_id === currentUserId;
    
    // Build message class based on sender
    const messageClass = isFromCurrentUser ? 'chat-message chat-message-user' : 'chat-message chat-message-admin';
    
    // Format timestamp
    const timestamp = new Date(message.timestamp);
    const formattedTime = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // Set message content
    messageElement.className = messageClass;
    messageElement.innerHTML = `
      <div class="mb-1 font-bold">${isFromCurrentUser ? 'Você' : message.sender_name}</div>
      <div>${message.content}</div>
      <div class="text-xs text-right mt-1 opacity-75">${formattedTime}</div>
    `;
    
    // Add to chat container
    chatContainer.appendChild(messageElement);
  }
  
  // Periodic check for new messages (fallback for non-socket connections)
  function fetchMessages() {
    if (!chatContainer || !partnerId || (socket && socket.connected)) return;
    
    fetch(`/api/messages?partner_id=${partnerId}`)
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(messages => {
        // Clear existing messages
        chatContainer.innerHTML = '';
        
        // Add all messages
        messages.forEach(message => {
          addMessageToChat(message);
        });
        
        // Scroll to bottom
        scrollChatToBottom();
      })
      .catch(error => {
        console.error('Error fetching messages:', error);
      });
  }
  
  // Initial fetch for fallback only
  if (chatContainer && partnerId && (!socket || !socket.connected)) {
    fetchMessages();
    
    // Fetch new messages every 5 seconds as fallback
    setInterval(fetchMessages, 5000);
  }
  
  // Handle admin chat user selection
  const chatUserLinks = document.querySelectorAll('.chat-user-link');
  
  chatUserLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      
      // Leave current chat room if connected
      if (socket && socket.connected && partnerId) {
        socket.emit('leave_chat', { partner_id: partnerId });
      }
      
      // Remove active class from all user links
      chatUserLinks.forEach(el => el.classList.remove('bg-indigo-100'));
      
      // Add active class to clicked link
      this.classList.add('bg-indigo-100');
      
      // Update the chat interface with the selected user
      const userId = this.dataset.userId;
      window.location.href = `/admin/chats?user_id=${userId}`;
    });
  });
});
