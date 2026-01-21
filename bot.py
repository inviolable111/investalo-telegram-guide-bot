# investalo_bot.py
# Investalo Telegram Bot – Tagesguide mit Markteinschätzung, Mindset, Lernen & Reflexion

import os
import random
from datetime import datetime
from dotenv import load_dotenv
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes

# ------------------------------
# ENV
# ------------------------------
load_dotenv("daten.env")

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_IDS = [os.getenv("CHAT_ID_MAIN"), os.getenv("CHAT_ID_SECOND")]
INVESTALO_URL = "https://investalo.de"
TWELVEDATA_API_KEY = os.getenv("TWELVEDATA_API_KEY")

# ------------------------------
# CONFIG
# ------------------------------
MASCOT_IMAGE = "ohnehintergrund1.png"

# ------------------------------
# STATIC TEXTS
# ------------------------------
GUIDE_INTRO = (
    "👤 *Investalo Guide*\n"
    "Ruhige Einordnung. Klarer Tagesplan.\n"
    "Struktur vor Aktion."
)

TEXT_START = (
    "Willkommen bei *Investalo*.\n\n"
    "Eine Plattform für Marktverständnis,\n"
    "Denkweise & Orientierung – ohne Lärm.\n\n"
    "Wähle, was dich interessiert 👇"
)

TEXT_MARKT = (
    "📊 *Marktlogik*\n\n"
    "Märkte bewegen sich nicht wegen Meinungen,\n"
    "sondern wegen Struktur und Verhalten."
)

TEXT_MINDSET = (
    "🧠 *Denkweise*\n\n"
    "Nicht jede Bewegung verlangt Aktion.\n"
    "Klarheit entsteht durch Zurückhaltung."
)

TEXT_WAS = (
    "🔍 *Was ist Investalo?*\n\n"
    "Eine Finanzplattform für ruhige Marktbeobachtung,\n"
    "mentale Klarheit und saubere Entscheidungen."
)

QUOTES = [
    "Klarheit entsteht durch Beobachtung, nicht Aktion.",
    "Geduld ist die wichtigste Entscheidung des Tages.",
    "Nicht jeder Impuls muss verfolgt werden.",
    "Wissen kommt durch Beobachtung, nicht Eile.",
]

# ------------------------------
# THEMES & CHALLENGES
# ------------------------------
THEMES = {
    "Mindset": [
        "Geduld ist eine aktive Entscheidung.",
        "Disziplin zeigt sich im Nicht-Handeln.",
        "Abstand bringt Klarheit.",
        "Nicht jeder Impuls ist relevant."
    ],
    "Lernen": [
        "Beobachtung kommt vor Handlung.",
        "Struktur schlägt Intuition.",
        "Wiederholung schärft Wahrnehmung.",
        "Verstehen braucht Zeit."
    ],
    "Reflexion": [
        "Was hast du heute bewusst ausgelassen?",
        "Welche Emotion war präsent?",
        "Wo war Zurückhaltung sinnvoll?",
        "Was hast du über dich gelernt?"
    ]
}

CHALLENGES = {
    "Mindset": [
        "📝 Notiere eine Situation, in der du bewusst nichts getan hast.",
        "🧘‍♂️ Atme 3 Minuten ruhig und beobachte Gedanken.",
    ],
    "Lernen": [
        "👀 Beobachte den Markt 20 Minuten ohne Aktion.",
        "📚 Analysiere ein sauberes Marktverhalten.",
    ],
    "Reflexion": [
        "💭 Welche Emotion dominierte heute?",
        "🖋️ Notiere einen klaren Moment des Tages.",
    ]
}

last_sent = {theme: None for theme in THEMES.keys()}

# ------------------------------
# MARKET SYMBOLS (nur intern)
# ------------------------------
MARKET_SYMBOLS = {
    "DAX": "DAX",
    "S&P 500": "SPX",
    "Gold": "XAU/USD",
    "EUR/USD": "EUR/USD"
}

# ------------------------------
# MENU
# ------------------------------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Marktlogik", callback_data="markt")],
        [InlineKeyboardButton("🧠 Denkweise", callback_data="mindset")],
        [InlineKeyboardButton("🔍 Was ist Investalo?", callback_data="was")],
        [InlineKeyboardButton("🌐 Website", url=INVESTALO_URL)],
    ])

# ------------------------------
# AUTO WELCOME
# ------------------------------
async def auto_welcome(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in CHAT_IDS:
        if not chat_id:
            continue
        try:
            with open(MASCOT_IMAGE, "rb") as img:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=img,
                    caption=GUIDE_INTRO,
                    parse_mode="Markdown"
                )
        except:
            pass

        await context.bot.send_message(
            chat_id=chat_id,
            text=TEXT_START,
            reply_markup=main_menu(),
            parse_mode="Markdown"
        )

# ------------------------------
# MARKET CONTEXT (neutral)
# ------------------------------
def get_market_context():
    states = []

    for symbol in MARKET_SYMBOLS.values():
        try:
            r = requests.get(
                f"https://api.twelvedata.com/quote?symbol={symbol}&apikey={TWELVEDATA_API_KEY}",
                timeout=5
            ).json()

            if "code" in r:
                continue

            high = float(r.get("high", 0))
            low = float(r.get("low", 0))
            open_ = float(r.get("open", 0))
            if open_ == 0:
                continue

            range_pct = abs(high - low) / open_

            if range_pct > 0.015:
                states.append("unruhig")
            elif range_pct > 0.007:
                states.append("aktiv")
            else:
                states.append("ruhig")

        except:
            continue

    calm_texts = [
        "Die Märkte wirken ruhig und strukturiert. Ein Umfeld für saubere Vorbereitung.",
        "Aktuell zeigt sich wenig Marktdruck. Beobachtung ist wertvoller als Aktion.",
        "Das Umfeld ist ruhig. Fokus auf Struktur statt Bewegung."
    ]

    if states.count("unruhig") >= 2:
        return "Die Märkte wirken angespannt. Bewegungen entstehen eher aus Dynamik als aus Klarheit."
    elif states.count("aktiv") >= 2:
        return "Das Marktumfeld zeigt Bewegung, aber ohne klare Dominanz. Geduld ist sinnvoll."
    else:
        return random.choice(calm_texts)

# ------------------------------
# HELPER: Tagesphase
# ------------------------------
def get_day_phase():
    hour = datetime.now().hour
    if 6 <= hour < 9:
        return "Morgen"
    elif 9 <= hour < 12:
        return "Vormittag"
    elif 12 <= hour < 15:
        return "Mittag"
    elif 15 <= hour < 18:
        return "Nachmittag"
    elif 18 <= hour < 21:
        return "Abend"
    else:
        return "Nacht"

def get_day_phase_emoji(phase):
    mapping = {
        "Morgen": "☀️",
        "Vormittag": "🌤️",
        "Mittag": "☀️",
        "Nachmittag": "🌤️",
        "Abend": "🌙",
        "Nacht": "🧭"
    }
    return mapping.get(phase, "")

# ------------------------------
# AUTO PUSH (alle 2 Stunden)
# ------------------------------
async def auto_push(context: ContextTypes.DEFAULT_TYPE):
    theme_name = random.choice(list(THEMES.keys()))
    options = [c for c in THEMES[theme_name] if c != last_sent[theme_name]]
    content = random.choice(options if options else THEMES[theme_name])
    last_sent[theme_name] = content

    challenge = random.choice(CHALLENGES.get(theme_name, []))
    quote = random.choice(QUOTES)

    phase = get_day_phase()
    zeit = f"{get_day_phase_emoji(phase)} {phase}"

    # Markttext immer anhängen
    market_text = "\n\n📊 *Marktumfeld*\n" + get_market_context()

    msg = (
        f"👤 *Investalo Guide*\n\n"
        f"{zeit}\n"
        f"📌 *Thema*: {theme_name}\n\n"
        f"{content}"
        f"{market_text}\n\n"
        f"{challenge}\n"
        f"💡 {quote}\n\n"
        f"Mehr auf: [investalo.de]({INVESTALO_URL})"
    )

    for chat_id in CHAT_IDS:
        if chat_id:
            await context.bot.send_message(
                chat_id=chat_id,
                parse_mode="Markdown",
                text=msg
            )
            # Menü zwischendurch anzeigen (30 % Chance)
            if random.random() < 0.3:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="Was möchtest du als Nächstes tun?",
                    reply_markup=main_menu(),
                    parse_mode="Markdown"
                )

# ------------------------------
# BUTTON HANDLER
# ------------------------------
async def button_handler(update, context):
    q = update.callback_query
    await q.answer()

    if q.data == "markt":
        await q.edit_message_text(TEXT_MARKT, reply_markup=main_menu(), parse_mode="Markdown")
    elif q.data == "mindset":
        await q.edit_message_text(TEXT_MINDSET, reply_markup=main_menu(), parse_mode="Markdown")
    elif q.data == "was":
        await q.edit_message_text(TEXT_WAS, reply_markup=main_menu(), parse_mode="Markdown")

# ------------------------------
# MAIN
# ------------------------------
def main():
    if not BOT_TOKEN or not TWELVEDATA_API_KEY:
        raise ValueError("🚨 Environment-Variable fehlt! Bot beendet.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CallbackQueryHandler(button_handler))

    # Auto-Welcome beim Start
    app.job_queue.run_once(auto_welcome, when=5)

    # Automatischer Push alle 2 Stunden
    app.job_queue.run_repeating(auto_push, interval=7200, first=10)

    print("🤖 Investalo Bot läuft stabil …")
    app.run_polling()

if __name__ == "__main__":
    main()
