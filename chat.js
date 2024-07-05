document.addEventListener("DOMContentLoaded", function () {
    const chatButton = document.getElementById("open-chat-button");
    const chatContainer = document.getElementById("chat-container");
    

    // Function to open the chat window
    chatButton.addEventListener("click", function () {
        chatContainer.style.display = "block";
    });


    
    const chatMessages = document.getElementById('chat-messages');
    const messageInput = document.getElementById('message-input');

// Function to add a message to the chat with a timestamp
    function addMessage(message, isUser = false) {
        const messageContainer = document.createElement('div');
        messageContainer.classList.add('message-container');

        const messageElement = document.createElement('div');
        messageElement.classList.add('message', isUser ? 'user-message' : 'bot-message');

        // Create a timestamp element
        const timestampElement = document.createElement('div');
        const timestamp = new Date().toLocaleTimeString();
        timestampElement.innerText = timestamp;
        timestampElement.classList.add('timestamp');

        messageElement.innerText = message;

        messageContainer.appendChild(messageElement);
        messageContainer.appendChild(timestampElement);

        chatMessages.appendChild(messageContainer);

        // Scroll to the bottom of the chat
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Function to send a message to the bot and receive a response
    async function sendMessageToBot(message) {
        try {
            const apiUrl = 'http://127.0.0.1:5000/bot'; // Fixed the API URL
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message }), // Changed 'user_message' to 'message'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            return data.message; // Changed 'bot_message' to 'message'
        } catch (error) {
            console.error('Error:', error);
            return 'Error: Failed to fetch bot response.';
        }
    }


    // Event listener for sending a message
    messageInput.addEventListener('keypress', async function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            const message = messageInput.value.trim();
            if (message !== '') {
                addMessage(message, true);
                messageInput.value = '';

                // Send the user message to the bot
                const botResponse = await sendMessageToBot(message);
                addMessage(botResponse);
            }
        }
    });

    // Example: Start a conversation with a greeting
    addMessage('Hello! How can I assist you today?');
});