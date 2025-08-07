import os
import telebot
from telebot import types
from flask import Flask, request

TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    raise ValueError("Переменная окружения TOKEN не установлена")

bot = telebot.TeleBot(TOKEN)

AUTHORIZED_IDS = [564415186, 1038649944]  # Добавь сюда свои ID

app = Flask(__name__)

def is_authorized(message):
    return message.from_user.id in AUTHORIZED_IDS

@bot.message_handler(commands=['start'])
def cmd_start(message):
    bot.reply_to(message, "Привет! Напиши 'помощь', чтобы увидеть список команд.")

@bot.message_handler(func=lambda message: message.text.lower() == "помощь")
def cmd_help(message):
    help_text = (
        "Доступные команды и фразы:\n"
        "/start\n"
        "помощь\n"
        "касса\n"
        "долги\n"
        "общаякасса\n"
        "категории\n"
        "+доход <сумма> <категория>\n"
        "-расход <сумма> <категория>\n"
        "+долг <сумма> <имя>\n"
        "-вернул <сумма> <имя>\n"
        "+мыдолжны <сумма> <имя>\n"
        "отчёт месяц"
    )
    bot.reply_to(message, help_text)

@bot.message_handler(func=lambda message: True)
def handle_all(message):
    if not is_authorized(message):
        bot.reply_to(message, "У вас нет доступа к этому боту.")
        return

    msg = message.text.lower()

    if msg == "касса":
        bot.reply_to(message, "Касса: 1,000,000 UZS")
    elif msg == "долги":
        bot.reply_to(message, "Долги:\n- Алишер должен 100,000\n- Мы должны: 200,000")
    elif msg == "общаякасса":
        bot.reply_to(message, "Общая касса (с учётом долгов): 1,300,000 UZS")
    elif msg == "категории":
        bot.reply_to(message, "Категории: бизнес, здоровье, зарплата, еда, развлечения")
    elif msg.startswith("+доход"):
        bot.reply_to(message, "Доход записан")
    elif msg.startswith("-расход"):
        bot.reply_to(message, "Расход записан")
    elif msg.startswith("+долг"):
        bot.reply_to(message, "Долг добавлен")
    elif msg.startswith("-вернул"):
        bot.reply_to(message, "Долг погашен")
    elif msg.startswith("+мыдолжны"):
        bot.reply_to(message, "Отметил, что мы должны")
    elif msg.startswith("отчёт"):
        bot.reply_to(message, "Отчёт за месяц отправлен")
    else:
        bot.reply_to(message, "Неизвестная команда. Напишите 'помощь' для списка команд.")

@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/', methods=['GET'])
def index():
    return "Бот работает!", 200

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=f"https://{os.environ['RAILWAY_STATIC_URL']}/{TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
