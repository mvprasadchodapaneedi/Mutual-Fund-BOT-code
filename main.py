import requests
import os
from datetime import datetime

# =========================
# CONFIG (GitHub Secrets)
# =========================
BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

# =========================
# MUTUAL FUND LIST (STATIC)
# =========================
# Scheme Code from mfapi.in
FUNDS = {
    "Parag Parikh Flexi Cap": "122639",
    "Motilal Oswal Midcap": "127042",
    "Kotak Emerging Equity": "120841",
    "Nippon India Small Cap": "118778",
    "ICICI Bluechip": "120586",
    "HDFC Balanced Advantage": "119551",
    "UTI Nifty 50 Index": "120716"
}

# =========================
# GOALS CONFIG
# =========================
GOALS = {
    "Daughter Goal (16 yrs)": {
        "sip": 19000,
        "funds": [
            "Parag Parikh Flexi Cap",
            "ICICI Bluechip",
            "Motilal Oswal Midcap",
            "HDFC Balanced Advantage"
        ]
    },
    "Son Goal (23 yrs)": {
        "sip": 8000,
        "funds": [
            "Motilal Oswal Midcap",
            "Kotak Emerging Equity",
            "Nippon India Small Cap",
            "Parag Parikh Flexi Cap"
        ]
    },
    "Retirement Goal": {
        "sip": 7500,
        "funds": [
            "Parag Parikh Flexi Cap",
            "UTI Nifty 50 Index",
            "HDFC Balanced Advantage"
        ]
    }
}

# =========================
# FETCH NAV DATA
# =========================
def get_fund_return(scheme_code, months=12):
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    r = requests.get(url, timeout=10).json()

    data = r.get("data", [])
    if len(data) < months * 20:
        return None

    nav_now = float(data[0]["nav"])
    nav_old = float(data[months * 20]["nav"])

    return round(((nav_now - nav_old) / nav_old) * 100, 2)

# =========================
# TELEGRAM
# =========================
def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg})

# =========================
# ANALYSIS ENGINE
# =========================
def analyze_fund(fund_name):
    scheme = FUNDS[fund_name]
    ret_1y = get_fund_return(scheme, 12)
    ret_3y = get_fund_return(scheme, 36)

    if ret_1y is None or ret_3y is None:
        return "DATA NOT AVAILABLE", None, None

    if ret_1y > 12 and ret_3y > 14:
        signal = "🟢 SIP కొనసాగించండి"
    elif ret_1y < 5:
        signal = "⚠️ గమనించాలి"
    else:
        signal = "🟡 HOLD"

    return signal, ret_1y, ret_3y

# =========================
# MAIN BOT LOGIC
# =========================
def run_bot():
    today = datetime.now().strftime("%d-%m-%Y")

    for goal, info in GOALS.items():
        message = f"""
🎯 లక్ష్యం: {goal}
📅 తేదీ: {today}
💰 Monthly SIP: ₹{info['sip']}

"""

        for fund in info["funds"]:
            signal, r1, r3 = analyze_fund(fund)

            if r1 is None:
                message += f"❌ {fund}: డేటా లేదు\n"
                continue

            message += f"""
📌 ఫండ్: {fund}
1Y Return: {r1}%
3Y Return: {r3}%
సూచన: {signal}
"""

        message += "\n-----------------------\n"
        send_telegram(message)

# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    run_bot()
