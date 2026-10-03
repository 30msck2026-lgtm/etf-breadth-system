import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import os

st.set_page_config(page_title="美股細分行業 ETF 深度監控與轉勢雷達", page_icon="📈", layout="wide")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_FILE = os.path.join(DATA_DIR, "etf_system.db")

@st.cache_data(ttl=5)
def load_dashboard_data():
    if not os.path.exists(DB_FILE):
        return None, None, None, None, None
    conn = sqlite3.connect(DB_FILE)
    try:
        date_df = pd.read_sql("SELECT MAX(date) as max_date FROM market_daily_metrics", conn)
        latest_date = date_df["max_date"].iloc[0]
    except Exception as e:
        conn.close()
        return None, None, None, None, None
        
    if not latest_date:
        conn.close()
        return None, None, None, None, None
        
    q_metrics = f"""
    SELECT m.*, meta.name, meta.sector, meta.sub_industry, meta.benchmark
    FROM market_daily_metrics m
    JOIN etf_metadata meta ON m.symbol = meta.symbol
    WHERE m.date = '{latest_date}'
    """
    df_metrics = pd.read_sql(q_metrics, conn)
    df_macro = pd.read_sql("SELECT * FROM macro_breadth ORDER BY date ASC", conn)
    
    sectors_q = f"""
    SELECT symbol, close_price, pct_change, momentum_5d, dist_20ma
    FROM market_daily_metrics 
    WHERE symbol IN ('XLK','XLV','XLF','XLI','XLY','XLP','XLE','XLB','XLU','XLRE','XLC') 
      AND date = '{latest_date}'
    """
    df_sectors = pd.read_sql(sectors_q, conn)
    
    try:
        df_logs = pd.read_sql("SELECT * FROM system_health_logs ORDER BY timestamp DESC LIMIT 15", conn)
    except:
        df_logs = None
        
    conn.close()
    return df_metrics, df_macro, df_sectors, df_logs, latest_date

st.title("🏛️ 美股細分行業 ETF 深度監控與市場寬度雷達")

top_col1, top_col2 = st.columns([8, 2])
with top_col2:
    if st.button("🔄 清除快取並重讀資料庫"):
        st.cache_data.clear()
        st.rerun()

df_metrics, df_macro, df_sectors, df_logs, latest_date = load_dashboard_data()

# 系統健康檢查橫幅
if df_logs is not None and not df_logs.empty:
    err_logs = df_logs[df_logs["status"].isin(["WARNING", "ERROR"])]
    if not err_logs.empty:
        with st.expander(f"⚠️ 系統偵測到 {len(err_logs)} 項數據抓取警報 (點擊展開查看詳細診斷)", expanded=False):
            st.caption("以下為後台執行時遭遇的發行商反爬阻擋或個股行情獲取記錄：")
            st.dataframe(
                err_logs.rename(columns={"timestamp": "時間", "log_type": "類型", "target": "對象標的", "status": "狀態", "message": "診斷詳情"}),
                use_container_width=True,
                height=180
            )
    else:
        st.success("🟢 數據源健康檢查：全量持股同步與個股行情獲取狀態良好，無任何異常！")

if df_metrics is None or df_metrics.empty:
    st.warning("⚠️ 資料庫尚未初始化或正在計算中！")
    st.info("請在 GitHub Actions 頁面點擊【Run workflow】以執行全量計算。")
    st.stop()

# ==========================================
# A. 全局市場層 (Macro Breadth)
# ==========================================
st.markdown(f"## 🌐 A. 全局市場層 (Macro Breadth) — 基準日: `{latest_date}`")

if df_macro is not None and not df_macro.empty:
    latest_macro = df_macro[df_macro["date"] == latest_date]
    m_cols = st.columns(4)
    for _, row in latest_macro.iterrows():
        idx_n = row["index_name"]
        nh = row["new_highs_count"]
        nl = row["new_lows_count"]
        net = row["net_highs_lows"]
        p50 = row["pct_above_50ma"]
        if "S&P" in idx_n:
            m_cols[0].metric("標普 500 (52週新高 / 新低)", f"{nh} 隻 / {nl} 隻", delta=f"淨新高: {net:+d}")
            m_cols[1].metric("標普 500 站上 50MA 比例", f"{p50}%")
        else:
            m_cols[2].metric("納指 100 (52週新高 / 新低)", f"{nh} 隻 / {nl} 隻", delta=f"淨新高: {net:+d}")
            m_cols[3].metric("納指 100 站上 50MA 比例", f"{p50}%")
            
    if len(df_macro["date"].unique()) > 1:
        st.caption("📈 S&P 500 & Nasdaq 每日淨新高 (NH - NL) 走勢曲線")
        fig_macro = px.line(df_macro, x="date", y="net_highs_lows", color="index_name", markers=True)
        fig_macro.add_hline(y=0, line_dash="dash", line_color="gray")
        fig_macro.update_layout(height=260, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_macro, use_container_width=True)

if df_sectors is not None and not df_sectors.empty:
    st.markdown("#### 🧭 11 大核心板塊 (Sectors) 當日資金流向熱力分佈")
    fig_sector_heat = px.bar(
        df_sectors.sort_values(by="pct_change", ascending=False),
        x="symbol", y="pct_change",
        color="pct_change",
        color_continuous_scale="RdYlGn",
        text="pct_change",
        labels={"pct_change": "漲跌幅 (%)", "symbol": "板塊 ETF"}
    )
    fig_sector_heat.update_traces(texttemplate="%{text:+.2f}%", textposition="outside")
    fig_sector_heat.update_layout(height=280, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_sector_heat, use_container_width=True)

st.markdown("---")

# ==========================================
# C. 轉勢雷達 (Reversal Radar)
# ==========================================
st.markdown("## 🚨 C. 轉勢雷達 (Reversal Radar)")
radar_alerts = df_metrics[df_metrics["reversal_signal_flag"] != "常規波動"]
if not radar_alerts.empty:
    alert_cols = st.columns(min(len(radar_alerts), 4))
    for i, (_, r) in enumerate(radar_alerts.head(4).iterrows()):
        with alert_cols[i % 4]:
            t_cnt = int(r.get('total_stocks_count', 0))
            if t_cnt == 0:
                t_cnt = int(r.get('advancing_count', 0)) + int(r.get('declining_count', 0))
            adv_txt = f"{int(r.get('advancing_count',0))}升 / {int(r.get('declining_count',0))}跌 (共{t_cnt}隻)"
            st.error(f"⚡ **{r['symbol']} ({r['name']})**\n\n"
                     f"• 信號: **{r['reversal_signal_flag']}**\n"
                     f"• ETF 漲跌: `{r['pct_change']:+.2f}%` | 等權: `{r['equal_weight_return']:+.2f}%`\n"
                     f"• 距 20MA: `{r['dist_20ma']:+.2f}%`\n"
                     f"• 內部漲跌: **{adv_txt}** (佔比 `{r['advancing_ratio']}%`)")
else:
    st.success("✅ 今日 Universe 內暫未發現極端轉勢異動，市場維持現有趨勢。")

st.markdown("---")

# ==========================================
# B. 細分子行業篩選層 (Sub-Industry Screener)
# ==========================================
st.markdown("## 🔬 B. 細分子行業篩選層 (Sub-Industry Screener)")

st.sidebar.header("🎯 複合條件篩選 (Screener Filters)")
STANDARD_11_SECTORS = [
    "資訊科技", "通信服務", "非必需消費", "必需消費", "醫療保健",
    "金融", "工業", "能源", "原材料", "公用事業", "房地產"
]
sel_sectors = st.sidebar.multiselect("選擇大板塊 (GICS 11 大標準分類):", STANDARD_11_SECTORS, default=STANDARD_11_SECTORS)

sort_by = st.sidebar.selectbox("動量 / 均線排行 (Sort By):", [
    "當日升幅 (pct_change)", "5 日動量 (momentum_5d)", "20 日動量 (momentum_20d)",
    "距離 20MA 偏離度 (dist_20ma)", "內部上漲比率 (advancing_ratio)"
])

divergence_filter = st.sidebar.selectbox("背離與轉勢過濾:", ["全部", "隱形強勢", "虛胖拉升", "右側爆發", "左側反轉"])
min_adv = st.sidebar.slider("內部最低上漲比例 (%):", 0, 100, 0)
ma20_bias_range = st.sidebar.slider("距 20MA 偏離範圍 (%):", -20.0, 20.0, (-15.0, 15.0))

view_df = df_metrics[df_metrics["sector"].isin(sel_sectors)]
view_df = view_df[
    (view_df["advancing_ratio"] >= min_adv) &
    (view_df["dist_20ma"] >= ma20_bias_range[0]) &
    (view_df["dist_20ma"] <= ma20_bias_range[1])
]
if divergence_filter != "全部":
    view_df = view_df[view_df["reversal_signal_flag"].str.contains(divergence_filter, na=False)]

sort_map = {
    "當日升幅 (pct_change)": "pct_change",
    "5 日動量 (momentum_5d)": "momentum_5d",
    "20 日動量 (momentum_20d)": "momentum_20d",
    "距離 20MA 偏離度 (dist_20ma)": "dist_20ma",
    "內部上漲比率 (advancing_ratio)": "advancing_ratio"
}
view_df = view_df.sort_values(by=sort_map[sort_by], ascending=False)

def build_breadth_text(r):
    t_cnt = int(r.get('total_stocks_count', 0))
    a_cnt = int(r.get('advancing_count', 0))
    d_cnt = int(r.get('declining_count', 0))
    if t_cnt == 0:
        t_cnt = a_cnt + d_cnt
    return f"{a_cnt}升 / {d_cnt}跌 (共{t_cnt}隻)"

view_df["adv_dec_text"] = view_df.apply(build_breadth_text, axis=1)

disp_cols = [
    "symbol", "name", "sector", "sub_industry", "close_price",
    "pct_change", "equal_weight_return", "ew_vs_cap_spread",
    "adv_dec_text", "advancing_ratio",
    "dist_20ma", "dist_50ma", "dist_200ma",
    "momentum_5d", "above_20ma_ratio", "reversal_signal_flag"
]
rename_map = {
    "symbol": "代號", "name": "名稱", "sector": "大板塊", "sub_industry": "細分子行業",
    "close_price": "收盤價", "pct_change": "當日升幅", "equal_weight_return": "等權升幅", "ew_vs_cap_spread": "等權差額",
    "adv_dec_text": "內部升跌(隻數/總數)", "advancing_ratio": "上漲佔比%",
    "dist_20ma": "距20MA", "dist_50ma": "距50MA", "dist_200ma": "距200MA",
    "momentum_5d": "5日動量", "above_20ma_ratio": "站上20MA%", "reversal_signal_flag": "轉勢信號"
}

def style_screener(st_df):
    return st_df.format({
        "收盤價": "${:.2f}",
        "當日升幅": "{:+.2f}%",
        "等權升幅": "{:+.2f}%",
        "等權差額": "{:+.2f}%",
        "上漲佔比%": "{:.1f}%",
        "距20MA": "{:+.2f}%",
        "距50MA": "{:+.2f}%",
        "距200MA": "{:+.2f}%",
        "5日動量": "{:+.2f}%",
        "站上20MA%": "{:.1f}%"
    })

styled_table = style_screener(view_df[disp_cols].rename(columns=rename_map).style)
st.dataframe(styled_table, use_container_width=True, height=420)

# ==========================================
# 散佈圖與全量持股穿透
# ==========================================
st.markdown("---")
st.subheader("💡 內外背離雷達圖 (ETF 當日升幅 vs 等權升幅)")
fig_scat = px.scatter(
    view_df,
    x="pct_change", y="equal_weight_return",
    text="symbol", color="advancing_ratio",
    color_continuous_scale="RdYlGn",
    size=np.abs(view_df["ew_vs_cap_spread"]) + 2,
    hover_data=["name", "sub_industry", "adv_dec_text", "reversal_signal_flag"],
    labels={"pct_change": "ETF 當日升幅 (%)", "equal_weight_return": "內部等權升幅 (%)"}
)
min_v = min(view_df["pct_change"].min(), view_df["equal_weight_return"].min(), -2)
max_v = max(view_df["pct_change"].max(), view_df["equal_weight_return"].max(), 2)
fig_scat.add_trace(go.Scatter(x=[min_v, max_v], y=[min_v, max_v], mode="lines", line=dict(dash="dash", color="gray"), name="等權 = 市值"))
fig_scat.update_traces(textposition="top center")
fig_scat.update_layout(height=480)
st.plotly_chart(fig_scat, use_container_width=True)

st.markdown("---")
st.subheader("🔎 單一細分 ETF 成分股持股穿透 (Holdings Drill-Down)")
target_etf = st.selectbox("選擇要穿透全量持股的 ETF:", view_df["symbol"].tolist())
if target_etf:
    conn = sqlite3.connect(DB_FILE)
    h_df = pd.read_sql(f"SELECT stock_symbol, weight, updated_date FROM etf_holdings WHERE etf_symbol='{target_etf}' ORDER BY weight DESC", conn)
    conn.close()
    if not h_df.empty:
        st.write(f"**{target_etf}** 底層持股清單（已完整展示該 ETF 的全體 **{len(h_df)} 隻**成分股）：")
        formatted_h_df = h_df.rename(columns={"stock_symbol": "成分股代號", "weight": "持股權重", "updated_date": "持股更新日期"})
        st.dataframe(
            formatted_h_df.style.format({"持股權重": "{:.4f}"}),
            use_container_width=True,
            height=350
        )
