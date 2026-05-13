from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import random

TOKEN = "8409479235:AAGBBODhZBQyKf76-zKevURrxHzYM4nINOA"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Quotex Signal Bot Online")

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):

    pair = random.choice([
        "EUR/USD",
        "GBP/USD",
        "USD/JPY",
        "BTC/USD"
    ])

    direction = random.choice([
        "📈 UP",
        "📉 DOWN"
    ])

    message = f"""
🔥 SIGNAL READY

💱 Pair: {pair}
🚀 Signal: {direction}
⏰ Time: 1 MIN
"""

    await update.message.reply_text(message)

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("signal", signal))

print("Bot Running...")
app.run_polling()
