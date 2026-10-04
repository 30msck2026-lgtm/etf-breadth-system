import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse

st.set_page_config(page_title="美股細分行業 ETF 深度監控與市場寬度雷達", page_icon="📈", layout="wide")

# ==============================================================================
# 0. 配置您的 Google Sheet 試算表 ID
# ==============================================================================
# 請將下方的 SHEET_ID 替換為您在瀏覽器網址列看到的 Google Sheet 長串代碼
# 例如: https://docs.google.com/spreadsheets/d/1qd_h5Q768s5_4XPcO8Nqbruvqy4VPOu4OJLm5vQ5ggY/edit
DEFAULT_SHEET_ID = "1m5Iw5TEGCWDfhnta3Xv83er2j91gIDp56LHWjEjdjxM/edit?gid=603057017#gid=603057017"

# 允許在側邊欄即時切換或覆蓋 Google Sheet ID
st.sidebar.header("⚙️ 數據庫連線設定")
sheet_id = st.sidebar.text_input("Google Sheet 試算表 ID:", value=DEFAULT_SHEET_ID)

@st.cache_data(ttl=60)
def load_sheet_csv(sheet_id, sheet_name):
    """免金鑰、100% 免費直接透過 Google GViz 端點讀取公開試算表分頁為 DataFrame"""
    encoded_name = urllib.parse.quote(sheet_name)
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_name}"
    try:
        df = pd.read_csv(url)
        return df
    except Exception as e:
        return None

# 讀取總看板【財報日更新表】
df_raw = load_sheet_csv(sheet_id, "財報日更新表")

st.title("🏛️ 美股細分行業 ETF 深度監控與市場寬度雷達")
st.caption("⚡ 數據底層：Google Sheets 即時同步 | 前端界面：互動式量化雷達儀表板")

if df_raw is None or df_raw.empty:
    st.error("⚠️ 無法連線至 Google Sheet！請確認：\n1. 試算表右上角【共用】已設為「知道連結的人均可檢視 (Viewer)」\n2. 試算表 ID 是否正確。")
    st.stop()

# -------------------------------------------------------------
# 數據清洗與解析
# -------------------------------------------------------------
# 尋找宏觀大盤指標行 (SPY, QQQ, IWM, VIX, DIA)
macro_data = {}
try:
    # 讀取第 3 行宏觀數據
    spy_p = df_raw.iloc[1, 1] if len(df_raw) > 1 else None
    spy_c = df_raw.iloc[1, 2] if len(df_raw) > 1 else None
    qqq_p = df_raw.iloc[1, 4] if len(df_raw) > 1 else None
    qqq_c = df_raw.iloc[1, 5] if len(df_raw) > 1 else None
    iwm_p = df_raw.iloc[1, 7] if len(df_raw) > 1 else None
    iwm_c = df_raw.iloc[1, 8] if len(df_raw) > 1 else None
    vix_p = df_raw.iloc[1, 10] if len(df_raw) > 1 else None
    dia_p = df_raw.iloc[1, 12] if len(df_raw) > 1 else None
    dia_c = df_raw.iloc[1, 13] if len(df_raw) > 1 else None
except:
    pass

# 尋找 ETF 主數據表 (從第 5 行表頭開始)
header_row_idx = None
for idx, r in df_raw.iterrows():
    if any("ETF 代號" in str(v) for v in r.values):
        header_row_idx = idx
        break

if header_row_idx is not None:
    df_metrics = df_raw.iloc[header_row_idx+1:].copy()
    df_metrics.columns = [str(c).strip() for c in df_raw.iloc[header_row_idx].values]
    df_metrics = df_metrics.dropna(subset=["ETF 代號"])
    df_metrics = df_metrics[df_metrics["ETF 代號"].str.len() <= 6]
else:
    df_metrics = df_raw.copy()

# 數值型別轉換清洗
def clean_num(val):
    if pd.isna(val): return 0.0
    s = str(val).replace("$", "").replace("%", "").replace(",", "").replace("+", "").strip()
    try: return float(s)
    except: return 0.0

col_map = {
    "最新現價": "close_price",
    "當日升幅": "pct_change",
    "內部等權升幅": "equal_weight_return",
    "等權差額 (背離)": "ew_vs_cap_spread",
    "上漲佔比%": "advancing_ratio",
    "20日均線(20MA)": "ma20",
    "距20MA偏離度": "dist_20ma",
    "5日動量": "momentum_5d",
    "轉勢雷達信號": "reversal_signal_flag",
    "內部升跌狀態": "adv_dec_text",
    "大板塊 (GICS)": "sector",
    "細分子行業": "sub_industry",
    "ETF 名稱": "name",
    "ETF 代號": "symbol",
    "發行商": "issuer"
}

for k, v in col_map.items():
    if k in df_metrics.columns:
        df_metrics[v] = df_metrics[k]

num_cols = ["close_price", "pct_change", "equal_weight_return", "ew_vs_cap_spread", "advancing_ratio", "dist_20ma", "momentum_5d"]
for c in num_cols:
    if c in df_metrics.columns:
        df_metrics[c] = df_metrics[c].apply(clean_num)

# ==============================================================================
# 頂部控制列
# ==============================================================================
top_c1, top_c2 = st.columns([8, 2])
with top_c2:
    if st.button("🔄 刷新 Google Sheet 數據", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ==============================================================================
# 📋 財報日更新表 (發行商持股更新狀態)
# ==============================================================================
st.markdown("## 📋 財報日更新表")
st.caption("即時監控 Universe 內各 ETF 底層持股更新狀態、調倉週期及內部升跌情況：")
disp_sync_cols = [c for c in ["symbol", "name", "issuer", "sector", "sub_industry", "adv_dec_text", "reversal_signal_flag", "調倉月份"] if c in df_metrics.columns]
st.dataframe(df_metrics[disp_sync_cols].rename(columns={
    "symbol": "ETF 代號", "name": "ETF 名稱", "issuer": "發行商", "sector": "大板塊",
    "sub_industry": "細分子行業", "adv_dec_text": "內部升跌狀態", "reversal_signal_flag": "轉勢信號", "調倉月份": "官方調倉月份"
}), use_container_width=True, height=220)

st.markdown("---")

# ==============================================================================
# A. 全局市場層 (Macro Breadth)
# ==============================================================================
st.markdown("## 🌐 A. 全局市場層 (Macro Breadth)")
m_c1, m_c2, m_c3, m_c4 = st.columns(4)
m_c1.metric("標普 500 (SPY)", f"${clean_num(spy_p):.2f}", delta=f"{clean_num(spy_c):+.2f}%")
m_c2.metric("納指 100 (QQQ)", f"${clean_num(qqq_p):.2f}", delta=f"{clean_num(qqq_c):+.2f}%")
m_c3.metric("羅素 2000 (IWM)", f"${clean_num(iwm_p):.2f}", delta=f"{clean_num(iwm_c):+.2f}%")
m_c4.metric("道瓊斯 (DIA)", f"${clean_num(dia_p):.2f}", delta=f"{clean_num(dia_c):+.2f}%")

# 11 大核心板塊 (Sectors) 資金流向熱力分佈圖
sectors_list = ['XLK','XLV','XLF','XLI','XLY','XLP','XLE','XLB','XLU','XLRE','XLC']
df_sectors = df_metrics[df_metrics["symbol"].isin(sectors_list)].copy()
if not df_sectors.empty:
    st.markdown("#### 🧭 11 大核心板塊 (Sectors) 當日資金流向熱力分佈")
    fig_sector = px.bar(
        df_sectors.sort_values(by="pct_change", ascending=False),
        x="symbol", y="pct_change",
        color="pct_change",
        color_continuous_scale="RdYlGn",
        text="pct_change",
        hover_data=["name"],
        labels={"pct_change": "漲跌幅 (%)", "symbol": "板塊 ETF"}
    )
    fig_sector.update_traces(texttemplate="%{text:+.2f}%", textposition="outside")
    fig_sector.update_layout(height=280, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_sector, use_container_width=True)

st.markdown("---")

# ==============================================================================
# C. 轉勢雷達 (Reversal Radar)
# ==============================================================================
st.markdown("## 🚨 C. 轉勢雷達 (Reversal Radar)")
radar_alerts = df_metrics[
    (df_metrics["reversal_signal_flag"].str.contains("⚡|⚠️|🚀|🔄", na=False)) &
    (~df_metrics["symbol"].isin(sectors_list))
]
if not radar_alerts.empty:
    alert_cols = st.columns(min(len(radar_alerts), 4))
    for i, (_, r) in enumerate(radar_alerts.head(4).iterrows()):
        with alert_cols[i % 4]:
            st.error(f"⚡ **{r['symbol']} ({r['name']})**\n\n"
                     f"• 信號: **{r['reversal_signal_flag']}**\n"
                     f"• ETF 漲跌: `{r['pct_change']:+.2f}%` | 等權: `{r['equal_weight_return']:+.2f}%`\n"
                     f"• 距 20MA: `{r['dist_20ma']:+.2f}%`\n"
                     f"• 內部狀況: **{r.get('adv_dec_text', '--')}**")
else:
    st.success("✅ 今日 Universe 內暫未發現極端轉勢異動，市場維持現有趨勢。")

st.markdown("---")

# ==============================================================================
# B. 細分子行業篩選層 (Sub-Industry Screener)
# ==============================================================================
st.markdown("## 🔬 B. 細分子行業篩選層 (Sub-Industry Screener)")

# 左側邊欄篩選控件 (完全復刻原版)
STANDARD_11_SECTORS = [
    "資訊科技", "通信服務", "非必需消費", "必需消費", "醫療保健",
    "金融", "工業", "能源", "原材料", "公用事業", "房地產"
]
sel_sectors = st.sidebar.multiselect("選擇大板塊 (GICS 11 大標準分類):", STANDARD_11_SECTORS, default=STANDARD_11_SECTORS)

sort_by = st.sidebar.selectbox("動量 / 均線排行 (Sort By):", [
    "當日升幅 (pct_change)", "5 日動量 (momentum_5d)",
    "距離 20MA 偏離度 (dist_20ma)", "內部上漲比率 (advancing_ratio)"
])

divergence_filter = st.sidebar.selectbox("背離與轉勢過濾:", ["全部", "隱形強勢", "虛胖拉升", "右側爆發", "左側反轉"])
min_adv = st.sidebar.slider("內部最低上漲比例 (%):", 0, 100, 0)
ma20_bias_range = st.sidebar.slider("距 20MA 偏離範圍 (%):", -20.0, 20.0, (-15.0, 15.0))

# 執行過濾
view_df = df_metrics[
    (df_metrics["sector"].isin(sel_sectors)) &
    (~df_metrics["symbol"].isin(sectors_list))
]
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
    "距離 20MA 偏離度 (dist_20ma)": "dist_20ma",
    "內部上漲比率 (advancing_ratio)": "advancing_ratio"
}
view_df = view_df.sort_values(by=sort_map[sort_by], ascending=False)

disp_cols = [
    "symbol", "name", "sector", "sub_industry", "close_price",
    "pct_change", "equal_weight_return", "ew_vs_cap_spread",
    "adv_dec_text", "advancing_ratio",
    "dist_20ma", "momentum_5d", "reversal_signal_flag"
]
rename_map = {
    "symbol": "代號", "name": "名稱", "sector": "大板塊", "sub_industry": "細分子行業",
    "close_price": "收盤價", "pct_change": "當日升幅", "equal_weight_return": "等權升幅", "ew_vs_cap_spread": "等權差額",
    "adv_dec_text": "內部升跌(隻數/總數)", "advancing_ratio": "上漲佔比%",
    "dist_20ma": "距20MA", "momentum_5d": "5日動量", "reversal_signal_flag": "轉勢信號"
}

st.dataframe(view_df[disp_cols].rename(columns=rename_map).style.format({
    "收盤價": "${:.2f}", "當日升幅": "{:+.2f}%", "等權升幅": "{:+.2f}%",
    "等權差額": "{:+.2f}%", "上漲佔比%": "{:.1f}%", "距20MA": "{:+.2f}%", "5日動量": "{:+.2f}%"
}), use_container_width=True, height=420)

# ==============================================================================
# 💡 內外背離雷達圖 (散點圖)
# ==============================================================================
st.markdown("---")
st.subheader("💡 內外背離雷達圖 (ETF 當日升幅 vs 等權升幅)")
if not view_df.empty:
    fig_scat = px.scatter(
        view_df,
        x="pct_change", y="equal_weight_return",
        text="symbol", color="advancing_ratio",
        color_continuous_scale="RdYlGn",
        size=np.abs(view_df["ew_vs_cap_spread"]) + 3,
        hover_data=["name", "sub_industry", "adv_dec_text", "reversal_signal_flag"],
        labels={"pct_change": "ETF 當日升幅 (%)", "equal_weight_return": "內部等權升幅 (%)"}
    )
    min_v = min(view_df["pct_change"].min(), view_df["equal_weight_return"].min(), -2)
    max_v = max(view_df["pct_change"].max(), view_df["equal_weight_return"].max(), 2)
    fig_scat.add_trace(go.Scatter(x=[min_v, max_v], y=[min_v, max_v], mode="lines", line=dict(dash="dash", color="gray"), name="等權 = 市值"))
    fig_scat.update_traces(textposition="top center")
    fig_scat.update_layout(height=480)
    st.plotly_chart(fig_scat, use_container_width=True)

# ==============================================================================
# 🔎 單一細分 ETF 成分股持股穿透 (Holdings Drill-Down)
# ==============================================================================
st.markdown("---")
st.subheader("🔎 單一細分 ETF 成分股持股穿透 (Holdings Drill-Down)")
all_avail_symbols = df_metrics["symbol"].tolist()
target_etf = st.selectbox("選擇要穿透全量持股的 ETF:", all_avail_symbols, index=all_avail_symbols.index("XTN") if "XTN" in all_avail_symbols else 0)

if target_etf:
    tab_name = f"{target_etf}_持股明細"
    df_drill = load_sheet_csv(sheet_id, tab_name)
    if df_drill is not None and not df_drill.empty:
        # 清洗明細表頭
        h_idx = 0
        for i_row, r_val in df_drill.iterrows():
            if any("股票代號" in str(x) for x in r_val.values):
                h_idx = i_row
                break
        df_drill_clean = df_drill.iloc[h_idx+1:].copy()
        df_drill_clean.columns = [str(c).strip() for c in df_drill.iloc[h_idx].values]
        df_drill_clean = df_drill_clean.dropna(subset=[df_drill_clean.columns[0]])
        
        st.write(f"**{target_etf}** 底層持股清單（來自 Google Sheet【{tab_name}】分頁，共展示 **{len(df_drill_clean)} 隻**成分股）：")
        st.dataframe(df_drill_clean, use_container_width=True, height=350)
    else:
        st.info(f"ℹ️ Google Sheet 尚未建立【{tab_name}】分頁。請在試算表的「ETF_空白快速新增模板」輸入 {target_etf} 並點擊按鈕生成！")
