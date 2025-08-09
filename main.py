# -*- coding: utf-8 -*-
import os
import logging
import datetime
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from db import init_db, add_op, get_balance, get_history
from ai_helper import parse_free_text, ai_answer

# ---- ТВОИ НАСТРОЙКИ ----
TOKEN = "7611168200:AAFkdTWAz1xMawJOKF0Mu21ViFA5Oz8wblk"
AUTHORIZED_IDS = [564415186, 1038649944]  # ты и брат
PUBLIC_URL = "https://razzakovstelegrambot.up.railway.app"
# -------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INCOME_CATEGORIES = ["Зарплата", "Бонус", "Продажа товаров", "Перевод", "Другое (доход)"]
EXPENSE_CATEGORIES = ["Еда", "Транспорт", "Здоровье", "Аренда", "Закупки", "Развлечения", "Другое"]


def check_access(user_id: int) -> bool:
    return user_id in AUTHORIZED_IDS


def main_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("➕ Доход", callback_data="add_income"),
         InlineKeyboardButton("➖ Расход", callback_data="add_expense")],
        [InlineKeyboardButton("📊 Баланс", callback_data="show_balance"),
         InlineKeyboardButton("📜 История", callback_data="show_history")],
        [InlineKeyboardButton("📤 Экспорт в Excel", callback_data="export_excel"),
         InlineKeyboardButton("🤖 AI помощник", callback_data="ai_help")],
    ]
    return InlineKeyboardMarkup(keyboard)


# --------- Хэндлеры ---------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_access(update.effective_user.id):
        await update.message.reply_text("⛔ У вас нет доступа.")
        return
    await update.message.reply_text("💰 Бот запущен. Выберите действие:", reply_markup=main_menu())


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    if not check_access(uid):
        await q.edit_message_text("⛔ У вас нет доступа.")
        return

    data = q.data
    if data == "add_income":
        context.user_data["type"] = "Доход"
        await q.edit_message_text("💵 Введите сумму и описание (или просто сумму):")
    elif data == "add_expense":
        context.user_data["type"] = "Расход"
        await q.edit_message_text("💸 Введите сумму и описание:")
    elif data == "show_balance":
        b = get_balance(q.message.chat.id)
        await q.edit_message_text(
            f"💰 Баланс:\nUSD: {b['USD']}\nUZS: {b['UZS']}",
            reply_markup=main_menu()
        )
    elif data == "show_history":
        hist = get_history(q.message.chat.id, 10)
        if not hist:
            await q.edit_message_text("История пуста.", reply_markup=main_menu())
            return
        text = "📜 Последние операции:\n" + "\n".join(
            f"{ts} — {uname}: {t} {amt} {cur} ({cat})" for t, cat, cur, amt, ts, uname in hist
        )
        await q.edit_message_text(text, reply_markup=main_menu())
    elif data == "export_excel":
        hist = get_history(q.message.chat.id, 1000)
        df = pd.DataFrame(hist, columns=["Тип", "Категория", "Валюта", "Сумма", "Дата", "Пользователь"])
        path = "export.xlsx"
        df.to_excel(path, index=False)
        await q.message.reply_document(open(path, "rb"))
    elif data == "ai_help":
        await q.edit_message_text("🤖 Введите вопрос для AI (или пришлите запись вида: 'еда 150000 usd').")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    if not check_access(uid):
        return

    text = (update.message.text or "").strip()

    # Режим AI
    if context.user_data.get("await_ai"):
        context.user_data["await_ai"] = False
        ans = ai_answer(text) or "⚠ AI не активирован (нет OPENAI_API_KEY)."
        await update.message.reply_text(ans, reply_markup=main_menu())
        return

    # Ввод операции (после нажатия Доход/Расход)
    if "type" in context.user_data:
        p = parse_free_text(text)
        op_type = context.user_data["type"]
        # Категория: для расхода проверяем, что она из списка расходов
        category = (
            p["category"] if op_type == "Доход"
            else (p["category"] if p["category"] in EXPENSE_CATEGORIES else "Другое")
        )
        amount = p["amount"]
        currency = p["currency"]
        if not amount:
            await update.message.reply_text("Не понял сумму. Пример: 'Еда 150000' или 'продажа 100 usd'")
            return
        add_op(
            chat_id,
            uid,
            update.effective_user.first_name or str(uid),
            op_type,
            category,
            currency,
            int(amount),
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        )
        await update.message.reply_text(
            f"✅ {op_type}: {amount} {currency} ({category}) — сохранено.",
            reply_markup=main_menu(),
        )
        del context.user_data["type"]
        return

    # Вопрос → включаем AI
    if text.endswith("?"):
        context.user_data["await_ai"] = True
        await update.message.reply_text("🤖 Вопрос принят. Жду ответ от AI...")
        return

    # Иначе — просто показать меню
    await update.message.reply_text("Выберите действие:", reply_markup=main_menu())


# --------- Запуск (Webhook) ---------
def main():
    init_db()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # ВАЖНО: для твоей версии библиотеки параметр называется url_path
    path = f"/webhook/{TOKEN}"
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        url_path=path,                              # <— ключевая правка
        webhook_url=f"{PUBLIC_URL}{path}",          # Telegram будет бить сюда
    )


if __name__ == "__main__":
    main()

