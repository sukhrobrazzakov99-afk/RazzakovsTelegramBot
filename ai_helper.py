import os, re
from typing import Dict, Optional

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '').strip()

INCOME_HINTS = ['зарплата','оклад','бонус','прем','продал','перевод','доход']
EXPENSE_HINTS = {
    'Еда': ['еда','продукт','обед','ужин','завтрак','мясо','кофе','чай','фастфуд','ханчапан'],
    'Транспорт': ['топлив','бензин','такси','транспорт','машин','метро','автобус','byd','парковк'],
    'Здоровье': ['аптек','лекар','врач','стомат','анализ'],
    'Аренда': ['аренда','квартира','дом','офис','съём','съем'],
    'Закупки': ['закуп','ремонт','мебел','техника','оборуд','инструмент','чехол','кейсы'],
    'Развлечения': ['кино','игр','cs2','донат','кафе','ресторан','караоке','подарок'],
}

def parse_free_text(text: str) -> Dict:
    """
    Пытаемся понять: тип (Доход/Расход), категория, сумма, валюта (UZS/USD)
    Пример: 'купил мясо 150000', 'продажа 100 usd', 'бонус 500k'
    """
    s = text.lower()
    # Валюта
    currency = 'UZS'
    if 'usd' in s or '$' in s:
        currency = 'USD'
    # Сумма
    import re
    m = re.search(r'(\d[\d\s,.]*)', s)
    amount = None
    if m:
        raw = m.group(1).replace(' ', '').replace(',', '').replace('.', '')
        try:
            amount = int(raw)
        except Exception:
            amount = None
    # Тип
    op_type = 'Расход'
    if any(k in s for k in INCOME_HINTS):
        op_type = 'Доход'
    # Категория
    category = 'Другое' if op_type=='Расход' else 'Другое (доход)'
    if op_type=='Расход':
        for cat, keys in EXPENSE_HINTS.items():
            if any(k in s for k in keys):
                category = cat
                break
    else:
        if any(k in s for k in ['зарплата','оклад']):
            category = 'Зарплата'
        elif any(k in s for k in ['бонус','прем']):
            category = 'Бонус'
        elif 'прод' in s:
            category = 'Продажа товаров'
        elif 'перевод' in s:
            category = 'Перевод'
    return {'type': op_type, 'category': category, 'amount': amount, 'currency': currency}

def ai_answer(question: str) -> Optional[str]:
    if not OPENAI_API_KEY:
        return None
    return 'AI-ответ: включится автоматически после установки OPENAI_API_KEY.'
