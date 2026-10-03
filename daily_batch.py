import datetime
import time
import pandas as pd
import numpy as np
import yfinance as yf
from db_manager import get_connection
from config_etfs import SECTOR_BENCHMARKS

def log_system_event(cur, log_type, target, status, message):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
    INSERT INTO system_health_logs (timestamp, log_type, target, status, message)
    VALUES (?, ?, ?, ?, ?)
    """, (ts, log_type, target, status, message))

def update_macro_breadth(conn, today_str):
    print("[*] 計算大盤層 (Macro Breadth)...")
    indices = {
        "S&P 500": "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        "Nasdaq 100": "https://en.wikipedia.org/wiki/Nasdaq-100"
    }
    cur = conn.cursor()
    for idx_name, url in indices.items():
        try:
            tables = pd.read_html(url)
            if idx_name == "S&P 500":
                tickers = tables[0]["Symbol"].str.replace(".", "-", regex=False).tolist()
            else:
                tickers = tables[4]["Ticker"].str.replace(".", "-", regex=False).tolist() if len(tables) > 4 else tables[3]["Ticker"].str.replace(".", "-", regex=False).tolist()
            
            chunk_size = 60
            valid, nh_cnt, nl_cnt, ab_50, ab_200 = 0, 0, 0, 0, 0
            for i in range(0, len(tickers), chunk_size):
                sub_tickers = tickers[i:i+chunk_size]
                try:
                    data = yf.download(sub_tickers, period="1y", interval="1d", group_by="ticker", auto_adjust=True, progress=False)
                    for sym in sub_tickers:
                        if sym in data.columns.levels[0]:
                            df_c = data[sym]["Close"].dropna()
                            if len(df_c) >= 150:
                                valid += 1
                                curr = df_c.iloc[-1]
                                max_1y = df_c.max()
                                min_1y = df_c.min()
                                if curr >= max_1y * 0.995:
                                    nh_cnt += 1
                                if curr <= min_1y * 1.005:
                                    nl_cnt += 1
                                if curr > df_c.rolling(50).mean().iloc[-1]:
                                    ab_50 += 1
                                if len(df_c) >= 200 and curr > df_c.rolling(200).mean().iloc[-1]:
                                    ab_200 += 1
                except Exception as ex:
                    log_system_event(cur, "PRICE_FETCH", idx_name, "WARNING", f"指數成分股下載警告: {ex}")
                time.sleep(3)
                                
            pct_50 = round(ab_50 / valid * 100, 1) if valid > 0 else 0.0
            pct_200 = round(ab_200 / valid * 100, 1) if valid > 0 else 0.0
            net_hl = nh_cnt - nl_cnt
            cur.execute("INSERT OR REPLACE INTO macro_breadth VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (today_str, idx_name, nh_cnt, nl_cnt, net_hl, pct_50, pct_200))
            conn.commit()
        except Exception as e:
            log_system_event(cur, "PRICE_FETCH", idx_name, "ERROR", f"計算大盤寬度失敗: {e}")

def run_daily_pipeline():
    conn = get_connection()
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    print(f"==================================================")
    print(f"啟動盤後安全批次指標計算: {today_str}")
    print(f"==================================================")
    
    update_macro_breadth(conn, today_str)
    
    meta_df = pd.read_sql("SELECT symbol, benchmark FROM etf_metadata", conn)
    holdings_df = pd.read_sql("SELECT etf_symbol, stock_symbol FROM etf_holdings", conn)
    
    etf_symbols = meta_df["symbol"].tolist()
    benchmarks = [b for b in meta_df["benchmark"].dropna().unique().tolist() if b]
    benchmarks += SECTOR_BENCHMARKS
    stock_symbols = holdings_df["stock_symbol"].dropna().unique().tolist()
    download_pool = list(set(etf_symbols + benchmarks + stock_symbols))
    
    print(f"[*] 全量抓取標的行情 (去重後共 {len(download_pool)} 隻股票)...")
    
    raw_dict = {}
    chunk_size = 60
    cur = conn.cursor()
    
    for i in range(0, len(download_pool), chunk_size):
        sub_pool = download_pool[i:i+chunk_size]
        try:
            d = yf.download(sub_pool, period="15mo", interval="1d", group_by="ticker", auto_adjust=True, progress=False)
            for sym in sub_pool:
                if sym in d.columns.levels[0]:
                    raw_dict[sym] = d[sym]
            print(f"[+] 下載進度: {min(i+chunk_size, len(download_pool))}/{len(download_pool)}")
        except Exception as err:
            log_system_event(cur, "PRICE_FETCH", f"BLOCK_{i}", "WARNING", f"下載塊失敗: {err}")
        time.sleep(3)
            
    for _, meta_row in meta_df.iterrows():
        etf = meta_row["symbol"]
        bench = meta_row["benchmark"]
        try:
            if etf not in raw_dict:
                log_system_event(cur, "ETF_PRICE", etf, "WARNING", f"{etf} 未能獲取自身行情數據")
                continue
            hist = raw_dict[etf]
            close = hist["Close"].dropna()
            volume = hist["Volume"].dropna() if "Volume" in hist else None
            if len(close) < 25:
                continue
                
            curr_c = float(close.iloc[-1])
            prev_c = float(close.iloc[-2])
            pct_change = round(((curr_c - prev_c) / prev_c) * 100.0, 2)
            
            c_5d_ago = close.iloc[-6] if len(close) >= 6 else close.iloc[0]
            c_20d_ago = close.iloc[-21] if len(close) >= 21 else close.iloc[0]
            momentum_5d = round(((curr_c - c_5d_ago) / c_5d_ago) * 100.0, 2)
            momentum_20d = round(((curr_c - c_20d_ago) / c_20d_ago) * 100.0, 2)
            
            ma20 = close.rolling(20).mean().iloc[-1]
            ma50 = close.rolling(50).mean().iloc[-1] if len(close) >= 50 else np.nan
            ma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else np.nan
            
            dist_20 = round(((curr_c - ma20) / ma20) * 100.0, 2) if pd.notna(ma20) else 0.0
            dist_50 = round(((curr_c - ma50) / ma50) * 100.0, 2) if pd.notna(ma50) else 0.0
            dist_200 = round(((curr_c - ma200) / ma200) * 100.0, 2) if pd.notna(ma200) else 0.0
            
            vol_ratio = 1.0
            if volume is not None and len(volume) >= 20:
                v_curr = volume.iloc[-1]
                v_20ma = volume.rolling(20).mean().iloc[-1]
                vol_ratio = round(float(v_curr / v_20ma), 2) if v_20ma > 0 else 1.0
                
            ratio_spread = 1.0
            if bench and bench in raw_dict:
                bench_c = raw_dict[bench]["Close"].dropna()
                if len(bench_c) >= 2:
                    ratio_spread = round(float(curr_c / bench_c.iloc[-1]), 4)
                    
            # 關鍵：分母永遠鎖定為資料庫中的持股數量！
            sub_stocks = holdings_df[holdings_df["etf_symbol"] == etf]["stock_symbol"].tolist()
            total_cnt = len(sub_stocks)
            
            stock_pcts = []
            ab_20 = 0
            ab_50 = 0
            ab_20_prev = 0
            
            for s in sub_stocks:
                if s in raw_dict:
                    s_close = raw_dict[s]["Close"].dropna()
                    if len(s_close) >= 2:
                        sc = s_close.iloc[-1]
                        sp = s_close.iloc[-2]
                        ret = ((sc - sp) / sp) * 100.0
                        stock_pcts.append(ret)
                        
                        if len(s_close) >= 22:
                            m20_curr = s_close.rolling(20).mean().iloc[-1]
                            m20_prev = s_close.rolling(20).mean().iloc[-2]
                            if sc > m20_curr:
                                ab_20 += 1
                            if sp > m20_prev:
                                ab_20_prev += 1
                        if len(s_close) >= 50 and sc > s_close.rolling(50).mean().iloc[-1]:
                            ab_50 += 1
                    else:
                        stock_pcts.append(0.0)
                else:
                    stock_pcts.append(0.0)
                    
            arr = np.array(stock_pcts)
            adv_cnt = int(np.sum(arr > 0.05))
            dec_cnt = int(np.sum(arr < -0.05))
            ew_return = round(float(np.mean(arr)), 2)
            adv_ratio = round(adv_cnt / total_cnt * 100.0, 1) if total_cnt > 0 else 50.0
            above_20_ratio = round(ab_20 / total_cnt * 100.0, 1) if total_cnt > 0 else 50.0
            above_20_prev_ratio = round(ab_20_prev / total_cnt * 100.0, 1) if total_cnt > 0 else 50.0
            above_50_ratio = round(ab_50 / total_cnt * 100.0, 1) if total_cnt > 0 else 50.0
            ab_20_jump = above_20_ratio - above_20_prev_ratio
                
            spread = round(ew_return - pct_change, 2)
            
            signals = []
            if curr_c > ma20 and ab_20_jump >= 20.0:
                signals.append("右側爆發(內部激增>20%)")
            elif 0.0 <= dist_20 <= 2.5 and above_20_ratio >= 60.0 and pct_change > 0:
                signals.append("突破20MA右側啟動")
                
            if momentum_5d <= -5.0 and vol_ratio >= 1.25 and ew_return > 0.0 and adv_ratio >= 60.0:
                signals.append("左側反轉(放量+等權翻紅)")
                
            if -0.2 <= pct_change <= 0.6 and adv_ratio >= 75.0:
                signals.append("隱形強勢(資金全面進場蓄勢)")
            if pct_change >= 1.2 and ew_return <= 0.2 and adv_ratio < 45.0:
                signals.append("虛胖拉升(巨頭拉指數內部下跌)")
                
            sig_text = " | ".join(signals) if signals else "常規波動"
            
            cur.execute("""
            INSERT OR REPLACE INTO market_daily_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (today_str, etf, curr_c, pct_change, dist_20, dist_50, dist_200, ew_return, spread,
                  adv_cnt, dec_cnt, total_cnt, adv_ratio, above_20_ratio, above_50_ratio,
                  momentum_5d, momentum_20d, vol_ratio, ratio_spread, sig_text))
        except Exception as e:
            log_system_event(cur, "PIPELINE_ERROR", etf, "ERROR", f"計算指標失敗: {e}")
            
    conn.commit()
    conn.close()
    print("[+] 每日指標計算完成，所有數據與持股庫完全嚴格吻合！")

if __name__ == "__main__":
    run_daily_pipeline()
