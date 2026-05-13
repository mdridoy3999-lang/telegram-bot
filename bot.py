from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import random

TOKEN = "8409479235:AAGBBODhZBQyKf76-zKevURrxHzYM4nINOA"

signals = [
    "📈 BUY BTCUSDT\nTP: 65000\nSL: 62000",
    "📉 SELL ETHUSDT\nTP: 2800\nSL: 3000",
    "📈 BUY GOLD\nTP: 2400\nSL: 2350"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Trading Signal Bot Online")

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    trade = random.choice(signals)
    await update.message.reply_text(trade)

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("signal", signal))

print("Bot Running...")
app.run_polling()
