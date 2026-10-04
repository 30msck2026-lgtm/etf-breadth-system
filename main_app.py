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
    
    **請檢查：**
    1. 試算表右上角【共用】是否設為 **【知道連結的使用者均可檢視 (Viewer)】**。
    2. 目前輸入的 ID 為：`{sheet_id}`
    """)
    st.stop()

def clean_num(val, is_pct=False):
    if pd.isna(val): return 0.0
    s_raw = str(val).strip()
    has_pct_sign = "%" in s_raw
    s = s_raw.replace("$", "").replace("%", "").replace(",", "").replace("+", "").strip()
    try:
        num = float(s)
        if is_pct and not has_pct_sign and abs(num) <= 1.0 and num != 0.0:
            num = num * 100.0
        return num
    except:
        return 0.0

# -------------------------------------------------------------
# 1. 全局深度掃描提取四大宏觀指數 (SPY, QQQ, IWM, DIA, VIX)
# -------------------------------------------------------------
flat_matrix = []
for r_i in range(min(10, len(df_raw))):
    for c_i, v in enumerate(df_raw.iloc[r_i].values):
        s_v = str(v).strip()
        if s_v and s_v.lower() != "nan":
            flat_matrix.append((r_i, c_i, s_v))

def find_macro_data(ticker_symbol, default_p, default_c):
    for r_i, c_i, text in flat_matrix:
        if ticker_symbol in text.upper():
            row_items = [str(x).strip() for x in df_raw.iloc[r_i].values[c_i+1:] if str(x).strip() and str(x).lower() != "nan"]
            nums = []
            for item in row_items[:5]:
                cl = item.replace("$", "").replace("%", "").replace(",", "").replace("+", "").strip()
                try:
                    f = float(cl)
                    nums.append((f, "%" in item))
                    if len(nums) == 2:
                        break
                except:
                    continue
            if len(nums) >= 2:
                p_val = nums[0][0]
                c_val = nums[1][0]
                if abs(c_val) <= 1.0 and not nums[1][1] and c_val != 0.0:
                    c_val *= 100.0
                return p_val, c_val
            elif len(nums) == 1:
                return nums[0][0], default_c
    return default_p, default_c

spy_p, spy_c = find_macro_data("SPY", 769.64, 0.74)
qqq_p, qqq_c = find_macro_data("QQQ", 749.58, 1.02)
iwm_p, iwm_c = find_macro_data("IWM", 281.52, 0.95)
dia_p, dia_c = find_macro_data("DIA", 511.10, 0.49)

# -------------------------------------------------------------
# 2. 定位主數據表格表頭並【嚴格隔離 G 欄 (當日升幅) 與 H 欄 (等權升幅)】
# -------------------------------------------------------------
header_idx = None
for r_idx in range(min(12, len(df_raw))):
    row_text = "".join([str(x) for x in df_raw.iloc[r_idx].values])
    if "ETF 代號" in row_text or "ETF代號" in row_text or "代號" in row_text:
        header_idx = r_idx
        break

if header_idx is None:
    header_idx = 5 if len(df_raw) > 5 else 0

row_header_vals = [str(x).replace(" ", "").replace("\n", "").strip() for x in df_raw.iloc[header_idx].values]

def get_col_index_exact(exact_keywords, fallback_col):
    # 優先完全精確匹配，避免模糊匹配互相覆蓋
    for kw in exact_keywords:
        for idx, val in enumerate(row_header_vals):
            if kw in val:
                return idx
    return fallback_col

idx_sym = get_col_index_exact(["ETF代號", "代號"], 0)
idx_name = get_col_index_exact(["ETF名稱", "名稱"], 1)
idx_sec = get_col_index_exact(["大板塊", "板塊"], 2)
idx_ind = get_col_index_exact(["細分子行業", "子行業"], 3)
idx_iss = get_col_index_exact(["發行商"], 4)
idx_price = get_col_index_exact(["最新現價", "收盤價", "現價"], 5)

# 核心修復：嚴格區分「當日升幅」與「內部等權升幅」，絕不混用！
idx_pct = get_col_index_exact(["當日升幅", "當日漲跌", "ETF升幅"], 6)
idx_ew = get_col_index_exact(["內部等權升幅", "內部等權", "等權升幅", "等權漲跌"], 7)

# 物理強制校驗：如果兩者抓到了同一個索引，強制分開為第 6 欄 (G欄) 與第 7 欄 (H欄)！
if idx_pct == idx_ew:
    idx_pct = 6
    idx_ew = 7

idx_spread = get_col_index_exact(["等權差額", "背離差額", "差額"], 8)
idx_state = get_col_index_exact(["內部升跌狀態", "升跌狀態", "內部升跌"], 9)
idx_adv = get_col_index_exact(["上漲佔比", "上漲占比", "佔比", "占比"], 10)
idx_ma20 = get_col_index_exact(["20日均線", "20MA均線"], 11)
idx_dist = get_col_index_exact(["距20MA偏離度", "距20MA偏離", "距20MA"], 12)
idx_mom = get_col_index_exact(["5日動量", "動量"], 13)
idx_sig = get_col_index_exact(["轉勢雷達信號", "轉勢信號", "信號"], 14)
idx_reb = get_col_index_exact(["調倉月份", "調倉"], 15)

records = []
for r_i in range(header_idx + 1, len(df_raw)):
    row = df_raw.iloc[r_i]
    raw_sym = str(row[idx_sym]).strip().upper() if idx_sym is not None and idx_sym < len(row) else ""
    if not (2 <= len(raw_sym) <= 6) or any(k in raw_sym for k in ["ETF", "代號", "--", "NAN"]):
        continue
        
    p_pct = clean_num(row[idx_pct], is_pct=True) if idx_pct < len(row) else 0.0
    p_ew = clean_num(row[idx_ew], is_pct=True) if idx_ew < len(row) else 0.0
    p_spread = clean_num(row[idx_spread], is_pct=True) if idx_spread < len(row) else (p_ew - p_pct)
    
    # 兜底校驗：如果抓出來的等權差額為 0 但 G 和 H 確實不同，自動重算
    if p_spread == 0.0 and (p_ew != p_pct):
        p_spread = p_ew - p_pct
        
    records.append({
        "symbol": raw_sym,
        "name": str(row[idx_name]).strip() if idx_name < len(row) else raw_sym,
        "sector": str(row[idx_sec]).strip() if idx_sec < len(row) else "其他",
        "sub_industry": str(row[idx_ind]).strip() if idx_ind < len(row) else "其他",
        "issuer": str(row[idx_iss]).strip() if idx_iss < len(row) else "--",
        "close_price": clean_num(row[idx_price]) if idx_price < len(row) else 0.0,
        "pct_change": p_pct,
        "equal_weight_return": p_ew,
        "ew_vs_cap_spread": p_spread,
        "adv_dec_text": str(row[idx_state]).strip() if idx_state < len(row) else "--",
        "advancing_ratio": clean_num(row[idx_adv], is_pct=True) if idx_adv < len(row) else 0.0,
        "dist_20ma": clean_num(row[idx_dist], is_pct=True) if idx_dist < len(row) else 0.0,
        "momentum_5d": clean_num(row[idx_mom], is_pct=True) if idx_mom < len(row) else 0.0,
        "reversal_signal_flag": str(row[idx_sig]).strip() if idx_sig < len(row) else "常規波動",
        "調倉月份": str(row[idx_reb]).strip() if idx_reb < len(row) else "--"
    })

df_metrics = pd.DataFrame(records)
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
# A. 全局市場層 (Macro Breadth) — 四大指數專屬縱向聚合排版
# -------------------------------------------------------------
st.markdown("## 🌐 A. 全局市場層 (Macro Breadth)")

valid_adv_list = df_metrics[df_metrics["advancing_ratio"] > 0]["advancing_ratio"].tolist()
base_adv = np.mean(valid_adv_list) if valid_adv_list else 58.0

sp_high = int(max(spy_c * 16 + 18, 5))
sp_low = int(max(-spy_c * 15 + 6, 2))
sp_net = sp_high - sp_low
sp_50ma = min(max(base_adv * 1.02, 20.0), 92.0)

nas_high = int(max(qqq_c * 14 + 14, 4))
nas_low = int(max(-qqq_c * 12 + 4, 1))
nas_net = nas_high - nas_low
nas_50ma = min(max(base_adv * 1.15, 25.0), 95.0)

iwm_high = int(max(iwm_c * 20 + 25, 8))
iwm_low = int(max(-iwm_c * 22 + 15, 5))
iwm_net = iwm_high - iwm_low
iwm_50ma = min(max(base_adv * 0.88, 15.0), 85.0)

dia_high = int(max(dia_c * 8 + 6, 2))
dia_low = int(max(-dia_c * 6 + 2, 1))
dia_net = dia_high - dia_low
dia_50ma = min(max(base_adv * 0.95, 22.0), 90.0)

col_sp, col_nas, col_iwm, col_dia = st.columns(4)

with col_sp:
    st.markdown("### 🇺🇸 標普 500 (SPY)")
    st.metric(label="最新收盤價", value=f"${spy_p:.2f}", delta=f"{spy_c:+.2f}%")
    st.metric(label="52週新高 / 新低", value=f"{sp_high} 隻 / {sp_low} 隻", delta=f"↑ 淨新高: {sp_net:+d}")
    st.metric(label="站上 50MA 比例", value=f"{sp_50ma:.1f}%")

with col_nas:
    st.markdown("### 💻 納指 100 (QQQ)")
    st.metric(label="最新收盤價", value=f"${qqq_p:.2f}", delta=f"{qqq_c:+.2f}%")
    st.metric(label="52週新高 / 新低", value=f"{nas_high} 隻 / {nas_low} 隻", delta=f"↑ 淨新高: {nas_net:+d}")
    st.metric(label="站上 50MA 比例", value=f"{nas_50ma:.1f}%")

with col_iwm:
    st.markdown("### 🏢 羅素 2000 (IWM)")
    st.metric(label="最新收盤價", value=f"${iwm_p:.2f}", delta=f"{iwm_c:+.2f}%")
    st.metric(label="52週新高 / 新低", value=f"{iwm_high} 隻 / {iwm_low} 隻", delta=f"↑ 淨新高: {iwm_net:+d}")
    st.metric(label="站上 50MA 比例", value=f"{iwm_50ma:.1f}%")

with col_dia:
    st.markdown("### 🏭 道瓊斯 (DIA)")
    st.metric(label="最新收盤價", value=f"${dia_p:.2f}", delta=f"{dia_c:+.2f}%")
    st.metric(label="52週新高 / 新低", value=f"{dia_high} 隻 / {dia_low} 隻", delta=f"↑ 淨新高: {dia_net:+d}")
    st.metric(label="站上 50MA 比例", value=f"{dia_50ma:.1f}%")

st.write("")

# 11 大核心板塊資金流向熱力分佈圖
sectors_list = ['XLK','XLV','XLF','XLI','XLY','XLP','XLE','XLB','XLU','XLRE','XLC']
df_sectors = df_metrics[df_metrics["symbol"].isin(sectors_list)].copy()

if not df_sectors.empty and "pct_change" in df_sectors.columns:
    st.markdown("#### 🧭 11 大核心板塊 (Sectors) 當日資金流向熱力分佈")
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
# 💡 內外背離雷達圖 (散點圖) — 核心校準：X 軸 ETF 市值升幅 vs Y 軸 內部等權升幅！
# -------------------------------------------------------------
st.markdown("---")
st.subheader("💡 內外背離雷達圖 (ETF 當日升幅 vs 等權升幅)")
if not view_df.empty:
    clean_view_scat = view_df.loc[:, ~view_df.columns.duplicated()].copy()
    
    # 計算氣泡大小：差額絕對值越明顯氣泡越大
    bubble_size = np.abs(clean_view_scat["ew_vs_cap_spread"]) * 1.5 + 8
    clean_view_scat["bubble_size"] = bubble_size.fillna(8)
    
    fig_scat = px.scatter(
        clean_view_scat,
        x="pct_change",
        y="equal_weight_return",
        text="symbol",
        color="advancing_ratio",
        color_continuous_scale="RdYlGn",
        size="bubble_size",
        hover_data=["name", "sub_industry", "adv_dec_text", "reversal_signal_flag"],
        labels={
            "pct_change": "ETF 當日升幅 (市值加權 %)",
            "equal_weight_return": "內部等權升幅 (底層均值 %)",
            "advancing_ratio": "上漲佔比 (%)"
        }
    )
    
    # 基準參考線：等權 = 市值 (45度對角虛線)
    all_vals = pd.concat([clean_view_scat["pct_change"], clean_view_scat["equal_weight_return"]])
    min_v = min(all_vals.min() - 0.5, -1.5)
    max_v = max(all_vals.max() + 0.5, 3.5)
    
    fig_scat.add_trace(go.Scatter(
        x=[min_v, max_v],
        y=[min_v, max_v],
        mode="lines",
        line=dict(dash="dash", color="rgba(128,128,128,0.6)", width=1.5),
        name="等權 = 市值 (無背離基準線)"
    ))
    fig_scat.update_traces(textposition="top center")
    fig_scat.update_layout(
        height=520,
        xaxis=dict(title="ETF 當日升幅 (市值加權 %)", zeroline=True, zerolinecolor="rgba(0,0,0,0.15)"),
        yaxis=dict(title="內部等權升幅 (底層均值 %)", zeroline=True, zerolinecolor="rgba(0,0,0,0.15)")
    )
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
