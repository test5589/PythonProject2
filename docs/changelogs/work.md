想要添加的文件

modules/api_weight_evaluator.py

內容如下:
"""api_weight_evaluator.py - API 權重測試與被鎖紀錄系統 (依據用戶原始邏輯)"""
import json
import os
import time
from datetime import datetime, timezone, timedelta

# === 紀錄檔路徑 ===
DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
RECORD_FILE = os.path.join(DATA_PATH, "api_weight_records.json")
LOG_FILE = os.path.join(DATA_PATH, "api_weight_log.txt")

# 六個時間框架
TIMEFRAMES = ["1m", "3m", "5m", "10m", "30m", "1h"]

# === 寫入日誌 ===
def _log(msg):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}] {msg}"
    print(line)
    os.makedirs(DATA_PATH, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# === 初始資料 ===
def _default_state():
    return {
        "weight": 1.0,
        "base_count": 2000,
        "lock_records": [],      # 每次被鎖紀錄
        "lock_times": 0,         # 連續被鎖次數
        "unlock_times": 0,       # 解鎖次數
        "last_lock_time": None,
        "last_unlock_time": None,
        "status": "normal"
    }


def _load_records():
    if os.path.exists(RECORD_FILE):
        try:
            with open(RECORD_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {tf: _default_state() for tf in TIMEFRAMES}


def _save_records(data):
    os.makedirs(DATA_PATH, exist_ok=True)
    with open(RECORD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# === 主控制類 ===
class APIWeightEvaluator:
    def __init__(self):
        self.records = _load_records()

    def get_state(self, tf):
        return self.records.get(tf, _default_state())

    # ========== (一) 權重循環：被鎖邏輯 ==========
    def mark_lock(self, tf: str, detected_count: int):
        """
        當 IP 被鎖時呼叫，依據當前筆數與循環狀態調整權重與筆數。
        """
        state = self.get_state(tf)
        w = state["weight"]
        base = state["base_count"]
        state["lock_times"] += 1
        lock_n = state["lock_times"]

        _log(f"⚠️ [{tf}] 第 {lock_n} 次被鎖觸發。當前筆數={detected_count}, 權重={w:.2f}")

        # 第一循環參數
        loss_table = [0.2, 0.15, 0.10]  # 依次扣除比例
        idx = (lock_n - 1) % len(loss_table)
        loss = loss_table[idx]

        # 若超過3次重複，回復成0.2
        if lock_n > 3:
            loss = 0.2

        # 更新筆數
        new_count = round(base * (1 - loss))
        state["base_count"] = new_count

        # 權重變化：被鎖減少 loss，之後恢復再加 (loss - 0.01)
        old_w = w
        w = round(max(0.0, w - loss), 3)
        state["weight"] = w

        # 紀錄
        lock_record = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "loss": loss,
            "old_weight": old_w,
            "new_weight": w,
            "new_count": new_count
        }
        state["lock_records"].append(lock_record)
        state["last_lock_time"] = lock_record["time"]
        state["status"] = "locked"
        _log(f"🔒 [{tf}] 扣除 {loss*100:.0f}% 筆數 → {new_count}, 權重 {old_w:.2f} → {w:.2f}")

        # 若連續5次被鎖 → 觸發第二循環
        if state["lock_times"] >= 5:
            self._trigger_second_cycle(tf)

        self.records[tf] = state
        _save_records(self.records)

    # ========== (一延伸) 解鎖回復 ==========
    def mark_unlock(self, tf: str):
        """
        當 IP 解鎖時呼叫，依照最後一次扣除比例恢復權重。
        """
        state = self.get_state(tf)
        if not state["lock_records"]:
            _log(f"ℹ️ [{tf}] 無鎖定紀錄可恢復。")
            return

        last = state["lock_records"][-1]
        loss = last["loss"]

        old_w = state["weight"]
        plus = round(loss - 0.01, 3)
        new_w = round(min(1.2, old_w + plus), 3)
        state["weight"] = new_w
        state["lock_times"] = 0
        state["unlock_times"] += 1
        state["last_unlock_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        state["status"] = "unlocked"

        _log(f"🔓 [{tf}] 解鎖恢復：+{plus} → 權重 {old_w:.2f} → {new_w:.2f}")

        self.records[tf] = state
        _save_records(self.records)

    # ========== (二) 第二循環邏輯 ==========
    def _trigger_second_cycle(self, tf: str):
        """
        當第一循環滿5次鎖定時，啟動平均補償循環。
        """
        state = self.get_state(tf)
        locks = state["lock_records"][-5:]
        if not locks:
            _log(f"❌ [{tf}] 無鎖定紀錄，無法進入第二循環。")
            return

        loss_sum = sum([r["loss"] for r in locks])
        avg_loss = loss_sum / len(locks)

        # 公式計算：
        # X = avg_loss * 0.312
        # Y = (Σ扣除筆數 / 5) * X
        X = round(avg_loss * 0.312, 5)
        total_lost = sum([r["loss"] * state["base_count"] for r in locks])
        Y = round((total_lost / len(locks)) * X)

        old_w = state["weight"]
        new_w = round(old_w + X, 3)
        new_count = state["base_count"] + Y

        _log(f"🧠 [{tf}] 第二循環計算：平均loss={avg_loss:.3f}, X={X}, Y={Y}")
        _log(f"🔁 [{tf}] 權重 {old_w:.3f} → {new_w:.3f}, 筆數 {state['base_count']} → {new_count}")

        state["weight"] = new_w
        state["base_count"] = new_count
        state["lock_times"] = 0
        state["status"] = "second_cycle"

        # 條件判斷
        if new_w >= 1:
            _log(f"✅ [{tf}] 第二循環完成，權重恢復正常 ({new_w})。")
            state["status"] = "normal"
        elif new_w < 0.81:
            _log(f"⛔ [{tf}] 權重過低 ({new_w})，中止所有動作並提醒用戶。")
            state["status"] = "halted"

        self.records[tf] = state
        _save_records(self.records)

    # ========== (三) 顯示狀態 ==========
    def show_all(self):
        for tf, s in self.records.items():
            _log(f"[{tf}] 狀態={s['status']}, 權重={s['weight']:.3f}, 筆數={s['base_count']}, 鎖={s['lock_times']}, 解鎖={s['unlock_times']}")

    # ========== (四) 重置特定 timeframe ==========
    def reset(self, tf: str):
        self.records[tf] = _default_state()
        _save_records(self.records)
        _log(f"♻️ [{tf}] 已重置狀態。")


# =============== 測試區域 ===============
if __name__ == "__main__":
    eva = APIWeightEvaluator()
    tf = "1m"

    # 模擬被鎖
    eva.mark_lock(tf, detected_count=7584)
    eva.mark_unlock(tf)
    eva.mark_lock(tf, detected_count=6067)
    eva.mark_unlock(tf)
    eva.mark_lock(tf, detected_count=5157)
    eva.mark_unlock(tf)
    eva.mark_lock(tf, detected_count=4641)
    eva.mark_unlock(tf)
    eva.mark_lock(tf, detected_count=4000)  # 觸發第二循環
    eva.show_all()

