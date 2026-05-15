"""
Streamlit 網頁應用：交易資料來源與缺口視覺化
- 資料來源顏色：interpolated(橘)、real(綠)、Aggregation(黃)、inferior-Aggregation(黑)
- 缺口視覺化：有資料(白長條)、缺口(紅長條)
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
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.dirname(__file__))

import debug_logger as dl  # type: ignore
dl = importlib.reload(dl)
from config.trading_config import TradingConfig

# 使用與 database.py 相同的路徑邏輯
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "system_data.db"))

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
    """生成完整時間桶，用於缺口視覺化"""
    buckets = []
    ts = start_ts
    while ts < end_ts:
        buckets.append({"timestamp": ts, "has_data": False})
        ts += interval_sec
    return pd.DataFrame(buckets)

def source_color_map(source: str) -> str:
    """資料來源對應顏色"""
    mapping = {
        "real": "green",
        "interpolated": "orange",
        "Aggregation": "yellow",
        "inferior-Aggregation": "black"
    }
    return mapping.get(source, "gray")

def plot_source_distribution(df: pd.DataFrame, title: str):
    """繪製資料來源分佈（長條圖）"""
    if df.empty:
        st.warning("無資料可繪")
        return
    df["color"] = df["data_source"].map(source_color_map)
    fig = px.bar(
        df,
        x="readable_time",
        y="close",
        color="data_source",
        color_discrete_map={
            "real": "green",
            "interpolated": "orange",
            "Aggregation": "yellow",
            "inferior-Aggregation": "black"
        },
        title=title,
        labels={"readable_time": "時間（UTC+8）", "close": "收盤價", "data_source": "資料來源"}
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, width='stretch')
    # 圖例說明
    st.markdown("""
    **圖例說明**
    - 🟢 綠色：real（即時真實資料）
    - 🟠 橘色：interpolated（內插資料）
    - 🟡 黃色：Aggregation（聚合資料，源皆為 real）
    - ⚫ 黑色：inferior-Aggregation（聚合資料，源含 interpolated）
    """)

def plot_gap_histogram(start_ts: float, end_ts: float, interval_sec: int, symbol: str):
    """缺口視覺化：有資料(淺灰長條)、缺口(紅長條)"""
    # 載入實際資料
    df = load_data(symbol, interval_sec, start_ts, end_ts)
    # 生成完整時間桶
    buckets = generate_time_buckets(start_ts, end_ts, interval_sec)
    # 標記有資料的桶
    if not df.empty:
        existing_ts = set(df["timestamp"])
        buckets["has_data"] = buckets["timestamp"].apply(lambda ts: ts in existing_ts)
    buckets["readable_time"] = pd.to_datetime(buckets["timestamp"], unit="s", utc=True).dt.tz_convert("Asia/Taipei")
    buckets["color"] = buckets["has_data"].apply(lambda x: "lightgray" if x else "red")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=buckets["readable_time"],
        y=[1]*len(buckets),
        marker_color=buckets["color"],
        name="有資料" if buckets["has_data"].all() else "缺口",
        hovertemplate="%{x}<br>有資料: %{customdata}<extra></extra>",
        customdata=buckets["has_data"]
    ))
    fig.update_layout(
        title=f"{symbol} 缺口視覺化（{interval_sec}s）",
        xaxis_title="時間（UTC+8）",
        yaxis_title="狀態",
        showlegend=False,
        height=300
    )
    st.plotly_chart(fig, width='stretch')
    # 統計缺口與圖例
    missing = (~buckets["has_data"]).sum()
    total = len(buckets)
    col1, col2 = st.columns(2)
    with col1:
        st.metric(f"缺口數（{interval_sec}s）", f"{missing}/{total}")
    with col2:
        st.markdown("""
        **圖例說明**
        - 🔳 淺灰色：有資料
        - 🔴 紅色：缺口（無資料）
        """)

def plot_sec_level_analysis(symbol: str, start_ts: float, end_ts: float, sec_interval: int = 1):
    """秒級視覺化分析：連續缺失最大區塊、最分散破碎時間段、最完整時間段"""
    df = load_data(symbol, sec_interval, start_ts, end_ts)
    if df.empty:
        st.warning(f"無 {sec_interval} 秒資料可分析")
        return
    # 生成完整時間桶
    buckets = generate_time_buckets(start_ts, end_ts, sec_interval)
    buckets["has_data"] = buckets["timestamp"].apply(lambda ts: ts in set(df["timestamp"]))
    # 1. 連續缺失最大區塊
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
    if missing_runs:
        max_gap = max(missing_runs, key=lambda x: x[1] - x[0] + sec_interval)
        st.write(f"🔴 **連續缺失最大區塊**：{datetime.fromtimestamp(max_gap[0], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} ~ {datetime.fromtimestamp(max_gap[1], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}（{(max_gap[1]-max_gap[0]+sec_interval)//sec_interval} 筆）")
        # 視覺化：最大缺口區塊長條圖
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
    # 2. 最分散破碎時間段（每 10 分鐘統計缺口率）
    window = 600  # 10 分鐘
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
        st.write(f"🟠 **最分散破碎時間段**：{datetime.fromtimestamp(most_fragmented[0], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} ~ {datetime.fromtimestamp(most_fragmented[1], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}（缺口率 {most_fragmented[2]*100:.1f}%）")
        # 視覺化：破碎時間段缺口率
        df_frag = pd.DataFrame(rates, columns=["start", "end", "gap_rate"])
        df_frag["time"] = pd.to_datetime(df_frag["start"], unit="s", utc=True).dt.tz_convert("Asia/Taipei")
        fig_frag = px.bar(df_frag, x="time", y="gap_rate", title="每 10 分鐘缺口率（最破碎時間段）", labels={"gap_rate": "缺口率", "time": "時間（UTC+8）"})
        fig_frag.update_layout(yaxis_tickformat=".0%", height=250)
        st.plotly_chart(fig_frag, width='stretch')
    # 3. 最完整時間段
    if rates:
        most_complete = min(rates, key=lambda x: x[2])
        st.write(f"🟢 **最完整時間段**：{datetime.fromtimestamp(most_complete[0], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} ~ {datetime.fromtimestamp(most_complete[1], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}（缺口率 {most_complete[2]*100:.1f}%）")
        # 視覺化：完整時間段缺口率
        df_comp = pd.DataFrame(rates, columns=["start", "end", "gap_rate"])
        df_comp["time"] = pd.to_datetime(df_comp["start"], unit="s", utc=True).dt.tz_convert("Asia/Taipei")
        fig_comp = px.bar(df_comp, x="time", y="gap_rate", title="每 10 分鐘缺口率（最完整時間段）", labels={"gap_rate": "缺口率", "time": "時間（UTC+8）"})
        fig_comp.update_layout(yaxis_tickformat=".0%", height=250)
        st.plotly_chart(fig_comp, width='stretch')

st.set_page_config(page_title="交易資料來源與缺口視覺化", layout="wide")
st.title("📊 交易資料來源與缺口視覺化")
st.sidebar.header("參數設定")
symbol = st.sidebar.selectbox("交易對", TradingConfig.SUPPORTED_SYMBOLS)
interval = st.sidebar.selectbox("級別", [
    ("15秒", 15), ("30秒", 30),
    ("1分鐘", 60), ("5分鐘", 300), ("15分鐘", 900), ("30分鐘", 1800),
    ("1小時", 3600), ("4小時", 14400), ("1天", 86400)
], format_func=lambda x: x[0])[1]

# 時間範圍選擇：改為「往後 X 小時」
if interval in (30, 60):  # 30秒、1分鐘預設上限8小時
    max_hours = 8
else:
    max_hours = 24

# 檢查是否在缺口視覺化頁面使用快速設定
if st.session_state.get("use_quick_setting", False):
    hours = st.session_state["quick_hours"]
    # 在側邊欄顯示提示但不顯示滑桿
    st.sidebar.info(f"時間範圍：{hours} 小時（快速設定）")
else:
    hours = st.sidebar.slider("時間範圍（往後小時）", min_value=1, max_value=max_hours, value=1, step=1)

# 開始時間選擇（固定 00:00，僅保留顯示）
taipei_tz = timezone(timedelta(hours=8))
now_taipei = datetime.now(tz=taipei_tz)
default_start = now_taipei - timedelta(hours=1)

st.sidebar.write(f"目前時間（UTC+8）：{now_taipei.strftime('%Y-%m-%d %H:%M:%S')}")
# 初始化 session_state（只在首次載入時設定預設值）
if "start_date_main" not in st.session_state:
    st.session_state["start_date_main"] = default_start.date()

# 使用 session_state 維持使用者選擇，時間固定為 00:00
start_dt = st.sidebar.date_input("開始日期（UTC+8）", value=st.session_state["start_date_main"], key="start_date_main")
start_time = datetime.min.time()  # 固定為 00:00

# 顯示固定時間
st.sidebar.info(f"開始時間已固定為 00:00 (UTC+8)")

# 轉換為 UTC 時間戳進行查詢
start_ts = int(datetime.combine(start_dt, start_time, tzinfo=taipei_tz).timestamp())

# 若開始時間為現在或未來，強制鎖定無法選擇
if start_ts >= now_taipei.timestamp():
    st.sidebar.error("⚠️ 開始日期不可為今天，請選擇過去日期")
    st.stop()

end_ts = start_ts + hours * 3600

tab1, tab2, tab3, tab4 = st.tabs(["📈 資料來源分佈", "🕳️ 缺口視覺化", "⏱️ 秒級視覺化", "🐛 除錯日誌"])
with tab1:
    df = load_data(symbol, interval, start_ts, end_ts)
    st.subheader(f"{symbol} ({interval}s) 資料來源分佈")
    plot_source_distribution(df, f"{symbol} 資料來源分佈（{interval}s）")
    if not df.empty:
        st.write("資料統計")
        st.write(df["data_source"].value_counts())
with tab2:
    st.subheader(f"{symbol} ({interval}s) 缺口視覺化")
    
    # 快速時間範圍設定按鈕
    st.write("#### 快速時間範圍設定")
    quick_hours = [2, 4, 6, 8, 16, 24]
    cols = st.columns(6)
    
    # 檢查是否使用快速設定
    for i, hour in enumerate(quick_hours):
        if cols[i].button(f"{hour}小時", key=f"quick_{hour}"):
            st.session_state["use_quick_setting"] = True
            st.session_state["quick_hours"] = hour
            st.rerun()
    
    # 判斷是否使用快速設定
    if st.session_state.get("use_quick_setting", False):
        hours = st.session_state["quick_hours"]
        st.info(f"使用快速設定：{hours} 小時")
        # 重置快速設定的按鈕
        if st.button("重置為手動設定"):
            st.session_state["use_quick_setting"] = False
            st.rerun()
    else:
        st.info("使用側邊欄的時間範圍滑桿設定")
    
    # 重新計算 end_ts
    end_ts = start_ts + hours * 3600
    
    plot_gap_histogram(start_ts, end_ts, interval, symbol)
with tab3:
    st.subheader(f"{symbol} 秒級視覺化（基於 {interval}s 範圍）")
    if interval <= 60:
        st.info("秒級視覺化：顯示連續缺失最大區塊、最分散破碎時間段、最完整時間段")
        # 秒級子選項
        sec_interval = st.selectbox("選擇秒級別", [("1秒", 1), ("2秒", 2), ("5秒", 5)], format_func=lambda x: x[0])[1]
        plot_sec_level_analysis(symbol, start_ts, end_ts, sec_interval)
    else:
        st.warning("秒級視覺化僅支援 15 秒～1 分鐘級別")
with tab4:
    st.subheader("🐛 除錯日誌")
    st.write("這裡顯示最近的查詢除錯資訊，包含參數、資料庫狀態、錯誤原因等。")
    log_content = dl.get_debug_log_content()
    st.text_area("除錯日誌", value=log_content, height=400)
    if st.button("清除日誌"):
        import os
        if os.path.exists("logs/streamlit_debug.log"):
            os.remove("logs/streamlit_debug.log")
            st.success("日誌已清除")
            st.rerun()
