let isWaitingForResponse = false;
let username = localStorage.getItem("username") || "User";

document.addEventListener("DOMContentLoaded", () => {
    const chatBox = document.querySelector('.chat-box');
    const messageInput = document.querySelector('.message-input');
    const sendButton = document.querySelector('.send-button');
    const serverUrl = "https://ai-test-doc.onrender.com/send";
    const loadingDiv = document.getElementById("loading");
    const sendBtn = document.getElementById("send-btn");
    const userInput = document.getElementById("user-input");

    // 🔹 تحميل المحادثات المحفوظة عند تحميل الصفحة
    window.onload = function() {
        const savedChat = JSON.parse(localStorage.getItem('chatHistory')) || [];
        savedChat.forEach(chat => {
            if (chat.sender === "user") {
                chatBox.innerHTML += `<div class="user-message">${chat.message}</div>`;
            } else if (chat.sender === "bot") {
                chatBox.innerHTML += `<div class="bot-response">${chat.message}</div>`;
            }
        });
        chatBox.scrollTop = chatBox.scrollHeight;
    };

    // 🔹 حفظ المحادثات في Local Storage
    function saveMessageToLocalStorage(message, sender) {
        let chatHistory = JSON.parse(localStorage.getItem("chatHistory")) || [];
        chatHistory.push({ sender: sender, message: message, timestamp: new Date().toISOString() });
        localStorage.setItem("chatHistory", JSON.stringify(chatHistory));
    }

    // إرسال الرسالة
    sendButton.addEventListener('click', () => {
        const message = messageInput.value;
        if (message.trim() === "") return;

        chatBox.innerHTML += `<div class="user-message">${message}</div>`;
        messageInput.value = '';
        saveMessageToLocalStorage(message, "user");

        fetch(serverUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            chatBox.innerHTML += `<div class="bot-response">${data.response}</div>`;
            saveMessageToLocalStorage(data.response, "bot");
        })
        .catch(error => console.error('خطأ في الاتصال بالخادم:', error));
    });

    // تحميل المحادثات السابقة عند التحميل
    loadChatHistory();

    // إرسال الرسالة عند الضغط على زر الإرسال
    sendBtn.addEventListener("click", () => {
        sendMessage();
    });

    // إرسال الرسالة عند الضغط على Enter
    userInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});

// دالة إرسال الرسالة
function sendMessage() {
    if (isWaitingForResponse) return;

    const serverUrl = "https://ai-test-doc.onrender.com/send";
    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const loadingDiv = document.getElementById("loading");

    isWaitingForResponse = false;

    function saveChat() {
        localStorage.setItem("chatHistory", chatBox.innerHTML);
    }

    function addMessage(content, sender = "user") {
        const messageBubble = document.createElement("div");
        messageBubble.classList.add("message-bubble", sender);
        messageBubble.innerHTML = content;
        chatBox.appendChild(messageBubble);
        chatBox.scrollTop = chatBox.scrollHeight;
        saveMessageToLocalStorage(content, sender); // 🔹 حفظ المحادثة
    }

    sendBtn.addEventListener("click", () => {
        if (isWaitingForResponse) return;

        const message = userInput.value.trim();
        if (message) {
            addMessage(message, "user");
            userInput.value = "";

            isWaitingForResponse = true;
            userInput.disabled = true;
            sendBtn.disabled = true;
            loadingDiv.style.display = "block";

            fetch(serverUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ user: "User", message: message })
            })
            .then(response => response.json())
            .then(data => {
                if (data.response) {
                    addMessage(data.response, "bot");
                } else {
                    addMessage("⚠️ لم أتمكن من توليد رد.", "error");
                }
            })
            .catch(error => {
                console.error("Error:", error);
                addMessage("⚠️ فشل الاتصال بالخادم!", "error");
            })
            .finally(() => {
                isWaitingForResponse = false;
                userInput.disabled = false;
                sendBtn.disabled = false;
                loadingDiv.style.display = "none";
                userInput.focus();
            });
        }
    });

    userInput.addEventListener("keypress", (event) => {
        if (isWaitingForResponse) {
            event.preventDefault(); 
        } else if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendBtn.click();
        }
    });
}

// دالة تحميل المحادثات السابقة
function loadChatHistory() {
    const chatBox = document.getElementById("chat-box");
    const chatHistory = JSON.parse(localStorage.getItem("chatHistory")) || [];
    chatHistory.forEach(chat => {
        const messageDiv = document.createElement("div");
        messageDiv.className = `${chat.sender}-message chat-bubble ${chat.sender === "user" ? "right" : "left"}`;
        messageDiv.innerHTML = chat.message;
        chatBox.appendChild(messageDiv);
    });
    chatBox.scrollTop = chatBox.scrollHeight;
}

// دالة إضافة الرسالة
function addMessage(text, className, align) {
    const chatBox = document.getElementById("chat-box");
    const messageDiv = document.createElement("div");
    messageDiv.className = `${className} chat-bubble ${align}`;
    messageDiv.innerHTML = text;
    chatBox.appendChild(messageDiv);
    scrollToBottom();
    saveMessageToLocalStorage(text, className); // 🔹 حفظ المحادثة
}

// دالة للتمرير لآخر الرسائل
function scrollToBottom() {
    const chatBox = document.getElementById("chat-box");
    chatBox.scrollTop = chatBox.scrollHeight;
}
