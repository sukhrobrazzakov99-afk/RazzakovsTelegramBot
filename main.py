import os
import telebot
from telebot import types
from flask import Flask, request

TOKEN = os.environ.get("TOKEN")
bot = telebot.TeleBot(TOKEN)

AUTHORIZED_USERS = [564415186, 1038649944]

# Простой пример ответа бота
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if message.from_user.id in AUTHORIZED_USERS:
        bot.reply_to(message, "Привет, команда получена!")
    else:
        bot.reply_to(message, "Извините, у вас нет доступа к этому боту.")

# Flask-приложение
app = Flask(__name__)

@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def index():
    return "Бот работает!", 200

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=f"https://{os.environ['RAILWAY_STATIC_URL']}/{TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))


