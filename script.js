let isWaitingForResponse = false;
let username = localStorage.getItem("username") || "User";

document.addEventListener("DOMContentLoaded", () => {
    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");

    fetch('https://ai-test-doc.onrender.com/chat_history', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: userMessage })
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
    if (isWaitingForResponse) return; // منع الإرسال إذا كان هناك رد قيد الانتظار

    const serverUrl = "http://127.0.0.1:5000/send"; // تعديل المسار ليتوافق مع السيرفر
    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const loadingDiv = document.getElementById("loading");
    
    let isWaitingForResponse = false;
    
    window.onload = function() {
        const savedChat = localStorage.getItem("chatHistory");
        if (savedChat) {
            chatBox.innerHTML = savedChat;
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    }
    
    function saveChat() {
        localStorage.setItem("chatHistory", chatBox.innerHTML);
    }
    
    function addMessage(content, sender = "user") {
        const messageBubble = document.createElement("div");
        messageBubble.classList.add("message-bubble", sender);
        messageBubble.innerHTML = content;
        chatBox.appendChild(messageBubble);
        chatBox.scrollTop = chatBox.scrollHeight;
        saveChat();
    }
    
    sendBtn.addEventListener("click", () => {
        if (isWaitingForResponse) return; // منع الإرسال أثناء الانتظار
    
        const message = userInput.value.trim();
        if (message) {
            addMessage(message, "user");
            userInput.value = "";
    
            // تعطيل الكتابة أثناء الانتظار
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
                console.log("Response Data:", data);
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
                // إعادة تفعيل الكتابة بعد استلام الرد
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
            event.preventDefault(); // منع الكتابة أثناء الانتظار
        } else if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendBtn.click();
        }
    });
}
// دالة إضافة الرسالة
function addMessage(text, className, align) {
    const chatBox = document.getElementById("chat-box");
    const messageDiv = document.createElement("div");
    messageDiv.className = `${className} chat-bubble ${align}`;
    messageDiv.innerHTML = text;
    chatBox.appendChild(messageDiv);
    scrollToBottom();
}

// حفظ المحادثات في Local Storage
function saveMessageToLocalStorage(message, sender) {
    let chatHistory = JSON.parse(localStorage.getItem("chatHistory")) || [];
    chatHistory.push({ sender: sender, message: message, timestamp: new Date().toISOString() });
    localStorage.setItem("chatHistory", JSON.stringify(chatHistory));
}

// تحميل المحادثات السابقة
function loadChatHistory() {
    const chatHistory = JSON.parse(localStorage.getItem("chatHistory")) || [];
    chatHistory.forEach(chat => {
        if (chat.sender === "user") {
            addMessage(chat.message, "user-message", "right");
        } else if (chat.sender === "bot") {
            addMessage(chat.message, "bot-message", "left");
        }
    });
}

// تفعيل/إلغاء تفعيل زر الإرسال
function toggleSendButton(isWaiting) {
    const button = document.getElementById("send-btn");
    if (isWaiting) {
        button.disabled = true;
        button.innerText = "انتظر...";
    } else {
        button.disabled = false;
        button.innerText = "إرسال";
    }
}

// دالة للتمرير لآخر الرسائل
function scrollToBottom() {
    const chatBox = document.getElementById("chat-box");
    chatBox.scrollTop = chatBox.scrollHeight;
}
