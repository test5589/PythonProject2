"""
log_viewer.py - 查看歷史日誌

這是一個獨立的工具程式，用於查看日誌文件。
✅ 可以獨立運行：python modules/utils/tools/log_viewer.py

⚠️ 注意：這不是主程式入口
主程式入口：python core/gui_main.py
"""
import os

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "logs"))

def view_logs(keyword=None, tail=30):
    files = sorted(os.listdir(LOG_DIR))
    if not files:
        print("❌ 無任何日誌檔。"); return
    latest = os.path.join(LOG_DIR, files[-1])
    print(f"📜 查看日誌: {latest}\n")

    with open(latest, "r", encoding="utf-8") as f:
        lines = f.readlines()[-tail:]
        for l in lines:
            if not keyword or keyword.lower() in l.lower():
                print(l.strip())

if __name__ == "__main__":
    view_logs()
