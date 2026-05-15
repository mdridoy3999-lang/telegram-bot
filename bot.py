from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

import random

TOKEN = "8409479235:AAGBBODhZBQyKf76-zKevURrxHzYM4nINOA"

pairs = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "USD/CAD",
    "AUD/USD",
    "NZD/USD",
    "EUR/JPY",
    "GBP/JPY",
    "EUR/USD OTC",
    "GBP/USD OTC",
    "USD/JPY OTC",
    "AUD/USD OTC",
]

directions = [
    "⬆️ UP",
    "⬇️ DOWN"
]

# START COMMAND
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Trading Signal Bot Online 🔥"
    )

# SIGNAL COMMAND
async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):

    pair = random.choice(pairs)
    direction = random.choice(directions)

    msg = f"""
🔥 SIGNAL

{pair} 1M
{direction}
"""

    await update.message.reply_text(msg)

# MAIN BOT
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("signal", signal))

print("Bot Running...")

app.run_polling()
