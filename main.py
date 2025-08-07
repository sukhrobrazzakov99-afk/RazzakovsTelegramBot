import os
import telebot
from flask import Flask, request

# Твой токен — уже вставлен
TOKEN = "7611168200:AAFkdTWAz1xMawJOKF0Mu21ViFA5Oz8wblk"
bot = telebot.TeleBot(TOKEN)

AUTHORIZED_IDS = [564415186, 1038649944]

app = Flask(__name__)

def is_authorized(message):
    return message.from_user.id in AUTHORIZED_IDS

@bot.message_handler(commands=['start'])
def cmd_start(message):
    bot.reply_to(message, "Ассаламу алейкум! Я готов к работе. Напиши 'помощь'.")

@bot.message_handler(func=lambda message: message.text and message.text.lower() == "помощь")
def cmd_help(message):
    bot.reply_to(message,
        "📋 Команды:\n"
        "• касса\n"
        "• долги\n"
        "• общаякасса\n"
        "• категории\n"
        "• +доход <сумма> <категория>\n"
        "• -расход <сумма> <категория>\n"
        "• +долг <сумма> <имя>\n"
        "• -вернул <сумма> <имя>\n"
        "• +мыдолжны <сумма> <имя>\n"
        "• отчёт месяц\n"
    )

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if not is_authorized(message):
        bot.reply_to(message, "⛔ У вас нет доступа.")
        return

    text = message.text.lower()

    if text == "касса":
        bot.reply_to(message, "💰 Касса: 1,000,000 UZS")
    elif text == "долги":
        bot.reply_to(message, "📉 Долги:\n• Алишер: 100k\n• Мы должны: 200k")
    elif text == "общаякасса":
        bot.reply_to(message, "💼 Общая касса: 1,300,000 UZS")
    elif text == "категории":
        bot.reply_to(message, "📊 Категории: бизнес, здоровье, зарплата, еда, развлечения")
    elif text.startswith("+доход"):
        bot.reply_to(message, "✅ Доход записан.")
    elif text.startswith("-расход"):
        bot.reply_to(message, "📤 Расход записан.")
    elif text.startswith("+долг"):
        bot.reply_to(message, "📝 Долг добавлен.")
    elif text.startswith("-вернул"):
        bot.reply_to(message, "💸 Долг погашен.")
    elif text.startswith("+мыдолжны"):
        bot.reply_to(message, "🧾 Мы записали, что должны.")
    elif text.startswith("отчёт"):
        bot.reply_to(message, "📈 Отчёт за месяц готов.")
    else:
        bot.reply_to(message, "❓ Неизвестная команда. Напиши 'помощь'.")

@app.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "🤖 Бот запущен и работает."

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"https://{os.environ['RAILWAY_STATIC_URL']}/{TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
