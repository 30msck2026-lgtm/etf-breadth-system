import sqlite3
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_FILE = os.path.join(DATA_DIR, "etf_system.db")

def get_connection():
    os.makedirs(DATA_DIR, exist_ok=True)
    return sqlite3.connect(DB_FILE)

def init_database():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS etf_metadata (
        symbol TEXT PRIMARY KEY,
        name TEXT,
        sector TEXT,
        sub_industry TEXT,
        issuer TEXT,
        benchmark TEXT
    )""")
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS etf_holdings (
        etf_symbol TEXT,
        stock_symbol TEXT,
        weight REAL,
        updated_date TEXT,
        PRIMARY KEY (etf_symbol, stock_symbol)
    )""")
    
    # 專門記錄每個 ETF 的更新狀態總表 (供「財報日更新表」查詢)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS etf_sync_status (
        symbol TEXT PRIMARY KEY,
        name TEXT,
        issuer TEXT,
        holdings_count INTEGER,
        last_updated_date TEXT,
        download_success TEXT,
        source_note TEXT
    )""")
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS market_daily_metrics (
        date TEXT,
        symbol TEXT,
        close_price REAL,
        pct_change REAL,
        dist_20ma REAL,
        dist_50ma REAL,
        dist_200ma REAL,
        equal_weight_return REAL,
        ew_vs_cap_spread REAL,
        advancing_count INTEGER,
        declining_count INTEGER,
        total_stocks_count INTEGER,
        advancing_ratio REAL,
        above_20ma_ratio REAL,
        above_50ma_ratio REAL,
        momentum_5d REAL,
        momentum_20d REAL,
        volume_ratio REAL,
        ratio_vs_benchmark REAL,
        reversal_signal_flag TEXT,
        PRIMARY KEY (date, symbol)
    )""")
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS macro_breadth (
        date TEXT,
        index_name TEXT,
        new_highs_count INTEGER,
        new_lows_count INTEGER,
        net_highs_lows INTEGER,
        pct_above_50ma REAL,
        pct_above_200ma REAL,
        PRIMARY KEY (date, index_name)
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS system_health_logs (
        timestamp TEXT,
        log_type TEXT,
        target TEXT,
        status TEXT,
        message TEXT
    )""")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_database()
    print("Database initialized successfully with etf_sync_status.")
