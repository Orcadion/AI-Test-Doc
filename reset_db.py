import sqlite3

# مسح وإعادة إنشاء قاعدة البيانات
db_path = "chat_history.db"

# الاتصال بقاعدة البيانات
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# حذف الجداول القديمة إذا كانت موجودة
cursor.execute("DROP TABLE IF EXISTS chat_history")
cursor.execute("DROP TABLE IF EXISTS user_info")
cursor.execute("DROP TABLE IF EXISTS synonyms")

# إنشاء جدول لتخزين المحادثات
cursor.execute("""
    CREATE TABLE chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_input TEXT NOT NULL,
        bot_response TEXT NOT NULL
    )
""")

# إنشاء جدول لتخزين معلومات المستخدم (مثل الاسم والموقع)
cursor.execute("""
    CREATE TABLE user_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        value TEXT NOT NULL
    )
""")

# إنشاء جدول للمرادفات (لتعليم الذكاء الاصطناعي معاني الكلمات المشابهة)
cursor.execute("""
    CREATE TABLE synonyms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phrase TEXT UNIQUE NOT NULL,
        meaning TEXT NOT NULL
    )
""")

# حفظ التعديلات وإغلاق الاتصال
conn.commit()
conn.close()

print("✅ تم إعادة إنشاء قاعدة البيانات chat_history.db بنجاح!")
