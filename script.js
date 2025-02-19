let isWaitingForResponse = false;
let username = localStorage.getItem("username") || "User";

document.addEventListener("DOMContentLoaded", async () => {
    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");

    let isWaitingForResponse = false;
    let username = localStorage.getItem("username") || "User";

    // 🔹 دالة لإضافة الرسائل بتنسيق الفقاعات
    function addMessage(text, isUser) {
        if (!text) return; // منع إضافة رسائل فارغة

        const messageDiv = document.createElement("div");
        messageDiv.classList.add("chat-bubble", isUser ? "user-message" : "bot-message");
        messageDiv.textContent = text;

        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight; // تمرير للأحدث تلقائيًا
    }

    // 🔹 تحميل المحادثات السابقة عند فتح الصفحة
    async function loadChatHistory() {
        try {
            const response = await fetch("http://127.0.0.1:5000/chat_history", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user: username })
            });

            const data = await response.json();
            if (data.history && data.history.length > 0) {
                data.history.forEach(chat => {
                    addMessage(chat.message, true);  // رسائل المستخدم باللون الأزرق
                    addMessage(chat.response, false); // ردود الذكاء الاصطناعي باللون الرمادي
                });
            } else {
                console.log("🚀 لا توجد محادثات سابقة");
            }
        } catch (error) {
            console.error("❌ خطأ في تحميل المحادثة:", error);
        }
    }

    // 🔹 إرسال الرسالة عند الضغط على زر الإرسال
    sendBtn.addEventListener("click", sendMessage);
    
    // 🔹 إرسال الرسالة عند الضغط على "Enter"
    userInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !isWaitingForResponse) {
            sendMessage();
        }
    });

    // 🔹 دالة إرسال الرسالة إلى السيرفر ومعالجة الرد
    async function sendMessage() {
        if (isWaitingForResponse) return;

        let message = userInput.value.trim();
        if (!message) return;

        addMessage(message, true); // عرض رسالة المستخدم في الفقاعة الزرقاء
        userInput.value = "";
        isWaitingForResponse = true;
        toggleSendButton(true);

        try {
            const response = await fetch("http://127.0.0.1:5000/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user: username, message })
            });

            const data = await response.json();
            if (data.response) {
                addMessage(data.response, false); // عرض رد الذكاء الاصطناعي في الفقاعة الرمادية
            }
        } catch (error) {
            addMessage("⚠️ فشل الاتصال بالخادم!", false);
            console.error("❌ خطأ في الاتصال بالسيرفر:", error);
        } finally {
            isWaitingForResponse = false;
            toggleSendButton(false);
        }
    }

    // 🔹 تعطيل أو تفعيل زر الإرسال أثناء انتظار الرد
    function toggleSendButton(isWaiting) {
        sendBtn.disabled = isWaiting;
        sendBtn.innerText = isWaiting ? "انتظر..." : "إرسال";
    }

    // 🔹 تحميل المحادثة عند فتح الصفحة
    await loadChatHistory();
});




function handleKeyDown(event) {
    if (event.key === "Enter" && !isWaitingForResponse) {
        sendMessage();
    }
}

function sendMessage() {
    if (isWaitingForResponse) return;

    const userInput = document.getElementById("user-input");
    let message = userInput.value.trim();
    if (message === "") return;

    userInput.value = "";
    userInput.disabled = true; // منع المستخدم من الكتابة أثناء معالجة الرد
    toggleSendButton(true);
    
    addMessage(message, "user-message", "right");

    fetch("http://127.0.0.1:5000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user: username, message: message })
    })
    .then(response => response.json())
    .then(data => {
        if (data.response.includes("تم حفظ اسمك")) {
            username = data.response.split(" ")[1]; // استخراج الاسم
            localStorage.setItem("username", username);
        }
        addMessage(data.response, "bot-message", "left");
    })
    .catch(() => {
        addMessage("⚠️ فشل الاتصال بالخادم!", "error-message", "left");
    })
    .finally(() => {
        isWaitingForResponse = false;
        userInput.disabled = false;
        userInput.focus(); // إبقاء المؤشر في مربع الإدخال بعد الرد
        toggleSendButton(false);
    });
}

function toggleSendButton(isWaiting) {
    const button = document.getElementById("send-button");
    button.disabled = isWaiting;
    button.innerText = isWaiting ? "انتظر..." : "إرسال";
}

function addMessage(text, className, align) {
    const chatBox = document.getElementById("chat-box");
    const messageDiv = document.createElement("div");
    messageDiv.className = `${className} chat-bubble ${align}`;
    messageDiv.innerHTML = text;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function loadChatHistory() {
    fetch("http://127.0.0.1:5000/chat?user=" + username)
        .then(response => response.json())
        .then(data => {
            data.history.forEach(chat => {
                addMessage(chat.message, "user-message", "right");
                addMessage(chat.response, "bot-message", "left");
            });
        });
}
document.addEventListener("DOMContentLoaded", function () {
    const chatBox = document.getElementById("chat-box");
    const username = localStorage.getItem("username") || "default_user"; // استرجاع اسم المستخدم

    // 🔹 جلب المحادثات السابقة عند تحميل الصفحة
    fetch("http://localhost:5000/chat_history", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ user: username })
    })
    .then(response => response.json())
    .then(data => {
        if (data.history) {
            data.history.forEach(chat => {
                appendMessage("user", chat.message);
                appendMessage("ai", chat.response);
            });
        }
    })
    .catch(error => console.error("❌ فشل تحميل المحادثات السابقة:", error));
});

// 🔹 دالة إضافة الرسائل إلى المحادثة
function appendMessage(sender, text) {
    const chatBox = document.getElementById("chat-box");
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender);
    messageDiv.textContent = text;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}
document.addEventListener("DOMContentLoaded", function () {
    loadChatHistory();
});

function sendMessage() {
    let userInput = document.getElementById("user-input").value.trim();
    if (!userInput) return;

    displayMessage(userInput, "user-message"); // عرض رسالتك باللون الأزرق

    fetch("http://127.0.0.1:5000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user: "user", message: userInput }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.response) {
            displayMessage(data.response, "ai-message"); // عرض رد الذكاء الاصطناعي باللون الأبيض
        }
        document.getElementById("user-input").value = ""; // تفريغ الحقل بعد الإرسال
    })
    .catch(error => console.error("❌ حدث خطأ:", error));
}

function displayMessage(text, className) {
    let chatBox = document.getElementById("chat-box");
    let messageDiv = document.createElement("div");
    messageDiv.classList.add("message", className);
    messageDiv.textContent = text;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function loadChatHistory() {
    fetch("http://127.0.0.1:5000/chat_history", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user: "user" }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.history) {
            data.history.forEach(chat => {
                displayMessage(chat.message, "user-message");
                displayMessage(chat.response, "ai-message");
            });
        }
    })
    .catch(error => console.error("❌ خطأ في تحميل المحادثة:", error));
}
document.addEventListener("DOMContentLoaded", () => {
    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    
    function addMessage(text, isUser) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("chat-bubble", isUser ? "user-message" : "bot-message");
        messageDiv.textContent = text;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    sendBtn.addEventListener("click", async () => {
        const message = userInput.value.trim();
        if (!message) return;

        addMessage(message, true);
        userInput.value = "";

        const response = await fetch("http://127.0.0.1:5000/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user: "User", message })
        });

        const data = await response.json();
        if (data.response) addMessage(data.response, false);
    });
});
