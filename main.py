import math
from datetime import datetime
import requests
import os

# =========================
# TELEGRAM CONFIG
# =========================
BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

# =========================
# GLOBAL ASSUMPTIONS
# =========================
EXPECTED_RETURN = 0.12   # 12% CAGR
INFLATION = 0.06         # 6%
STEP_UP_RATE = 0.10      # 10%

# =========================
# GOALS CONFIG
# =========================
GOALS = [
    {
        "name": "👧 Daughter Education",
        "current_age": 9,
        "target_age": 25,
        "target_amount": 1_00_00_000
    },
    {
        "name": "👦 Son-1 Education",
        "current_age": 2.5,
        "target_age": 26,
        "target_amount": 1_00_00_000
    },
    {
        "name": "👦 Son-2 Education",
        "current_age": 2.5,
        "target_age": 26,
        "target_amount": 1_00_00_000
    },
    {
        "name": "🧓 Retirement",
        "current_age": 38,
        "target_age": 60,
        "target_amount": 1_00_00_000
    }
]

# =========================
# SIP CALCULATOR
# =========================
def calculate_monthly_sip(target, years, rate):
    r = rate / 12
    n = years * 12
    sip = target * r / ((1 + r) ** n - 1)
    return round(sip)

# =========================
# SIP STEP-UP CHECK
# =========================
def stepup_suggestion(current_sip):
    return round(current_sip * (1 + STEP_UP_RATE))

# =========================
# TELEGRAM
# =========================
def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram config missing")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg})

# =========================
# MAIN BOT LOGIC
# =========================
def run_bot():
    final_message = f"📊 *Mutual Fund AI Planner*\n📅 {datetime.now().strftime('%d-%m-%Y')}\n\n"

    for goal in GOALS:
        years_left = goal["target_age"] - goal["current_age"]
        sip = calculate_monthly_sip(
            goal["target_amount"],
            years_left,
            EXPECTED_RETURN
        )

        sip_stepup = stepup_suggestion(sip)

        final_message += f"""
{goal['name']}
🎯 Target: ₹{goal['target_amount']:,}
⏳ Years Left: {years_left}

💰 Required SIP: ₹{sip:,}/month
🔼 Next Year SIP (10% step-up): ₹{sip_stepup:,}

✅ Suggested Funds:
• Equity Mid & Small Cap (70%)
• Flexi Cap / Index (20%)
• Debt / Hybrid (10%)

━━━━━━━━━━━━━━━
"""

    final_message += """
📌 *Important Notes*
• SIP yearly 10% step-up చేయాలి
• Market fall లో extra invest చేయండి
• Yearly once portfolio review అవసరం

⚠️ ఇది financial education purpose మాత్రమే
"""

    send_telegram(final_message)

# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    run_bot()
