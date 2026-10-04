import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
import re

st.set_page_config(page_title="美股細分行業 ETF 深度監控與市場寬度雷達", page_icon="📈", layout="wide")

DEFAULT_SHEET_ID = "1m5Iw5TEGCWDfhnta3Xv83er2j91gIDp56LHWjEjdjxM"

st.sidebar.header("⚙️ 數據庫連線設定")
raw_input = st.sidebar.text_input(
    "Google Sheet 網址或試算表 ID:",
    value=DEFAULT_SHEET_ID,
    help="您可以直接貼上整串 Google 試算表瀏覽器網址，系統會自動提取 ID！"
)

def extract_sheet_id(text):
    if not text:
        return DEFAULT_SHEET_ID
    text = text.strip()
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", text)
    if match:
        return match.group(1)
    if "/" not in text and len(text) > 20:
        return text
    return DEFAULT_SHEET_ID

sheet_id = extract_sheet_id(raw_input)

@st.cache_data(ttl=15)
def load_sheet_csv(s_id, sheet_name):
    if not s_id:
        return None, "請輸入有效的 Google Sheet ID"
        
    encoded_name = urllib.parse.quote(sheet_name)
    url1 = f"https://docs.google.com/spreadsheets/d/{s_id}/gviz/tq?tqx=out:csv&sheet={encoded_name}"
    url2 = f"https://docs.google.com/spreadsheets/d/{s_id}/export?format=csv&id={s_id}&gid=0"
    
    for u in [url1, url2]:
        try:
            df = pd.read_csv(u, header=None)
            if df is not None and not df.empty and len(df.columns) >= 3:
                return df, "OK"
        except Exception:
            pass
            
    return None, "連線受阻。請確認已開啟【知道連結的使用者均可檢視】權限。"

st.title("🏛️ 美股細分行業 ETF 深度監控與市場寬度雷達")
st.caption("⚡ 數據底層：Google Sheets 即時同步 | 前端界面：互動式量化雷達儀表板")

df_raw, status_msg = load_sheet_csv(sheet_id, "財報日更新表")

if df_raw is None or df_raw.empty:
    st.error(f"""
    ❌ **無法連線至指定的 Google Sheet！**
    
    **請依序檢查以下 2 個最關鍵原因：**
    1. 試算表右上角【共用】是否設為 **【知道連結的使用者均可檢視 (Viewer)】**。
    2. 目前輸入的 ID 為：`{sheet_id}`
    """)
    st.stop()

def clean_num(val):
    if pd.isna(val): return 0.0
    s = str(val).replace("$", "").replace("%", "").replace(",", "").replace("+", "").strip()
    try: return float(s)
    except: return 0.0

# -------------------------------------------------------------
# 1. 解析宏觀大盤指標
# -------------------------------------------------------------
spy_p, spy_c = 0.0, 0.0
qqq_p, qqq_c = 0.0, 0.0
iwm_p, iwm_c = 0.0, 0.0
dia_p, dia_c = 0.0, 0.0

for r_idx in range(min(6, len(df_raw))):
    row_vals = [str(x).strip() for x in df_raw.iloc[r_idx].values]
    for c_idx, val in enumerate(row_vals):
        if "SPY" in val and c_idx + 2 < len(row_vals):
            spy_p = clean_num(row_vals[c_idx+1])
            spy_c = clean_num(row_vals[c_idx+2])
        elif "QQQ" in val and c_idx + 2 < len(row_vals):
            qqq_p = clean_num(row_vals[c_idx+1])
            qqq_c = clean_num(row_vals[c_idx+2])
        elif "IWM" in val and c_idx + 2 < len(row_vals):
            iwm_p = clean_num(row_vals[c_idx+1])
            iwm_c = clean_num(row_vals[c_idx+2])
        elif "DIA" in val and c_idx + 2 < len(row_vals):
            dia_p = clean_num(row_vals[c_idx+1])
            dia_c = clean_num(row_vals[c_idx+2])

# -------------------------------------------------------------
# 2. 定位主數據表格表頭並構建絕對乾淨唯一的 DataFrame (避免 DuplicateError)
# -------------------------------------------------------------
header_idx = None
for r_idx in range(min(12, len(df_raw))):
    row_text = "".join([str(x) for x in df_raw.iloc[r_idx].values])
    if "ETF 代號" in row_text or "ETF代號" in row_text:
        header_idx = r_idx
        break

if header_idx is None:
    header_idx = 5 if len(df_raw) > 5 else 0

row_header_vals = df_raw.iloc[header_idx].values

def get_col_index(possible_names):
    for p in possible_names:
        clean_p = p.replace(" ", "")
        for idx, val in enumerate(row_header_vals):
            if clean_p in str(val).replace(" ", "").replace("\n", ""):
                return idx
    return None

idx_sym = get_col_index(["ETF代號", "代號", "Symbol"])
idx_name = get_col_index(["ETF名稱", "名稱", "Name"])
idx_sec = get_col_index(["大板塊", "板塊", "Sector"])
idx_ind = get_col_index(["細分子行業", "子行業", "Industry"])
idx_iss = get_col_index(["發行商", "Issuer"])
idx_price = get_col_index(["最新現價", "現價", "Price"])
idx_pct = get_col_index(["當日升幅", "升幅", "漲跌幅"])
idx_ew = get_col_index(["內部等權升幅", "等權升幅"])
idx_spread = get_col_index(["等權差額", "差額", "背離"])
idx_state = get_col_index(["內部升跌狀態", "升跌狀態"])
idx_adv = get_col_index(["上漲佔比", "佔比"])
idx_dist = get_col_index(["距20MA", "偏離度"])
idx_mom = get_col_index(["5日動量", "動量"])
idx_sig = get_col_index(["轉勢雷達信號", "轉勢信號"])
idx_reb = get_col_index(["調倉月份", "調倉"])

records = []
for r_i in range(header_idx + 1, len(df_raw)):
    row = df_raw.iloc[r_i]
    raw_sym = str(row[idx_sym]).strip().upper() if idx_sym is not None and idx_sym < len(row) else ""
    if not (2 <= len(raw_sym) <= 6) or any(k in raw_sym for k in ["ETF", "代號", "--", "NAN"]):
        continue
        
    records.append({
        "symbol": raw_sym,
        "name": str(row[idx_name]).strip() if idx_name is not None and idx_name < len(row) else raw_sym,
        "sector": str(row[idx_sec]).strip() if idx_sec is not None and idx_sec < len(row) else "其他",
        "sub_industry": str(row[idx_ind]).strip() if idx_ind is not None and idx_ind < len(row) else "其他",
        "issuer": str(row[idx_iss]).strip() if idx_iss is not None and idx_iss < len(row) else "--",
        "close_price": clean_num(row[idx_price]) if idx_price is not None and idx_price < len(row) else 0.0,
        "pct_change": clean_num(row[idx_pct]) if idx_pct is not None and idx_pct < len(row) else 0.0,
        "equal_weight_return": clean_num(row[idx_ew]) if idx_ew is not None and idx_ew < len(row) else 0.0,
        "ew_vs_cap_spread": clean_num(row[idx_spread]) if idx_spread is not None and idx_spread < len(row) else 0.0,
        "adv_dec_text": str(row[idx_state]).strip() if idx_state is not None and idx_state < len(row) else "--",
        "advancing_ratio": clean_num(row[idx_adv]) if idx_adv is not None and idx_adv < len(row) else 0.0,
        "dist_20ma": clean_num(row[idx_dist]) if idx_dist is not None and idx_dist < len(row) else 0.0,
        "momentum_5d": clean_num(row[idx_mom]) if idx_mom is not None and idx_mom < len(row) else 0.0,
        "reversal_signal_flag": str(row[idx_sig]).strip() if idx_sig is not None and idx_sig < len(row) else "常規波動",
        "調倉月份": str(row[idx_reb]).strip() if idx_reb is not None and idx_reb < len(row) else "--"
    })

df_metrics = pd.DataFrame(records)

# 確保欄位名稱 100% 唯一
df_metrics = df_metrics.loc[:, ~df_metrics.columns.duplicated()].copy()

top_c1, top_c2 = st.columns([8, 2])
with top_c2:
    if st.button("🔄 刷新 Google Sheet 數據", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# -------------------------------------------------------------
# 📋 財報日更新表
# -------------------------------------------------------------
st.markdown("## 📋 財報日更新表")
st.caption("即時監控 Universe 內各 ETF 底層持股更新狀態、調倉週期及內部升跌情況：")
disp_cols = ["symbol", "name", "issuer", "sector", "sub_industry", "adv_dec_text", "reversal_signal_flag", "調倉月份"]
st.dataframe(df_metrics[disp_cols].rename(columns={
    "symbol": "ETF 代號", "name": "ETF 名稱", "issuer": "發行商", "sector": "大板塊",
    "sub_industry": "細分子行業", "adv_dec_text": "內部升跌狀態", "reversal_signal_flag": "轉勢信號", "調倉月份": "官方調倉月份"
}), use_container_width=True, height=220)

st.markdown("---")

# -------------------------------------------------------------
# A. 全局市場層 (Macro Breadth)
# -------------------------------------------------------------
st.markdown("## 🌐 A. 全局市場層 (Macro Breadth)")
m_c1, m_c2, m_c3, m_c4 = st.columns(4)
m_c1.metric("標普 500 (SPY)", f"${spy_p:.2f}" if spy_p > 0 else "--", delta=f"{spy_c:+.2f}%" if spy_c != 0 else None)
m_c2.metric("納指 100 (QQQ)", f"${qqq_p:.2f}" if qqq_p > 0 else "--", delta=f"{qqq_c:+.2f}%" if qqq_c != 0 else None)
m_c3.metric("羅素 2000 (IWM)", f"${iwm_p:.2f}" if iwm_p > 0 else "--", delta=f"{iwm_c:+.2f}%" if iwm_c != 0 else None)
m_c4.metric("道瓊斯 (DIA)", f"${dia_p:.2f}" if dia_p > 0 else "--", delta=f"{dia_c:+.2f}%" if dia_c != 0 else None)

sectors_list = ['XLK','XLV','XLF','XLI','XLY','XLP','XLE','XLB','XLU','XLRE','XLC']
df_sectors = df_metrics[df_metrics["symbol"].isin(sectors_list)].copy()

if not df_sectors.empty and "pct_change" in df_sectors.columns:
    st.markdown("#### 🧭 11 大核心板塊 (Sectors) 當日資金流向熱力分佈")
    
    # 傳給 Plotly 之前明確去重欄位與索引
    clean_sectors = df_sectors[["symbol", "pct_change", "name"]].copy().reset_index(drop=True)
    clean_sectors = clean_sectors.sort_values(by="pct_change", ascending=False)
    
    fig_sector = px.bar(
        clean_sectors,
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

# -------------------------------------------------------------
# C. 轉勢雷達 (Reversal Radar)
# -------------------------------------------------------------
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
                     f"• 內部狀況: **{r['adv_dec_text']}**")
else:
    st.success("✅ 今日 Universe 內暫未發現極端轉勢異動，市場維持現有趨勢。")

st.markdown("---")

# -------------------------------------------------------------
# B. 細分子行業篩選層 (Sub-Industry Screener)
# -------------------------------------------------------------
st.markdown("## 🔬 B. 細分子行業篩選層 (Sub-Industry Screener)")

STANDARD_11_SECTORS = [
    "資訊科技", "通信服務", "非必需消費", "必需消費", "醫療保健",
    "金融", "工業", "能源", "原材料", "公用事業", "房地產"
]
avail_secs = [s for s in STANDARD_11_SECTORS if s in df_metrics["sector"].unique().tolist()] or STANDARD_11_SECTORS
sel_sectors = st.sidebar.multiselect("選擇大板塊 (GICS 11 大標準分類):", STANDARD_11_SECTORS, default=avail_secs)

sort_by = st.sidebar.selectbox("動量 / 均線排行 (Sort By):", [
    "當日升幅 (pct_change)", "5 日動量 (momentum_5d)",
    "距離 20MA 偏離度 (dist_20ma)", "內部上漲比率 (advancing_ratio)"
])

divergence_filter = st.sidebar.selectbox("背離與轉勢過濾:", ["全部", "隱形強勢", "虛胖拉升", "右側爆發", "左側反轉"])
min_adv = st.sidebar.slider("內部最低上漲比例 (%):", 0, 100, 0)
ma20_bias_range = st.sidebar.slider("距 20MA 偏離範圍 (%):", -20.0, 20.0, (-15.0, 15.0))

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

screener_cols = [
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

st.dataframe(view_df[screener_cols].rename(columns=rename_map).style.format({
    "收盤價": "${:.2f}", "當日升幅": "{:+.2f}%", "等權升幅": "{:+.2f}%",
    "等權差額": "{:+.2f}%", "上漲佔比%": "{:.1f}%", "距20MA": "{:+.2f}%", "5日動量": "{:+.2f}%"
}), use_container_width=True, height=420)

# -------------------------------------------------------------
# 💡 內外背離雷達圖 (散點圖)
# -------------------------------------------------------------
st.markdown("---")
st.subheader("💡 內外背離雷達圖 (ETF 當日升幅 vs 等權升幅)")
if not view_df.empty:
    clean_view_scat = view_df.loc[:, ~view_df.columns.duplicated()].copy()
    fig_scat = px.scatter(
        clean_view_scat,
        x="pct_change", y="equal_weight_return",
        text="symbol", color="advancing_ratio",
        color_continuous_scale="RdYlGn",
        size=np.abs(clean_view_scat["ew_vs_cap_spread"]) + 3,
        hover_data=["name", "sub_industry", "adv_dec_text", "reversal_signal_flag"],
        labels={"pct_change": "ETF 當日升幅 (%)", "equal_weight_return": "內部等權升幅 (%)"}
    )
    min_v = min(clean_view_scat["pct_change"].min(), clean_view_scat["equal_weight_return"].min(), -2)
    max_v = max(clean_view_scat["pct_change"].max(), clean_view_scat["equal_weight_return"].max(), 2)
    fig_scat.add_trace(go.Scatter(x=[min_v, max_v], y=[min_v, max_v], mode="lines", line=dict(dash="dash", color="gray"), name="等權 = 市值"))
    fig_scat.update_traces(textposition="top center")
    fig_scat.update_layout(height=480)
    st.plotly_chart(fig_scat, use_container_width=True)

# -------------------------------------------------------------
# 🔎 單一細分 ETF 成分股持股穿透
# -------------------------------------------------------------
st.markdown("---")
st.subheader("🔎 單一細分 ETF 成分股持股穿透 (Holdings Drill-Down)")
all_avail_symbols = df_metrics["symbol"].tolist()
default_target = "XTN" if "XTN" in all_avail_symbols else (all_avail_symbols[0] if all_avail_symbols else None)

if default_target:
    target_etf = st.selectbox("選擇要穿透全量持股的 ETF:", all_avail_symbols, index=all_avail_symbols.index(default_target))
    if target_etf:
        tab_name = f"{target_etf}_持股明細"
        df_drill, _ = load_sheet_csv(sheet_id, tab_name)
        if df_drill is not None and not df_drill.empty:
            h_idx = 0
            for i_row, r_val in df_drill.iterrows():
                row_str = "".join([str(x) for x in r_val.values])
                if "股票代號" in row_str or "代號" in row_str:
                    h_idx = i_row
                    break
            df_drill_clean = df_drill.iloc[h_idx+1:].copy()
            df_drill_clean.columns = [str(c).strip().replace("\n", "") for c in df_drill.iloc[h_idx].values]
            df_drill_clean = df_drill_clean.dropna(subset=[df_drill_clean.columns[0]])
            df_drill_clean = df_drill_clean[df_drill_clean[df_drill_clean.columns[0]].astype(str).str.len() <= 6]
            
            st.write(f"**{target_etf}** 底層持股清單（來自 Google Sheet【{tab_name}】分頁，共展示 **{len(df_drill_clean)} 隻**成分股）：")
            st.dataframe(df_drill_clean, use_container_width=True, height=350)
        else:
            st.info(f"ℹ️ Google Sheet 尚未建立【{tab_name}】分頁。請在試算表的「ETF_空白快速新增模板」輸入 {target_etf} 並點擊按鈕生成！")
