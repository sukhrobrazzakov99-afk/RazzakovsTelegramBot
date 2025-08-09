import os, logging, sys
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters
from db import init_db, add_op, get_balance, get_history
from ai_helper import parse_free_text, ai_answer

load_dotenv()

logging.basicConfig(stream=sys.stdout, level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN','').strip()
AUTHORIZED = [int(x) for x in os.getenv('AUTHORIZED_USER_IDS','').replace(' ','').split(',') if x]
PORT = int(os.getenv('PORT','8000'))
PUBLIC_URL = os.getenv('RAILWAY_STATIC_URL','').rstrip('/')

USER_NAMES = {AUTHORIZED[i]: n for i,n in enumerate(['Сухроб','Брат'][:len(AUTHORIZED)])}

MAIN_KB = ReplyKeyboardMarkup([
    [KeyboardButton('➖ Добавить расход'), KeyboardButton('💰 Добавить доход')],
    [KeyboardButton('💼 Баланс'), KeyboardButton('📚 История')],
    [KeyboardButton('🤖 AI помощник'), KeyboardButton('📤 Экспорт')],
], resize_keyboard=True)

EXPENSE_CATS = ['🍔 Еда','🚕 Транспорт','💊 Здоровье','🏠 Аренда','🛠 Закупки','🎉 Развлечения','➖ Другое']
INCOME_CATS  = ['💼 Зарплата','🎁 Бонус','🏪 Продажа товаров','💳 Перевод','➕ Другое (доход)']
def cats_kb(cats): 
    rows=[cats[i:i+2] for i in range(0,len(cats),2)]
    rows.append(['🔙 Назад'])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

CURRENCIES_KB = ReplyKeyboardMarkup([[KeyboardButton('💵 USD'), KeyboardButton('🇺🇿 UZS')], ['🔙 Назад']], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user and update.effective_user.id not in AUTHORIZED:
        return
    await update.message.reply_text('Добро пожаловать! Выберите действие:', reply_markup=MAIN_KB)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user and update.effective_user.id not in AUTHORIZED:
        return
    await update.message.reply_text('Кнопки снизу: добавляйте доходы/расходы, смотрите баланс и историю.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.id not in AUTHORIZED:
        return
    chat_id = update.effective_chat.id
    text = (update.message.text or '').strip()

    if text in ('🔙 Назад','/start','Меню'):
        context.user_data.clear()
        await update.message.reply_text('Меню:', reply_markup=MAIN_KB)
        return

    if text == '➖ Добавить расход':
        context.user_data['mode'] = 'Расход'
        await update.message.reply_text('Выберите категорию расхода:', reply_markup=cats_kb(EXPENSE_CATS))
        return
    if text == '💰 Добавить доход':
        context.user_data['mode'] = 'Доход'
        await update.message.reply_text('Выберите категорию дохода:', reply_markup=cats_kb(INCOME_CATS))
        return

    if context.user_data.get('mode') in ('Расход','Доход') and text in EXPENSE_CATS + INCOME_CATS:
        context.user_data['category'] = text.replace(' (доход)','')
        await update.message.reply_text('В какой валюте?', reply_markup=CURRENCIES_KB)
        return

    if text in ('💵 USD','🇺🇿 UZS'):
        context.user_data['currency'] = 'USD' if 'USD' in text else 'UZS'
        await update.message.reply_text('Введите сумму (целое число):', reply_markup=ReplyKeyboardMarkup([['🔙 Назад']],resize_keyboard=True))
        return

    if context.user_data.get('currency') and text.isdigit():
        amount = int(text)
        op_type = context.user_data.get('mode')
        category = context.user_data.get('category')
        currency = context.user_data.get('currency')
        ts = datetime.now().strftime('%Y-%m-%d %H:%M')
        add_op(chat_id, user.id, USER_NAMES.get(user.id, str(user.id)), op_type, category, currency, amount, ts)
        context.user_data.clear()
        sign = '+' if op_type=='Доход' else '-'
        emoji = '🟢' if op_type=='Доход' else '🔴'
        await update.message.reply_text(f"{emoji} {op_type}: {category} {sign}{amount} {currency} — {ts} ({USER_NAMES.get(user.id,'')})",
                                        reply_markup=MAIN_KB)
        return

    if text == '💼 Баланс':
        b = get_balance(chat_id)
        await update.message.reply_text(f"💼 Общая касса:\nUSD: {b.get('USD',0)}\nUZS: {b.get('UZS',0)}", reply_markup=MAIN_KB)
        return

    if text == '📚 История':
        hist = get_history(chat_id, 10)
        if not hist:
            await update.message.reply_text('История пуста.', reply_markup=MAIN_KB); return
        lines = []
        for t,cat,cur,amt,ts,u in hist:
            sign = '+' if t=='Доход' else '-'
            emoji = '🟢' if t=='Доход' else '🔴'
            lines.append(f"{emoji} {t}: {cat} {sign}{amt} {cur} — {ts} ({u.lower()})")
        await update.message.reply_text('\n'.join(lines), reply_markup=MAIN_KB)
        return

    if text == '📤 Экспорт':
        await update.message.reply_text('Экспорт в Excel добавлю после деплоя (файл .xlsx за период).', reply_markup=MAIN_KB)
        return

    if text == '🤖 AI помощник':
        await update.message.reply_text("Напишите: 'еда 150000' или спросите: 'сколько потратили на еду в июле?' — попробую распознать.")
        context.user_data['ai_mode']=True
        return
    if context.user_data.get('ai_mode'):
        p = parse_free_text(text)
        if p['amount'] is not None:
            ts = datetime.now().strftime('%Y-%m-%d %H:%M')
            add_op(chat_id, user.id, USER_NAMES.get(user.id, str(user.id)), p['type'], p['category'], p['currency'], int(p['amount']), ts)
            sign = '+' if p['type']=='Доход' else '-'
            emoji = '🟢' if p['type']=='Доход' else '🔴'
            await update.message.reply_text(f"{emoji} {p['type']}: {p['category']} {sign}{p['amount']} {p['currency']} — {ts} ({USER_NAMES.get(user.id,'')})")
        else:
            ans = ai_answer(text) or 'Не понял сумму. Пример: "Еда 150000" или "продажа 100 usd".'
            await update.message.reply_text(ans)
        context.user_data.pop('ai_mode', None)
        return

    await update.message.reply_text('Выберите действие:', reply_markup=MAIN_KB)

async def on_startup(app: Application):
    init_db()
    if PUBLIC_URL and TOKEN:
        url = f"{PUBLIC_URL}/webhook/{TOKEN}"
        await app.bot.set_webhook(url)
        logging.info(f"Webhook set to: {url}")

def main():
    if not TOKEN:
        logging.error('Нет TELEGRAM_BOT_TOKEN'); return
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_cmd))
    app.add_handler(CommandHandler('export', help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.post_init = on_startup
    app.run_webhook(listen='0.0.0.0', port=int(os.getenv('PORT','8000')), secret_token=None)

if __name__ == '__main__':
    main()
