import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
from waitress import serve  # ✅ استيراد Waitress

# تحميل مفتاح API
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("❌ مفتاح API مفقود! تأكد من إضافته في ملف .env")

# إعداد التطبيق
app = Flask(__name__)
CORS(app)

DB_PATH = "chat_history.db"

# 🔹 تهيئة قاعدة البيانات
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            message TEXT NOT NULL,
            response TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

@app.route('/chat_history', methods=['POST'])
def chat_history():
    try:
        data = request.get_json()
        user = data.get("user", "").strip()

        if not user:
            return jsonify({"error": "❌ اسم المستخدم مطلوب!"}), 400

        history = get_chat_history(user)
        return jsonify({"history": history})

    except Exception as e:
        print(f"❌ خطأ أثناء جلب المحادثات السابقة: {e}")
        return jsonify({"error": "❌ حدث خطأ أثناء جلب المحادثات"}), 500

# 🔹 دالة لحفظ المحادثة
def save_chat(user, message, response):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chats (user, message, response) VALUES (?, ?, ?)", (user, message, response))
    conn.commit()
    conn.close()

# 🔹 دالة لاسترجاع المحادثات السابقة
def get_chat_history(user):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT message, response FROM chats WHERE user = ? ORDER BY timestamp ASC", (user,))
    chats = cursor.fetchall()
    conn.close()
    return [{"message": msg, "response": resp} for msg, resp in chats]

# 🔹 دالة للتحقق من وجود المستخدم
def get_user(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

# 🔹 دالة لحفظ المستخدم
def save_user(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
    conn.commit()
    conn.close()

# 🔹 نقطة نهاية لحفظ المستخدم
@app.route('/set_user', methods=['POST'])
def set_user():
    data = request.get_json()
    username = data.get("username", "").strip()

    if not username:
        return jsonify({"error": "❌ اسم المستخدم مطلوب!"}), 400

    save_user(username)
    return jsonify({"message": f"✅ تم حفظ اسم المستخدم: {username}"})

# 🔹 نقطة نهاية الدردشة
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user = data.get("user", "").strip()
        message = data.get("message", "").strip()

        if not message:
            return jsonify({"error": "❌ الرسالة فارغة!"}), 400

        # 🔹 التحقق من حفظ المستخدم
        if user:
            save_user(user)

        # 🔹 تحليل الرسالة لمعرفة ما إذا كان المستخدم يعرّف اسمه
        if "اسمي" in message:
            words = message.split()
            if len(words) > 2:
                username = words[-1]  # يفترض أن الاسم آخر كلمة في الجملة
                save_user(username)
                return jsonify({"response": f"مرحباً {username}! تم حفظ اسمك.", "history": get_chat_history(user)})

        # 🔥 إرسال الطلب إلى `Gemini API`
        response_text = generate_gemini_response(message)

        # 🔹 حفظ المحادثة
        save_chat(user, message, response_text)

        return jsonify({"response": response_text, "history": get_chat_history(user)})

    except Exception as e:
        print(f"❌ خطأ أثناء معالجة الطلب: {e}")
        return jsonify({"error": "❌ حدث خطأ أثناء معالجة الطلب"}), 500

# 🔹 دالة إرسال الطلب إلى `Gemini API`
def generate_gemini_response(user_message):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": user_message}]}]}

    try:
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()

        if "candidates" in response_data and response_data["candidates"]:
            return response_data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return "❌ لم أتمكن من توليد رد."

    except Exception as e:
        print(f"❌ خطأ أثناء طلب `Gemini API`: {e}")
        return "❌ حدث خطأ أثناء معالجة الطلب."

# ✅ تشغيل السيرفر باستخدام Waitress
if __name__ == '__main__':
    print("🚀 تشغيل السيرفر باستخدام `Waitress`...")
    app.run(host='0.0.0.0', port=8080)
