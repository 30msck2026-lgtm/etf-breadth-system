# 美股標準 GICS 11 大板塊母 ETF 及細分行業 ETF 映射表
SECTOR_BENCHMARKS = ["XLK", "XLV", "XLF", "XLI", "XLY", "XLP", "XLE", "XLB", "XLU", "XLRE", "XLC"]

ETF_UNIVERSE = [
    # --- 11 大標準板塊母基金 (用於熱力圖與板塊基準) ---
    {"ticker": "XLK", "name": "科技板塊 (SPDR)", "sector": "資訊科技", "industry": "板塊基準", "issuer": "SPDR", "benchmark": "SPY"},
    {"ticker": "XLC", "name": "通信服務板塊 (SPDR)", "sector": "通信服務", "industry": "板塊基準", "issuer": "SPDR", "benchmark": "SPY"},
    {"ticker": "XLY", "name": "非必需消費板塊 (SPDR)", "sector": "非必需消費", "industry": "板塊基準", "issuer": "SPDR", "benchmark": "SPY"},
    {"ticker": "XLP", "name": "必需消費板塊 (SPDR)", "sector": "必需消費", "industry": "民生必需", "issuer": "SPDR", "benchmark": "SPY"},
    {"ticker": "XLV", "name": "醫療保健板塊 (SPDR)", "sector": "醫療保健", "industry": "板塊基準", "issuer": "SPDR", "benchmark": "SPY"},
    {"ticker": "XLF", "name": "金融板塊 (SPDR)", "sector": "金融", "industry": "板塊基準", "issuer": "SPDR", "benchmark": "SPY"},
    {"ticker": "XLI", "name": "工業板塊 (SPDR)", "sector": "工業", "industry": "板塊基準", "issuer": "SPDR", "benchmark": "SPY"},
    {"ticker": "XLE", "name": "能源板塊 (SPDR)", "sector": "能源", "industry": "板塊基準", "issuer": "SPDR", "benchmark": "SPY"},
    {"ticker": "XLB", "name": "原材料板塊 (SPDR)", "sector": "原材料", "industry": "板塊基準", "issuer": "SPDR", "benchmark": "SPY"},
    {"ticker": "XLU", "name": "公用事業板塊 (SPDR)", "sector": "公用事業", "industry": "板塊基準", "issuer": "SPDR", "benchmark": "SPY"},
    {"ticker": "XLRE", "name": "房地產板塊 (SPDR)", "sector": "房地產", "industry": "板塊基準", "issuer": "SPDR", "benchmark": "SPY"},

    # 1. 資訊科技
    {"ticker": "SMH", "name": "半導體 (VanEck)", "sector": "資訊科技", "industry": "半導體", "issuer": "VanEck", "benchmark": "XLK"},
    {"ticker": "SOXX", "name": "半導體 (iShares)", "sector": "資訊科技", "industry": "半導體", "issuer": "iShares", "benchmark": "XLK"},
    {"ticker": "IGV", "name": "雲端與軟件", "sector": "資訊科技", "industry": "軟件SaaS", "issuer": "iShares", "benchmark": "XLK"},
    {"ticker": "CIBR", "name": "網絡安全", "sector": "資訊科技", "industry": "網絡安全", "issuer": "First Trust", "benchmark": "XLK"},
    {"ticker": "HACK", "name": "網絡安全 (Amplify)", "sector": "資訊科技", "industry": "網絡安全", "issuer": "Amplify", "benchmark": "XLK"},
    {"ticker": "BOTZ", "name": "AI與機器人", "sector": "資訊科技", "industry": "人工智能", "issuer": "Global X", "benchmark": "XLK"},
    {"ticker": "FINX", "name": "金融科技", "sector": "資訊科技", "industry": "FinTech", "issuer": "Global X", "benchmark": "XLK"},

    # 2. 通信服務
    {"ticker": "FDN", "name": "互聯網指數", "sector": "通信服務", "industry": "互聯網", "issuer": "First Trust", "benchmark": "XLC"},
    {"ticker": "NXTG", "name": "5G與下一代通信", "sector": "通信服務", "industry": "通信網絡", "issuer": "First Trust", "benchmark": "XLC"},
    {"ticker": "PBS", "name": "動態傳媒", "sector": "通信服務", "industry": "傳媒娛樂", "issuer": "Invesco", "benchmark": "XLC"},

    # 3. 非必需消費
    {"ticker": "XHB", "name": "地產建築商 (等權)", "sector": "非必需消費", "industry": "房屋建築", "issuer": "SPDR", "benchmark": "ITB"},
    {"ticker": "ITB", "name": "純住宅營造", "sector": "非必需消費", "industry": "住宅營造", "issuer": "iShares", "benchmark": "XLY"},
    {"ticker": "XRT", "name": "零售業 (等權)", "sector": "非必需消費", "industry": "實體零售", "issuer": "SPDR", "benchmark": "XLY"},
    {"ticker": "PEJ", "name": "休閒娛樂餐飲", "sector": "非必需消費", "industry": "休閒餐飲", "issuer": "Invesco", "benchmark": "XLY"},
    {"ticker": "AWAY", "name": "旅遊科技零售", "sector": "非必需消費", "industry": "旅遊零售", "issuer": "ETFMG", "benchmark": "XLY"},

    # 4. 必需消費
    {"ticker": "KXI", "name": "全球必需消費", "sector": "必需消費", "industry": "生活消費", "issuer": "iShares", "benchmark": "XLP"},
    {"ticker": "PBJ", "name": "食品與飲料", "sector": "必需消費", "industry": "食品飲品", "issuer": "Invesco", "benchmark": "XLP"},

    # 5. 醫療保健
    {"ticker": "XBI", "name": "生物科技 (等權)", "sector": "醫療保健", "industry": "生物科技", "issuer": "SPDR", "benchmark": "IBB"},
    {"ticker": "IBB", "name": "生物科技 (加權)", "sector": "醫療保健", "industry": "生物科技", "issuer": "iShares", "benchmark": "XLV"},
    {"ticker": "IHI", "name": "醫療設備與器材", "sector": "醫療保健", "industry": "醫療器械", "issuer": "iShares", "benchmark": "XLV"},
    {"ticker": "XHE", "name": "醫療裝備 (SPDR)", "sector": "醫療保健", "industry": "醫療裝備", "issuer": "SPDR", "benchmark": "XLV"},
    {"ticker": "XPH", "name": "傳統製藥", "sector": "醫療保健", "industry": "傳統製藥", "issuer": "SPDR", "benchmark": "XLV"},
    {"ticker": "IHF", "name": "醫療服務與醫保", "sector": "醫療保健", "industry": "醫療保險", "issuer": "iShares", "benchmark": "XLV"},

    # 6. 金融
    {"ticker": "KRE", "name": "區域銀行", "sector": "金融", "industry": "區域銀行", "issuer": "SPDR", "benchmark": "KBE"},
    {"ticker": "KBE", "name": "商業大行", "sector": "金融", "industry": "商業銀行", "issuer": "SPDR", "benchmark": "XLF"},
    {"ticker": "IAI", "name": "經紀投行", "sector": "金融", "industry": "投行券商", "issuer": "iShares", "benchmark": "XLF"},
    {"ticker": "KIE", "name": "保險產業", "sector": "金融", "industry": "保險", "issuer": "SPDR", "benchmark": "XLF"},

    # 7. 工業
    {"ticker": "ITA", "name": "國防軍工 (iShares)", "sector": "工業", "industry": "軍工航天", "issuer": "iShares", "benchmark": "XLI"},
    {"ticker": "XAR", "name": "航天軍工 (SPDR)", "sector": "工業", "industry": "軍工航天", "issuer": "SPDR", "benchmark": "XLI"},
    {"ticker": "IYT", "name": "交通運輸", "sector": "工業", "industry": "交運物流", "issuer": "iShares", "benchmark": "XLI"},
    {"ticker": "XTN", "name": "標普交通運輸", "sector": "工業", "industry": "交運物流", "issuer": "SPDR", "benchmark": "XLI"},
    {"ticker": "JETS", "name": "航空航運", "sector": "工業", "industry": "民航客運", "issuer": "US Global", "benchmark": "XLI"},
    {"ticker": "PAVE", "name": "基建工程", "sector": "工業", "industry": "基礎設施", "issuer": "Global X", "benchmark": "XLI"},

    # 8. 能源
    {"ticker": "XOP", "name": "油氣開採 (等權)", "sector": "能源", "industry": "上游勘探", "issuer": "SPDR", "benchmark": "XLE"},
    {"ticker": "OIH", "name": "油服與設備", "sector": "能源", "industry": "油田設備", "issuer": "VanEck", "benchmark": "XLE"},
    {"ticker": "AMLP", "name": "中游管網MLP", "sector": "能源", "industry": "中游管網", "issuer": "Alerian", "benchmark": "XLE"},
    {"ticker": "URA", "name": "鈾礦與核能", "sector": "能源", "industry": "鈾礦能源", "issuer": "Global X", "benchmark": "XLE"},

    # 9. 原材料
    {"ticker": "COPX", "name": "銅礦業", "sector": "原材料", "industry": "銅礦採選", "issuer": "Global X", "benchmark": "XLB"},
    {"ticker": "GDX", "name": "金礦股", "sector": "原材料", "industry": "大型金礦", "issuer": "VanEck", "benchmark": "GLD"},
    {"ticker": "GDXJ", "name": "初級中小型金礦", "sector": "原材料", "industry": "中小型金礦", "issuer": "VanEck", "benchmark": "GDX"},
    {"ticker": "XME", "name": "金屬採礦 (等權)", "sector": "原材料", "industry": "金屬冶煉", "issuer": "SPDR", "benchmark": "XLB"},

    # 10. 公用事業
    {"ticker": "GRID", "name": "智能電網與輸配電", "sector": "公用事業", "industry": "電網設備", "issuer": "First Trust", "benchmark": "XLU"},
    {"ticker": "ICLN", "name": "清潔能源", "sector": "公用事業", "industry": "新能源", "issuer": "iShares", "benchmark": "XLU"},
    {"ticker": "PBW", "name": "清潔能源 (Invesco)", "sector": "公用事業", "industry": "新能源", "issuer": "Invesco", "benchmark": "XLU"},
    {"ticker": "TAN", "name": "太陽能", "sector": "公用事業", "industry": "光伏太陽能", "issuer": "Invesco", "benchmark": "ICLN"},

    # 11. 房地產
    {"ticker": "REZ", "name": "住宅REITs", "sector": "房地產", "industry": "房產信託", "issuer": "iShares", "benchmark": "XLRE"},
    {"ticker": "VNQ", "name": "全美房地產REITs", "sector": "房地產", "industry": "房產信託", "issuer": "Vanguard", "benchmark": "XLRE"}
]
