import sqlite3

# 檢查 trading_bot.db
print("=== trading_bot.db ===")
try:
    conn = sqlite3.connect('data/trading_bot.db')
    tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print(f"Tables: {tables}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")

print("\n=== system_data.db ===")
try:
    conn = sqlite3.connect('data/system_data.db')
    tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print(f"Tables: {tables}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
