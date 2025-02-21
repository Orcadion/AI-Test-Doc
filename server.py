import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
from waitress import serve
from flask import Flask, send_from_directory
from flask import Flask, render_template, request, jsonify, session
from flask_session import Session

# 🔑 تحميل مفتاح API
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("❌ مفتاح API مفقود! تأكد من إضافته في ملف .env")

# 🚀 إعداد التطبيق
app = Flask(__name__)
CORS(app)
app.secret_key = os.urandom(24)  # مفتاح سري للجلسات
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

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
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 🔹 دالة لحفظ المحادثة
def save_chat(user, message, response):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO chats (user, message, response) VALUES (?, ?, ?)", (user, message, response))
        conn.commit()
    except sqlite3.Error as e:
        print(f"❌ خطأ في قاعدة البيانات: {e}")
    finally:
        conn.close()


# 🔹 دالة لاسترجاع المحادثات السابقة
def get_chat_history(user):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA journal_mode=WAL;')
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
# 🔥 تعديل دالة توليد الرد



# 🔥 دالة الاتصال بـ `Gemini API`
    # 🔥 دالة الاتصال بـ `Gemini API`
def generate_gemini_response(user_message, chat_history=[]):
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    context = ""

    # ✅ إضافة المعرفة المبدئية
    initial_knowledge = """
    - انا اعمل تيست تيكنشن
    """

  
    # دمج المعرفة مع المحادثات السابقة
    for chat in chat_history[-5:]:  # أخذ آخر 5 رسائل فقط للحفاظ على التركيز
        context += f"أنت: {chat['message']}\n"
        context += f"مساعد: {chat['response']}\n"
        context += f"هذه بعض المعلومات المبدئية:\n{initial_knowledge}\n"

    context += f"أنت: {user_message}\nمساعد: "

    # ✅ بناء البيانات بالطريقة الصحيحة
    data = {
        "contents": [{
            "parts": [{"text": f"تصرف كأنك صديق . المحادثة السابقة كانت: {context}"}]
        }]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        
        # 🔍 طباعة استجابة `Gemini API` للتحقق
        print("🌐 Status Code:", response.status_code)
        print("📥 Response:", response.text)

        response_data = response.json()
        
        # ✅ استخراج الرد بطريقة صحيحة
        if "candidates" in response_data and len(response_data["candidates"]) > 0:
            if "content" in response_data["candidates"][0] and \
               "parts" in response_data["candidates"][0]["content"] and \
               len(response_data["candidates"][0]["content"]["parts"]) > 0:
                
                return response_data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                return "❌ لم أتمكن من توليد رد."
        else:
            return "❌❌ لم أتمكن من توليد رد."

    except Exception as e:
        print(f"❌ خطأ أثناء طلب `Gemini API`: {e}")
        return "❌ حدث خطأ أثناء معالجة الطلب."

# 🔹 نقطة نهاية لإرسال الرسالة
# 🔹 نقطة نهاية لإرسال الرسالة
def get_user_id():
    if 'user_id' not in session:
        session['user_id'] = os.urandom(8).hex()  # مُعرّف فريد لكل مستخدم
    return session['user_id']
@app.route('/')
def home():
    # إنشاء معرّف فريد للمستخدم
    get_user_id()  # تأكد من وجود user_id في الجلسة
    return render_template('index.html')

@app.route('/script.js')
def script():
    return send_from_directory(os.getcwd(), 'script.js')

@app.route('/styles.css')
def styles():
    return send_from_directory(os.getcwd(), 'styles.css')

@app.route('/chat_history.db')
def get0_chat_history():
    return send_from_directory(os.getcwd(), 'chat_history.db')

@app.route('/server.py')
def get0_server():
    return send_from_directory(os.getcwd(), 'server.py')


@app.route('/.env')
def get0_env():
    return send_from_directory(os.getcwd(), '.env')


@app.route('/send', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        user_id = get_user_id()  # جلب الـ user_id الفريد من الجلسة
        message = data.get("message", "").strip()

        if not message:
            return jsonify({"error": "❌ الرسالة فارغة!"}), 400

        # 🔹 جلب المحادثات السابقة لهذا المستخدم
        chat_history = get_chat_history(user_id)

        # 🔥 توليد رد من الذكاء الاصطناعي باستخدام السياق
        response_text = generate_gemini_response(message, chat_history)

        # ✅ التأكد من أن الرد ليس فارغًا
        if not response_text or response_text.strip() == "":
            response_text = "❌ لم أتمكن من توليد رد."

        # 🔹 حفظ المحادثة
        save_chat(user_id, message, response_text)

        return jsonify({"response": response_text})

    except Exception as e:
        print(f"❌ خطأ أثناء معالجة الطلب: {e}")
        return jsonify({"error": "❌ حدث خطأ أثناء معالجة الطلب"}), 500

# 🔹 دوال مساعدة لتخزين واسترجاع المحادثات
def save_chat(user_id, message, response):
    # يمكنك تخزين المحادثات في قاعدة بيانات أو في ملف نصي لكل مستخدم
    with open(f"chat_{user_id}.txt", "a", encoding="utf-8") as f:
        f.write(f"User: {message}\nBot: {response}\n")
def get_chat_history(user_id):
    try:
        with open(f"chat_{user_id}.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return
# 🔹 نقطة نهاية لحفظ المعلومات العامة




@app.route('/save_info', methods=['POST'])
def save_info():
    data = request.get_json()
    key = data.get("key", "").strip().lower()
    value = data.get("value", "").strip()

    if not key or not value:
        return jsonify({"error": "❌ يجب إدخال المفتاح والقيمة!"}), 400

    save_general_info(key, value)
    return jsonify({"message": f"✅ تم حفظ المعلومات: {key} = {value}"})



# 🔹 نقطة نهاية لجلب المحادثات السابقة
@app.route('/chat_history', methods=['POST'])
def chat_history():
    data = request.get_json()
    user_message = data.get('message')
    # هنا ضع منطق الذكاء الاصطناعي للرد
    response = {"reply": "تم استقبال رسالتك: " + user_message}
    return jsonify(response)

# 🔹 دالة لحفظ المعلومات العامة
def save_general_info(key, value):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS general_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL
        )
    ''')
    cursor.execute("INSERT OR REPLACE INTO general_info (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()
# 🔹 دالة لاسترجاع المعلومات العامة
def get_general_info(key):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM general_info WHERE key = ?", (key,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# 🚀 تشغيل السيرفر
if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=5000)
