from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import random

TOKEN = "8409479235:AAGBBODhZBQyKf76-zKevURrxHzYM4nINOA"

pairs = [
    "BTC/USD",
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "USD/BDT",
    "USD/BRL"
    
]

directions = [
    "📈 UP",
    "📉 DOWN"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Signal Bot Online")

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):

    pair = random.choice(pairs)
    direction = random.choice(directions)

    msg = f"""
🔥 SIGNAL

{pair} 1M
{direction}
"""

    await update.message.reply_text(msg)

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("signal", signal))

print("Bot Running...")
app.run_polling()
