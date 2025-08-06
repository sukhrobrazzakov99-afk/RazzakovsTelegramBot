
import os
import telebot
from datetime import datetime
from collections import defaultdict

# Получение токена из переменных среды
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Списки доступа
AUTHORIZED_USERS = ["SukhrobAbdurazzakov", "revivemd"]

# Хранилище
cash_balance = 0
debts = []
we_owe = []
incomes = []
expenses = []
categories = defaultdict(lambda: {"income": 0, "expense": 0})

# Авторизация
def is_authorized(message):
    return message.from_user.username in AUTHORIZED_USERS

# Команды
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if is_authorized(message):
        bot.reply_to(message, f"👋 Привет, @{message.from_user.username}! Razzakov’s Bot готов к работе.")
    else:
        bot.reply_to(message, "⛔ У вас нет доступа к этому боту.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    global cash_balance

    if not is_authorized(message):
        return

    msg = message.text.strip()

    try:
        if msg.startswith("+доход"):
            parts = msg.split()
            amount = int(parts[1])
            category = parts[2].lower()
            comment = " ".join(parts[3:])
            incomes.append((datetime.now(), amount, category, comment))
            cash_balance += amount
            categories[category]["income"] += amount
            bot.reply_to(message, f"✅ Доход добавлен: {amount}$ ({category}) – {comment}")

        elif msg.startswith("-расход"):
            parts = msg.split()
            amount = int(parts[1])
            category = parts[2].lower()
            comment = " ".join(parts[3:])
            expenses.append((datetime.now(), amount, category, comment))
            cash_balance -= amount
            categories[category]["expense"] += amount
            bot.reply_to(message, f"💸 Расход добавлен: {amount}$ ({category}) – {comment}")

        elif msg.startswith("+долг"):
            parts = msg.split()
            amount = int(parts[1])
            name = parts[2]
            debts.append((datetime.now(), amount, name))
            bot.reply_to(message, f"🧾 Добавлен долг: {name} должен {amount}$")

        elif msg.startswith("-вернул"):
            parts = msg.split()
            amount = int(parts[1])
            name = parts[2]
            debts[:] = [d for d in debts if d[2] != name]
            cash_balance += amount
            bot.reply_to(message, f"✅ {name} вернул {amount}$")

        elif msg.startswith("+мыдолжны"):
            parts = msg.split()
            amount = int(parts[1])
            name = parts[2]
            we_owe.append((datetime.now(), amount, name))
            bot.reply_to(message, f"📌 Вы должны {name}: {amount}$")

        elif msg == "касса":
            bot.reply_to(message, f"💰 Текущий баланс: {cash_balance}$")

        elif msg == "общаякасса":
            total_debts = sum(d[1] for d in debts)
            total_we_owe = sum(w[1] for w in we_owe)
            total = cash_balance + total_debts - total_we_owe
            bot.reply_to(message, f"💼 Общая касса (если все вернут): {total}$")

        elif msg == "долги":
            text = "📊 Долги:
"
            for d in debts:
                text += f"- {d[2]} должен {d[1]}$
"
            text += "
📌 Мы должны:
"
            for w in we_owe:
                text += f"- {w[2]}: {w[1]}$
"
            bot.reply_to(message, text)

        elif msg == "категории":
            text = "📂 Категории:
"
            for cat, val in categories.items():
                text += f"- {cat.title()}: доход {val['income']}$ / расход {val['expense']}$
"
            bot.reply_to(message, text)

        elif msg == "отчёт месяц":
            text = "📅 Отчёт за месяц:
"
            total_income = sum(x[1] for x in incomes)
            total_expense = sum(x[1] for x in expenses)
            net = total_income - total_expense
            text += f"Доходов: {total_income}$
Расходов: {total_expense}$
Чистый итог: {net}$
"
            bot.reply_to(message, text)

    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

# Запуск
bot.polling()
