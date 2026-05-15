"""api_weight_evaluator.py - API 權重測試與被鎖紀錄系統 (依據用戶原始邏輯)"""

import json
import os
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from contextlib import contextmanager

from modules.utils.logger import get_logger

logger = get_logger("api_weight")

# === 紀錄檔路徑 ===
DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
RECORD_FILE = os.path.join(DATA_PATH, "api_weight_records.json")
LOG_FILE = os.path.join(DATA_PATH, "api_weight_log.txt")

# 六個時間框架
TIMEFRAMES = ["1m", "3m", "5m", "10m", "30m", "1h"]

# === 資料結構 ===
@dataclass
class LockRecord:
    """鎖定紀錄"""
    time: str
    loss: float
    old_weight: float
    new_weight: float
    new_count: int
    detected_count: int

@dataclass
class TimeframeState:
    """時間框架狀態"""
    weight: float = 1.0
    base_count: int = 2000
    lock_records: List[LockRecord] = None
    lock_times: int = 0
    unlock_times: int = 0
    last_lock_time: Optional[str] = None
    last_unlock_time: Optional[str] = None
    status: str = "normal"  # normal, locked, unlocked, second_cycle, halted
    
    def __post_init__(self):
        if self.lock_records is None:
            self.lock_records = []

# === 寫入日誌 ===
def _log(msg: str):
    """寫入日誌檔"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}] {msg}"
    print(line)
    os.makedirs(DATA_PATH, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# === 檔案操作 ===
def _ensure_data_dir():
    """確保資料目錄存在"""
    os.makedirs(DATA_PATH, exist_ok=True)


def _load_records() -> Dict[str, TimeframeState]:
    """載入紀錄檔"""
    if os.path.exists(RECORD_FILE):
        try:
            with open(RECORD_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                result = {}
                for tf, state_dict in data.items():
                    # 轉換 lock_records 為 LockRecord 物件
                    lock_records = []
                    for lr in state_dict.get("lock_records", []):
                        lock_records.append(LockRecord(**lr))
                    state_dict["lock_records"] = lock_records
                    result[tf] = TimeframeState(**state_dict)
                return result
        except Exception as e:
            logger.error(f"載入權重紀錄失敗: {e}")
    return {tf: TimeframeState() for tf in TIMEFRAMES}


def _save_records(records: Dict[str, TimeframeState]):
    """儲存紀錄檔"""
    _ensure_data_dir()
    try:
        data = {}
        for tf, state in records.items():
            state_dict = asdict(state)
            # 轉換 LockRecord 物件為字典
            lock_records = []
            for lr in state.lock_records:
                lock_records.append(asdict(lr))
            state_dict["lock_records"] = lock_records
            data[tf] = state_dict
        
        with open(RECORD_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"儲存權重紀錄失敗: {e}")


# === 主控制類 ===
class APIWeightEvaluator:
    """API 權重評估器"""
    
    def __init__(self):
        self.records = _load_records()
        self._lock = threading.Lock()
    
    def get_state(self, tf: str) -> TimeframeState:
        """取得時間框架狀態"""
        with self._lock:
            return self.records.get(tf, TimeframeState())
    
    def get_optimal_count(self, tf: str) -> int:
        """取得建議的抓取筆數"""
        state = self.get_state(tf)
        if state.status == "halted":
            raise ValueError(f"時間框架 {tf} 權重過低，已中止操作")
        return state.base_count
    
    def get_weight(self, tf: str) -> float:
        """取得目前權重值"""
        state = self.get_state(tf)
        return state.weight
    
    def is_halted(self, tf: str) -> bool:
        """檢查是否已中止"""
        state = self.get_state(tf)
        return state.status == "halted"
    
    # ========== (一) 權重循環：被鎖邏輯 ==========
    def mark_lock(self, tf: str, detected_count: int):
        """
        當 IP 被鎖時呼叫，依據當前筆數與循環狀態調整權重與筆數。
        
        Args:
            tf: 時間框架
            detected_count: 偵測到的筆數
        """
        with self._lock:
            state = self.get_state(tf)
            w = state.weight
            base = state.base_count
            state.lock_times += 1
            lock_n = state.lock_times

            _log(f"⚠️ [{tf}] 第 {lock_n} 次被鎖觸發。當前筆數={detected_count}, 權重={w:.2f}")

            # 第一循環參數
            loss_table = [0.2, 0.15, 0.10]  # 依次扣除比例
            idx = min(lock_n - 1, len(loss_table) - 1)
            loss = loss_table[idx]

            # 若超過3次重複，回復成0.2
            if lock_n > 3:
                loss = 0.2

            # 更新筆數
            new_count = round(base * (1 - loss))
            state.base_count = new_count

            # 權重變化：被鎖減少 loss
            old_w = w
            w = round(max(0.0, w - loss), 3)
            state.weight = w

            # 紀錄
            lock_record = LockRecord(
                time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                loss=loss,
                old_weight=old_w,
                new_weight=w,
                new_count=new_count,
                detected_count=detected_count
            )
            state.lock_records.append(lock_record)
            state.last_lock_time = lock_record.time
            state.status = "locked"
            
            _log(f"🔒 [{tf}] 扣除 {loss*100:.0f}% 筆數 → {new_count}, 權重 {old_w:.2f} → {w:.2f}")

            # 若連續5次被鎖 → 觸發第二循環
            if state.lock_times >= 5:
                self._trigger_second_cycle(tf)

            self.records[tf] = state
            _save_records(self.records)
    
    # ========== (一延伸) 解鎖回復 ==========
    def mark_unlock(self, tf: str):
        """
        當 IP 解鎖時呼叫，依照最後一次扣除比例恢復權重。
        
        Args:
            tf: 時間框架
        """
        with self._lock:
            state = self.get_state(tf)
            if not state.lock_records:
                _log(f"ℹ️ [{tf}] 無鎖定紀錄可恢復。")
                return

            last = state.lock_records[-1]
            loss = last.loss

            old_w = state.weight
            plus = round(loss - 0.01, 3)
            new_w = round(min(1.2, old_w + plus), 3)
            state.weight = new_w
            state.lock_times = 0
            state.unlock_times += 1
            state.last_unlock_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            state.status = "unlocked"

            _log(f"🔓 [{tf}] 解鎖恢復：+{plus} → 權重 {old_w:.2f} → {new_w:.2f}")

            self.records[tf] = state
            _save_records(self.records)
    
    # ========== (二) 第二循環邏輯 ==========
    def _trigger_second_cycle(self, tf: str):
        """
        當第一循環滿5次鎖定時，啟動平均補償循環。
        
        Args:
            tf: 時間框架
        """
        state = self.get_state(tf)
        locks = state.lock_records[-5:]
        if not locks:
            _log(f"❌ [{tf}] 無鎖定紀錄，無法進入第二循環。")
            return

        loss_sum = sum([r.loss for r in locks])
        avg_loss = loss_sum / len(locks)

        # 公式計算：
        # X = avg_loss * 0.312
        # Y = (Σ扣除筆數 / 5) * X
        X = round(avg_loss * 0.312, 5)
        total_lost = sum([r.loss * state.base_count for r in locks])
        Y = round((total_lost / len(locks)) * X)

        old_w = state.weight
        new_w = round(old_w + X, 3)
        new_count = state.base_count + Y

        _log(f"🧠 [{tf}] 第二循環計算：平均loss={avg_loss:.3f}, X={X}, Y={Y}")
        _log(f"🔁 [{tf}] 權重 {old_w:.3f} → {new_w:.3f}, 筆數 {state.base_count} → {new_count}")

        state.weight = new_w
        state.base_count = new_count
        state.lock_times = 0
        state.status = "second_cycle"

        # 條件判斷
        if new_w >= 1:
            _log(f"✅ [{tf}] 第二循環完成，權重恢復正常 ({new_w})。")
            state.status = "normal"
        elif new_w < 0.81:
            _log(f"⛔ [{tf}] 權重過低 ({new_w})，中止所有動作並提醒用戶。")
            state.status = "halted"

        self.records[tf] = state
        _save_records(self.records)
    
    # ========== (三) 狀態管理 ==========
    def show_all(self):
        """顯示所有時間框架狀態"""
        _log("=== API 權重評估狀態 ===")
        for tf, s in self.records.items():
            _log(f"[{tf}] 狀態={s.status}, 權重={s.weight:.3f}, 筆數={s.base_count}, "
                 f"鎖={s.lock_times}, 解鎖={s.unlock_times}")
    
    def reset(self, tf: str):
        """重置特定時間框架"""
        with self._lock:
            self.records[tf] = TimeframeState()
            _save_records(self.records)
            _log(f"[RESET] [{tf}] 已重置狀態。")
    
    def reset_all(self):
        """重置所有時間框架"""
        with self._lock:
            for tf in TIMEFRAMES:
                self.records[tf] = TimeframeState()
            _save_records(self.records)
            _log(f"[RESET] 已重置所有時間框架狀態。")
    
    # ========== (四) 統計資訊 ==========
    def get_statistics(self, tf: str) -> Dict:
        """取得統計資訊"""
        state = self.get_state(tf)
        recent_locks = state.lock_records[-10:]  # 最近10次
        
        return {
            "timeframe": tf,
            "status": state.status,
            "weight": state.weight,
            "base_count": state.base_count,
            "total_locks": len(state.lock_records),
            "unlock_times": state.unlock_times,
            "last_lock": state.last_lock_time,
            "last_unlock": state.last_unlock_time,
            "recent_locks": [asdict(lr) for lr in recent_locks]
        }
    
    def get_all_statistics(self) -> Dict[str, Dict]:
        """取得所有時間框架統計"""
        return {tf: self.get_statistics(tf) for tf in TIMEFRAMES}
    
    # ========== (五) 上下文管理器 ==========
    @contextmanager
    def api_request_context(self, tf: str, requested_count: int):
        """
        API 請求上下文管理器，自動處理鎖定偵測
        
        Args:
            tf: 時間框架
            requested_count: 請求的筆數
        """
        try:
            yield self.get_optimal_count(tf)
        except Exception as e:
            # 偵測是否為 IP 被鎖錯誤
            if "429" in str(e) or "rate limit" in str(e).lower():
                self.mark_lock(tf, requested_count)
                raise
            else:
                raise


# === 全域實例 ===
_global_evaluator: Optional[APIWeightEvaluator] = None
_evaluator_lock = threading.Lock()


def get_api_weight_evaluator() -> APIWeightEvaluator:
    """取得全域權重評估器（單例模式）"""
    global _global_evaluator
    
    with _evaluator_lock:
        if _global_evaluator is None:
            _global_evaluator = APIWeightEvaluator()
        return _global_evaluator


# === 便捷函數 ===
def mark_api_lock(tf: str, detected_count: int):
    """標記 API 被鎖"""
    evaluator = get_api_weight_evaluator()
    evaluator.mark_lock(tf, detected_count)


def mark_api_unlock(tf: str):
    """標記 API 解鎖"""
    evaluator = get_api_weight_evaluator()
    evaluator.mark_unlock(tf)


def get_optimal_request_count(tf: str) -> int:
    """取得建議請求筆數"""
    evaluator = get_api_weight_evaluator()
    return evaluator.get_optimal_count(tf)


def is_api_halted(tf: str) -> bool:
    """檢查 API 是否已中止"""
    evaluator = get_api_weight_evaluator()
    return evaluator.is_halted(tf)


# =============== 測試區域 ===============
if __name__ == "__main__":
    evaluator = APIWeightEvaluator()
    tf = "1m"

    # 模擬被鎖
    evaluator.mark_lock(tf, detected_count=7584)
    evaluator.mark_unlock(tf)
    evaluator.mark_lock(tf, detected_count=6067)
    evaluator.mark_unlock(tf)
    evaluator.mark_lock(tf, detected_count=5157)
    evaluator.mark_unlock(tf)
    evaluator.mark_lock(tf, detected_count=4641)
    evaluator.mark_unlock(tf)
    evaluator.mark_lock(tf, detected_count=4000)  # 觸發第二循環
    evaluator.show_all()
    
    # 測試上下文管理器
    print("\n=== 測試上下文管理器 ===")
    try:
        with evaluator.api_request_context("1m", 5000) as count:
            print(f"建議請求筆數: {count}")
    except Exception as e:
        print(f"API 請求失敗: {e}")
