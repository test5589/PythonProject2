import sqlite3
import os

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "system_data.db"))
print(f"🔍 資料庫路徑: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("\n=== 資料表清單 ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for t in tables:
    print("📄", t[0])

# 顯示每個資料表的前幾筆資料
for t in tables:
    print(f"\n=== {t[0]} 表格的前5筆資料 ===")
    try:
        cursor.execute(f"SELECT * FROM {t[0]} LIMIT 5;")
        rows = cursor.fetchall()
        for r in rows:
            print(r)
    except Exception as e:
        print(f"⚠️ 無法讀取：{e}")

conn.close()


