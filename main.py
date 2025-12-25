import requests
import pandas as pd
from datetime import datetime, timedelta
import os

# =========================
# CONFIG
# =========================
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

if not FINNHUB_API_KEY or not BOT_TOKEN or not CHAT_ID:
    raise Exception("Environment variables missing")

# =========================
# FILES
# =========================
TRADE_LOG = "paper_trades.csv"

# =========================
# NSE HOLIDAYS (update yearly)
# =========================
NSE_HOLIDAYS = [
    "2025-01-26",
    "2025-03-29",
    "2025-08-15",
    "2025-10-02",
    "2025-11-01",
]

# =========================
# TELEGRAM
# =========================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg})

# =========================
# FINNHUB DATA
# =========================
def get_price_history(symbol):
    to_time = int(datetime.now().timestamp())
    from_time = int((datetime.now() - timedelta(days=365)).timestamp())
    url = (
        "https://finnhub.io/api/v1/stock/candle"
        f"?symbol={symbol}&resolution=D&from={from_time}&to={to_time}&token={FINNHUB_API_KEY}"
    )
    r = requests.get(url).json()
    if r.get("s") != "ok":
        return None
    return pd.DataFrame({
        "Close": r["c"],
        "High": r["h"],
        "Low": r["l"]
    })

def get_fundamentals(symbol):
    url = (
        "https://finnhub.io/api/v1/stock/metric"
        f"?symbol={symbol}&metric=all&token={FINNHUB_API_KEY}"
    )
    r = requests.get(url).json()
    return r.get("metric", {})

# =========================
# INDICATORS
# =========================
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(period).mean() / loss.rolling(period).mean()
    return 100 - (100 / (1 + rs))

def calculate_macd(series):
    exp1 = series.ewm(span=12, adjust=False).mean()
    exp2 = series.ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def calculate_atr(high, low, close, period=14):
    hl = high - low
    hc = (high - close.shift()).abs()
    lc = (low - close.shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.rolling(period).mean()

# =========================
# AI DECISION (MID/SMALLCAP)
# =========================
def ai_decision(symbol):
    hist = get_price_history(symbol)
    if hist is None or hist.empty:
        return None

    fundamentals = get_fundamentals(symbol)

    mcap = fundamentals.get("marketCapitalization")
    if not mcap or mcap > 10000:   # exclude large cap
        return None

    price = hist["Close"].iloc[-1]
    rsi = calculate_rsi(hist["Close"]).iloc[-1]
    macd, signal = calculate_macd(hist["Close"])
    atr = calculate_atr(hist["High"], hist["Low"], hist["Close"]).iloc[-1]

    roe = fundamentals.get("roe")
    debt = fundamentals.get("debtToEquity")
    margin = fundamentals.get("profitMarginTTM")

    score = 0
    if roe and roe > 0.15: score += 10
    if debt and debt < 0.5: score += 10
    if margin and margin > 0.1: score += 10
    if rsi < 35 and macd.iloc[-1] > signal.iloc[-1]: score += 20

    if score >= 30:
        action = "🟢 BUY"
        target = round(price + atr * 1.8, 2)
        stop_loss = round(price - atr * 1.0, 2)
    else:
        return None

    return {
        "symbol": symbol.replace("NSE:", ""),
        "price": round(price, 2),
        "rsi": round(rsi, 2),
        "atr": round(atr, 2),
        "score": score,
        "action": action,
        "target": target,
        "stop_loss": stop_loss
    }

# =========================
# PAPER TRADING
# =========================
def log_trade(res):
    exists = os.path.exists(TRADE_LOG)
    with open(TRADE_LOG, "a") as f:
        if not exists:
            f.write("Date,Stock,Entry,Target,StopLoss,Status\n")
        f.write(
            f"{datetime.now().date()},{res['symbol']},{res['price']},"
            f"{res['target']},{res['stop_loss']},OPEN\n"
        )

# =========================
# WEEKLY REPORT
# =========================
def weekly_report():
    if not os.path.exists(TRADE_LOG):
        return "📊 ఈ వారం ట్రేడ్స్ లేవు."

    df = pd.read_csv(TRADE_LOG)
    total = len(df)
    return f"""
📊 వారపు Paper Trading Report

మొత్తం ట్రేడ్స్: {total}

గమనిక:
ఇది learning / paper trading కోసం మాత్రమే.
"""

# =========================
# TELUGU MESSAGE
# =========================
def telugu_msg(res):
    return f"""
🟢 కొనడానికి అనుకూలమైన స్టాక్

స్టాక్: {res['symbol']}
ధర: ₹{res['price']}
RSI: {res['rsi']}
ATR: {res['atr']}

🎯 టార్గెట్: ₹{res['target']}
🛑 స్టాప్ లాస్: ₹{res['stop_loss']}

⏰ కొనుగోలు సమయం:
9:15 – 9:30 AM

⚠️ మార్కెట్ ఓపెన్ తర్వాత మాత్రమే కొనండి
"""

# =========================
# MAIN
# =========================
def run_scan():
    today = datetime.now().strftime("%Y-%m-%d")

    if today in NSE_HOLIDAYS:
        send_telegram("📅 ఈ రోజు NSE మార్కెట్ హాలిడే.")
        return

    df = pd.read_csv("nse_symbols.csv")
    buys = []

    for _, row in df.iterrows():
        symbol = f"NSE:{row.iloc[0]}"
        try:
            res = ai_decision(symbol)
            if res:
                buys.append(res)
        except:
            pass

    buys = sorted(buys, key=lambda x: x["score"], reverse=True)[:3]

    if not buys:
        send_telegram("🟡 ఈ రోజు స్పష్టమైన BUY అవకాశాలు లేవు.")
        return

    send_telegram("📈 ఈ రోజు Top BUY స్టాక్స్\n")

    for res in buys:
        send_telegram(telugu_msg(res))
        log_trade(res)

# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    if datetime.now().weekday() == 6:  # Sunday
        send_telegram(weekly_report())
    else:
        run_scan()
