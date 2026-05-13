from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import random

TOKEN = "8409479235:AAGBBODhZBQyKf76-zKevURrxHzYM4nINOA"

pairs = ["EUR/USD", "USD/JPY", "GBP/USD", "BTC/USD"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Quotex Signal Bot Online")

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pair = random.choice(pairs)
    direction = random.choice(["📈 UP", "📉 DOWN"])
    time = random.choice(["1 MIN", "5 MIN"])

    msg = f"""
🔥 Quotex Signal

Pair: {pair}
Signal: {direction}
Time: {time}
"""
    await update.message.reply_text(msg)

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("signal", signal))

print("Bot Running...")
app.run_polling()
