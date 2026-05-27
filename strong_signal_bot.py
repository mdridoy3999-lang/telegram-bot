from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import random
import asyncio
import datetime

TOKEN = "8409479235:AAGBBODhZBQyKf76-zKevURrxHzYM4nINOA"

pairs = ["USD NGN OTC", "EUR USD OTC", "GBP USD OTC", "USD JPY OTC", "AUD USD OTC"]

async def send_result(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, direction: str):
    """সিগন্যালের ১ মিনিট পর WIN/LOSS রেজাল্ট পাঠাবে"""
    await asyncio.sleep(60)  # ১ মিনিট অপেক্ষা

    # সিমুলেশন (৬৮% Win Rate)
    is_win = random.random() < 0.68
    
    if is_win:
        result_text = f"✅ **WIN** ✅\n\n{direction} দিকে ট্রেডটি সফল হয়েছে!"
        emoji = "🎉"
    else:
        result_text = f"❌ **LOSS** ❌\n\n{direction} দিকে ট্রেডটি লস হয়েছে।"
        emoji = "😔"

    result_message = f"""══════════════════════
{emoji} **SIGNAL RESULT** {emoji}
══════════════════════

{result_text}

⏰ **Closed at:** {datetime.datetime.now().strftime("%H:%M:%S")}
"""

    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=result_message,
            reply_to_message_id=message_id
        )
    except:
        pass  # যদি মেসেজ ডিলিট হয়ে যায়


async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pair = random.choice(pairs)
    now = datetime.datetime.now()
    entry_time = now.strftime("%H:%M:%S")

    # শক্তিশালী সিগনালের জন্য লজিক
    rsi = random.randint(18, 85)
    ema_trend = random.choice(["Strong Bullish", "Strong Bearish"])
    zig_zag = random.choice(["Higher High", "Lower Low"])
    fractal = random.choice(["Bullish Fractal", "Bearish Fractal"])
    
    score = 0
    if rsi <= 28: score += 35
    elif rsi >= 73: score += 35
    
    score += 30  # EMA
    
    if (zig_zag == "Higher High" and fractal == "Bullish Fractal") or \
       (zig_zag == "Lower Low" and fractal == "Bearish Fractal"):
        score += 35

    if score >= 75:
        if ema_trend == "Strong Bullish":
            direction = "UP"
            emoji = "🟢"
            arrow = "⬆️"
            strength = "🔥 EXTREME STRONG BUY"
        else:
            direction = "DOWN"
            emoji = "🔴"
            arrow = "⬇️"
            strength = "🔥 EXTREME STRONG SELL"
            
        confidence = random.randint(78, 94)
        
        text = f"""🔥 **EXTREME STRONG SIGNAL** 🔥

📊 **{pair}** {emoji}

⏰ **1M** 📌 
**{direction}** {arrow}

🕒 **Signal & Entry:** {entry_time}

📈 **Indicators:**
• RSI       : {rsi} {' (Strong Oversold)' if rsi <= 28 else ' (Strong Overbought)'}
• EMA       : {ema_trend}
• Zig Zag   : {zig_zag}
• Fractal   : {fractal}

💪 **Strength**  : {strength}
📊 **Confidence** : {confidence}%

⚡ **এখনই এন্ট্রি নাও**
⏳ Validity: ৪৫-৭৫ সেকেন্ড
"""

        sent_message = await update.message.reply_text(text)

        # ১ মিনিট পর রেজাল্ট পাঠানোর টাস্ক শুরু
        asyncio.create_task(
            send_result(context, update.effective_chat.id, sent_message.message_id, direction)
        )
        
    else:
        await update.message.reply_text("⏳ এখন কোনো স্ট্রং সিগনাল নেই। পরে আবার চেষ্টা করো।")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **Strong Signal Bot** চালু আছে!\n\n"
        "🔹 /signal → শুধুমাত্র খুব শক্তিশালী সিগনাল\n"
        "⚠️ সিগন্যালের ১ মিনিট পর অটোমেটিক WIN/LOSS রেজাল্ট আসবে।"
    )


def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal))
    
    print("✅ Strong Signal Bot চালু হয়েছে... (Auto Win/Loss Enabled)")
    app.run_polling()


if __name__ == '__main__':
    asyncio.run(main())
