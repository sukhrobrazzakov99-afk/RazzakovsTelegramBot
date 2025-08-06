import telebot
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Переменная окружения BOT_TOKEN не установлена")

bot = telebot.TeleBot(TOKEN)

# Авторизованные пользователи по user.id
AUTHORIZED_IDS = [564415186, 1038649944]

def is_authorized(message):
    return message.from_user.id in AUTHORIZED_IDS

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if not is_authorized(message):
        bot.reply_to(message, "У вас нет доступа к этому боту.")
        return

    msg = message.text.lower()

    if msg == "касса":
        bot.reply_to(message, "Касса: 1,000,000 UZS")
    elif msg == "долги":
        text = "Долги:\n- Алишер должен 100,000\n- Мы должны: 200,000"
        bot.reply_to(message, text)
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
        bot.reply_to(message, "Отметили, что мы должны")
    elif msg.startswith("отчёт"):
        bot.reply_to(message, "Отчёт за месяц отправлен")
    elif msg == "помощь":
        help_text = (
            "Доступные команды:\n"
            "+доход 1000 бизнес комментарий\n"
            "-расход 300 еда комментарий\n"
            "+долг 500 Алишер\n"
            "-вернул 500 Алишер\n"
            "+мыдолжны 200 Кредит\n"
            "касса\n"
            "общаякасса\n"
            "долги\n"
            "категории\n"
            "отчёт месяц"
        )
        bot.reply_to(message, help_text)
    else:
        bot.reply_to(message, "Неизвестная команда. Напишите 'помощь' для списка команд.")

bot.polling()
