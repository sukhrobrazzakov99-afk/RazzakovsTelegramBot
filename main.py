from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import os
from aiohttp import web

TOKEN = "7611168200:AAFkdTWAz1xMawJOKF0Mu21ViFA5Oz8wblk"
AUTHORIZED_USERS = [564415186, 1038649944]

keyboard = [
    ["➕ Доход", "➖ Расход"],
    ["📊 Баланс", "💰 История"]
]

user_data = {}

def is_authorized(user_id):
    return user_id in AUTHORIZED_USERS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("⛔️ У вас нет доступа к этому боту.")
        return
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👋 Привет! Я финансовый бот Razzakovs. Выберите действие:", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("⛔️ У вас нет доступа.")
        return

    text = update.message.text
    if text == "➕ Доход":
        await update.message.reply_text("Введите сумму дохода:")
        context.user_data["action"] = "income"
    elif text == "➖ Расход":
        await update.message.reply_text("Введите сумму расхода:")
        context.user_data["action"] = "expense"
    elif text == "📊 Баланс":
        balance = user_data.get(user_id, {}).get("balance", 0)
        await update.message.reply_text(f"💼 Ваш текущий баланс: {balance} сум")
    elif text == "💰 История":
        history = user_data.get(user_id, {}).get("history", [])
        if not history:
            await update.message.reply_text("История пуста.")
        else:
            msg = "\n".join(history[-10:])
            await update.message.reply_text(f"Последние записи:\n{msg}")
    elif text.replace(" ", "").isdigit():
        action = context.user_data.get("action")
        amount = int(text.replace(" ", ""))
        if user_id not in user_data:
            user_data[user_id] = {"balance": 0, "history": []}

        if action == "income":
            user_data[user_id]["balance"] += amount
            user_data[user_id]["history"].append(f"🟢 Доход: +{amount}")
            await update.message.reply_text(f"Доход +{amount} сохранён!")
        elif action == "expense":
            user_data[user_id]["balance"] -= amount
            user_data[user_id]["history"].append(f"🔴 Расход: -{amount}")
            await update.message.reply_text(f"Расход -{amount} сохранён!")
        else:
            await update.message.reply_text("Сначала выберите ➕ Доход или ➖ Расход.")
    else:
        await update.message.reply_text("Пожалуйста, выберите действие на клавиатуре.")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

async def on_startup(app_: web.Application):
    webhook_url = os.environ.get("RAILWAY_STATIC_URL") + f"/webhook/{TOKEN}"
    await app.bot.set_webhook(url=webhook_url)

app.run_webhook(
    listen="0.0.0.0",
    port=int(os.environ.get("PORT", 8000)),
    path=f"/webhook/{TOKEN}",
    on_startup=on_startup
)
