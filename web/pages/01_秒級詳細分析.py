"""
秒級詳細分析頁面
- 支援 1s/2s/5s/10s/15s/30s 詳細分析
- 連續缺失區塊、破碎時間段、完整時間段視覺化
- 匯出報告功能
"""
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timezone, timedelta
import os
import sys
import importlib

# 加入專案根目錄和當前目錄到路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.append(os.path.dirname(__file__))

import debug_logger as dl  # type: ignore
dl = importlib.reload(dl)
from config.trading_config import TradingConfig

# 使用與 database.py 相同的路徑邏輯
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "system_data.db"))

@st.cache_data(ttl=60, show_spinner=False)
def load_data(symbol: str, interval: int, start_ts: float, end_ts: float) -> pd.DataFrame:
    """載入指定範圍與 interval 的資料（含除錯日誌）"""
    df, error = dl.debug_load_data(symbol, interval, start_ts, end_ts)
    if error:
        st.error(f"載入資料失敗：{error}")
        return pd.DataFrame()
    
    if not df.empty:
        df["readable_time"] = pd.to_datetime(df["timestamp"], unit="s", utc=True).dt.tz_convert("Asia/Taipei")
    return df

@st.cache_data(ttl=60, show_spinner=False)
def generate_time_buckets(start_ts: float, end_ts: float, interval_sec: int) -> pd.DataFrame:
    buckets = []
    ts = start_ts
    while ts < end_ts:
        buckets.append({"timestamp": ts, "has_data": False})
        ts += interval_sec
    return pd.DataFrame(buckets)

def sec_analysis(symbol: str, start_ts: float, end_ts: float, sec_interval: int):
    df = load_data(symbol, sec_interval, start_ts, end_ts)
    if df.empty:
        st.warning(f"無 {sec_interval} 秒資料可分析")
        return
    buckets = generate_time_buckets(start_ts, end_ts, sec_interval)
    buckets["has_data"] = buckets["timestamp"].apply(lambda ts: ts in set(df["timestamp"]))
    # 連續缺失區塊
    missing_runs = []
    in_gap = False
    gap_start = None
    for ts, has in zip(buckets["timestamp"], buckets["has_data"]):
        if not has:
            if not in_gap:
                in_gap = True
                gap_start = ts
        else:
            if in_gap:
                in_gap = False
                missing_runs.append((gap_start, ts - sec_interval))
                gap_start = None
    if in_gap:
        missing_runs.append((gap_start, buckets["timestamp"].iloc[-1]))
    # 最大缺口
    if missing_runs:
        max_gap = max(missing_runs, key=lambda x: x[1] - x[0] + sec_interval)
        st.write(f"🔴 **連續缺失最大區塊**：{datetime.fromtimestamp(max_gap[0], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} ~ {datetime.fromtimestamp(max_gap[1], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}（{(max_gap[1]-max_gap[0]+sec_interval)//sec_interval} 筆）")
        fig_max = go.Figure()
        fig_max.add_trace(go.Bar(
            x=[datetime.fromtimestamp(max_gap[0], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')],
            y=[(max_gap[1]-max_gap[0]+sec_interval)//sec_interval],
            marker_color='red',
            name='最大缺口區塊'
        ))
        fig_max.update_layout(title="最大連續缺失區塊", xaxis_title="時間", yaxis_title="缺失筆數", height=250)
        st.plotly_chart(fig_max, width='stretch')
    else:
        st.success("🟢 無連續缺失區塊")
    # 破碎與完整時間段（每 10 分鐘）
    window = 600
    rates = []
    t = start_ts
    while t + window <= end_ts:
        sub = buckets[(buckets["timestamp"] >= t) & (buckets["timestamp"] < t + window)]
        if not sub.empty:
            rate = (~sub["has_data"]).sum() / len(sub)
            rates.append((t, t + window, rate))
        t += window
    if rates:
        most_fragmented = max(rates, key=lambda x: x[2])
        most_complete = min(rates, key=lambda x: x[2])
        st.write(f"🟠 **最分散破碎時間段**：{datetime.fromtimestamp(most_fragmented[0], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} ~ {datetime.fromtimestamp(most_fragmented[1], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}（缺口率 {most_fragmented[2]*100:.1f}%）")
        st.write(f"🟢 **最完整時間段**：{datetime.fromtimestamp(most_complete[0], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} ~ {datetime.fromtimestamp(most_complete[1], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}（缺口率 {most_complete[2]*100:.1f}%）")
        df_rate = pd.DataFrame(rates, columns=["start", "end", "gap_rate"])
        df_rate["time"] = pd.to_datetime(df_rate["start"], unit="s", utc=True).dt.tz_convert("Asia/Taipei")
        fig = px.bar(df_rate, x="time", y="gap_rate", title="每 10 分鐘缺口率", labels={"gap_rate": "缺口率", "time": "時間（UTC+8）"})
        fig.update_layout(yaxis_tickformat=".0%", height=300)
        st.plotly_chart(fig, width='stretch')
    # 匯出報告
    if st.button("匯出分析報告（CSV）"):
        report = pd.DataFrame({
            "metric": ["最大缺口區塊", "最破碎時間段", "最完整時間段"],
            "start_time": [max_gap[0] if missing_runs else None, most_fragmented[0] if rates else None, most_complete[0] if rates else None],
            "end_time": [max_gap[1] if missing_runs else None, most_fragmented[1] if rates else None, most_complete[1] if rates else None],
            "value": [(max_gap[1]-max_gap[0]+sec_interval)//sec_interval if missing_runs else 0, most_fragmented[2] if rates else 0, most_complete[2] if rates else 0]
        })
        csv = report.to_csv(index=False, encoding='utf-8-sig')
        st.download_button("下載 CSV", csv, f"{symbol}_{sec_interval}s_analysis.csv", "text/csv")

st.set_page_config(page_title="秒級詳細分析", layout="wide")
st.title("⏱️ 秒級詳細分析")
st.sidebar.header("參數設定")
symbol = st.sidebar.selectbox("交易對", TradingConfig.SUPPORTED_SYMBOLS)
sec_interval = st.sidebar.selectbox("秒級別", [("1秒", 1), ("2秒", 2), ("5秒", 5), ("10秒", 10), ("15秒", 15), ("30秒", 30)], format_func=lambda x: x[0])[1]
hours = st.sidebar.slider("分析範圍（往後小時）", min_value=1, max_value=8, value=1, step=1)

# 台灣時間顯示與選擇（固定 00:00）
taipei_tz = timezone(timedelta(hours=8))
now_taipei = datetime.now(tz=taipei_tz)
default_start = now_taipei - timedelta(hours=1)

st.sidebar.write(f"目前時間（UTC+8）：{now_taipei.strftime('%Y-%m-%d %H:%M:%S')}")
# 初始化 session_state（只在首次載入時設定預設值）
if "start_date_secpage" not in st.session_state:
    st.session_state["start_date_secpage"] = default_start.date()

# 使用 session_state 維持使用者選擇，時間固定為 00:00
start_dt = st.sidebar.date_input("開始日期（UTC+8）", value=st.session_state["start_date_secpage"], key="start_date_secpage")
start_time = datetime.min.time()  # 固定為 00:00

# 顯示固定時間
st.sidebar.info(f"開始時間已固定為 00:00 (UTC+8)")

# 轉換為 UTC 時間戳進行查詢
start_ts = int(datetime.combine(start_dt, start_time, tzinfo=taipei_tz).timestamp())

# 未來時間鎖定
if start_ts >= now_taipei.timestamp():
    st.sidebar.error("⚠️ 開始日期不可為今天，請選擇過去日期")
    st.stop()
end_ts = start_ts + hours * 3600

sec_analysis(symbol, start_ts, end_ts, sec_interval)

# 除錯日誌區塊
st.divider()
st.subheader("🐛 除錯日誌")
st.write("這裡顯示最近的查詢除錯資訊，包含參數、資料庫狀態、錯誤原因等。")
log_content = dl.get_debug_log_content()
st.text_area("除錯日誌", value=log_content, height=300)
if st.button("清除日誌"):
    import os
    if os.path.exists("logs/streamlit_debug.log"):
        os.remove("logs/streamlit_debug.log")
        st.success("日誌已清除")
        st.rerun()
