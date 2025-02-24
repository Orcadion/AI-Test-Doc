import sqlite3
from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
from waitress import serve
from flask_session import Session

# 🔑 تحميل مفتاح API
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("❌ مفتاح API مفقود! تأكد من إضافته في ملف .env")

# 🚀 إعداد التطبيق
app = Flask(__name__)
CORS(app)

# ✅ إعدادات الجلسة
app.secret_key = os.urandom(24)  # مفتاح سري للجلسات
app.config['SESSION_TYPE'] = 'filesystem'  # تخزين الجلسات في ملفات
app.config['SESSION_PERMANENT'] = False    # الجلسة لا تنتهي بعد غلق المتصفح
app.config['SESSION_USE_SIGNER'] = True    # توقيع الجلسة لمزيد من الأمان
app.config['SESSION_FILE_DIR'] = "./flask_session"  # مجلد لتخزين ملفات الجلسات
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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT message, response FROM chats WHERE user = ? ORDER BY timestamp ASC", (user,))
    chats = cursor.fetchall()
    conn.close()
    return [{"message": msg, "response": resp} for msg, resp in chats]

# 🔹 دالة للحصول على user_id من الجلسة
def get_user_id():
    if 'user_id' not in session:
        session['user_id'] = os.urandom(8).hex()  # مُعرّف فريد لكل مستخدم
        session.modified = True  # تأكيد حفظ الجلسة
    return session['user_id']

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

    context += f"أنت: {user_message}\nمساعد: "

    # ✅ بناء البيانات بالطريقة الصحيحة
    data = {
        "contents": [{
            "parts": [{"text": f"تصرف كأنك صديق . المحادثة السابقة كانت: {context}"}]
        }]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()
        
        # ✅ استخراج الرد بطريقة صحيحة
        if "candidates" in response_data and len(response_data["candidates"]) > 0:
            return response_data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return "❌ لم أتمكن من توليد رد."
    except Exception as e:
        print(f"❌ خطأ أثناء طلب `Gemini API`: {e}")
        return "❌ حدث خطأ أثناء معالجة الطلب."

# 🔹 نقطة نهاية لاسترجاع المحادثات السابقة عند تحميل الصفحة
@app.route('/get_history', methods=['GET'])
def get_history():
    user_id = get_user_id()
    chat_history = get_chat_history(user_id)
    return jsonify(chat_history)

# 🔹 نقطة نهاية لإرسال الرسائل
@app.route('/send', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        user_id = get_user_id()
        message = data.get("message", "").strip()

        if not message:
            return jsonify({"error": "❌ الرسالة فارغة!"}), 400

        chat_history = get_chat_history(user_id)
        response_text = generate_gemini_response(message, chat_history)

        if not response_text or response_text.strip() == "":
            response_text = "❌ لم أتمكن من توليد رد."

        save_chat(user_id, message, response_text)
        return jsonify({"response": response_text})

    except Exception as e:
        print(f"❌ خطأ أثناء معالجة الطلب: {e}")
        return jsonify({"error": "❌ حدث خطأ أثناء معالجة الطلب"}), 500

# 🔹 نقطة نهاية لتحميل الملفات الثابتة
@app.route('/')
def home():
    return send_from_directory(os.getcwd(), 'index.html')

@app.route('/script.js')
def script():
    return send_from_directory(os.getcwd(), 'script.js')

@app.route('/styles.css')
def styles():
    return send_from_directory(os.getcwd(), 'styles.css')

# 🚀 تشغيل السيرفر
if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=5000)
