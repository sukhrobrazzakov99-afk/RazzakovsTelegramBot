from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from datetime import datetime
import os

TOKEN = "7611168200:AAFkdTWAz1xMawJOKF0Mu21ViFA5Oz8wblk"
AUTHORIZED_USERS = [564415186, 1038649944]

keyboard = [
    ["➕ Доход", "➖ Расход"],
    ["📊 Баланс", "💰 История"],
    ["🔄 Отмена", "🧨 Сброс"]
]

category_keyboard = [
    ["💼 Зарплата", "🎁 Бонус"],
    ["🍔 Еда", "🚕 Транспорт"],
    ["💊 Здоровье", "🏠 Аренда"],
    ["🔙 Назад"]
]

user_data = {}

def is_authorized(user_id):
    return user_id in AUTHORIZED_USERS

def format_history_entry(entry):
    return f"{entry['emoji']} {entry['type']}: {entry['category']} {entry['sign']}{entry['amount']} сум — {entry['date']}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("⛔️ У вас нет доступа к этому боту.")
        return
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👋 Привет! Я финансовый бот Razzakovs. Выберите действие:", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if not is_authorized(user_id):
        await update.message.reply_text("⛔️ У вас нет доступа.")
        return

    if user_id not in user_data:
        user_data[user_id] = {"balance": 0, "history": [], "temp": {}}

    data = user_data[user_id]

    if text == "➕ Доход":
        context.user_data["action"] = "income"
        reply_markup = ReplyKeyboardMarkup(category_keyboard, resize_keyboard=True)
        await update.message.reply_text("Выберите категорию дохода:", reply_markup=reply_markup)

    elif text == "➖ Расход":
        context.user_data["action"] = "expense"
        reply_markup = ReplyKeyboardMarkup(category_keyboard, resize_keyboard=True)
        await update.message.reply_text("Выберите категорию расхода:", reply_markup=reply_markup)

    elif text in sum(category_keyboard, []):
        if text == "🔙 Назад":
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("Главное меню", reply_markup=reply_markup)
            return
        context.user_data["category"] = text
        await update.message.reply_text("Введите сумму:")

    elif text.replace(" ", "").isdigit():
        action = context.user_data.get("action")
        category = context.user_data.get("category")
        amount = int(text.replace(" ", ""))
        now = datetime.now().strftime("%d.%m.%Y %H:%M")

        if not action or not category:
            await update.message.reply_text("Сначала выберите ➕ Доход или ➖ Расход и категорию.")
            return

        sign = "+" if action == "income" else "-"
        emoji = "🟢" if action == "income" else "🔴"
        entry = {
            "type": "Доход" if action == "income" else "Расход",
            "category": category,
            "amount": amount,
            "sign": sign,
            "emoji": emoji,
            "date": now
        }

        if action == "income":
            data["balance"] += amount
        else:
            data["balance"] -= amount

        data["history"].append(entry)
        data["temp"]["last"] = entry

        await update.message.reply_text(f"{emoji} {entry['type']} {category} {sign}{amount} сохранён!")

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Что дальше?", reply_markup=reply_markup)

    elif text == "📊 Баланс":
        await update.message.reply_text(f"💼 Ваш текущий баланс: {data['balance']} сум")

    elif text == "💰 История":
        if not data["history"]:
            await update.message.reply_text("История пуста.")
        else:
            msg = "
".join([format_history_entry(e) for e in data["history"][-10:]])
            await update.message.reply_text(f"Последние записи:
{msg}")

    elif text == "🧨 Сброс":
        data["balance"] = 0
        data["history"] = []
        await update.message.reply_text("Все данные сброшены!")

    elif text == "🔄 Отмена":
        last = data.get("temp", {}).get("last")
        if last:
            if last["type"] == "Доход":
                data["balance"] -= last["amount"]
            else:
                data["balance"] += last["amount"]
            data["history"].remove(last)
            data["temp"]["last"] = None
            await update.message.reply_text("⛔️ Последняя операция отменена.")
        else:
            await update.message.reply_text("Нет операций для отмены.")

    else:
        await update.message.reply_text("Пожалуйста, выберите действие на клавиатуре.")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
