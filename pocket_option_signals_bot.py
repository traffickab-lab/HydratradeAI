# pocket_option_signals_bot.py
# Pocket Option Signals Telegram Bot (ready-to-run)
# Token, REF_LINK, BONUS_TEXT and ADMIN_ID are already filled in.
import os
import json
import logging
import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------- Настройки (берутся из env или берутся значения по умолчанию) ---------------------
TOKEN = os.getenv("TOKEN", "8265669590:AAGgSYBz3FAIW7ghrr37k_UXPihl_UpJ8C8")
REF_LINK = os.getenv("REF_LINK", "https://po-ru4.click/register?utm_campaign=824830&utm_source=affiliate&utm_medium=sr&a=vn8O5uQ2KKyJGY&ac=botvtelegram&code=50START")
BONUS_TEXT = os.getenv("BONUS_TEXT", "50START (бонус 50%; минимальный депозит $50)")

ADMIN_ID_ENV = os.getenv("ADMIN_ID")
if ADMIN_ID_ENV:
    try:
        ADMIN_ID = int(ADMIN_ID_ENV)
    except Exception:
        ADMIN_ID = None
else:
    ADMIN_ID = 8199618278  # подставлен твой ID

DB_FILE = os.getenv("DB_FILE", "db.json")

# --------------------- Список доступных пар и таймфреймов ---------------------
PAIRS = {
    "EUR/USD": "eur-usd",
    "GBP/USD": "gbp-usd",
    "USD/JPY": "usd-jpy",
    "AUD/USD": "aud-usd",
    "USD/CAD": "usd-cad"
}

TIMEFRAMES = {
    "1 мин": "1m",
    "5 мин": "5m",
    "15 мин": "15m",
    "1 час": "1h",
    "4 часа": "4h",
    "1 день": "1D"
}

# --------------------- Инициализация бота ---------------------
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# --------------------- DB helpers ---------------------
def load_db():
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"pending": {}, "approved": {}}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

db = load_db()

# --------------------- Keyboards ---------------------
def pairs_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(text=name, callback_data=f"pair|{slug}") for name, slug in PAIRS.items()]
    kb.add(*buttons)
    return kb

def timeframes_keyboard(pair_slug):
    kb = InlineKeyboardMarkup(row_width=3)
    buttons = [InlineKeyboardButton(text=name, callback_data=f"tf|{pair_slug}|{code}") for name, code in TIMEFRAMES.items()]
    kb.add(*buttons)
    return kb

# --------------------- Хэндлеры ---------------------
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id in db.get("approved", {}):
        text = (
            f"Привет, {message.from_user.first_name}!\n\n"
            "У тебя уже есть доступ к сигналам. Нажми /signal чтобы выбрать пару."
        )
        await message.answer(text)
        return

    if user_id not in db.get("pending", {}):
        db.setdefault("pending", {})[user_id] = {
            "username": message.from_user.username or "",
            "first_name": message.from_user.first_name or ""
        }
        save_db(db)

    text = (
        "Привет!\n\n"
        "Чтобы получить доступ к сигналам, зарегистрируйся по моей ссылке:\n\n"
        f"{REF_LINK}\n\n"
        "После регистрации пришли сюда свой Pocket Option ID командой:\n"
        "/id <твой_PO_id>\n\n"
        "После проверки админом тебе откроют доступ."
    )
    await message.answer(text)

@dp.message_handler(commands=["id"])
async def cmd_id(message: types.Message):
    parts = message.text.strip().split()
    if len(parts) != 2:
        await message.reply("Неверный формат. Пример: /id 123456")
        return
    user_id = str(message.from_user.id)
    po_id = parts[1]
    db.setdefault("pending", {}).setdefault(user_id, {})["po_id"] = po_id
    save_db(db)
    await message.reply("Спасибо! Твой PO ID сохранён. Ожидай подтверждения админом.")

@dp.message_handler(commands=["pending"])
async def cmd_pending(message: types.Message):
    if ADMIN_ID is None or message.from_user.id != ADMIN_ID:
        await message.reply("У тебя нет прав для этой команды.")
        return
    pend = db.get("pending", {})
    if not pend:
        await message.reply("Список ожидающих пуст.")
        return
    text = "Ожидающие пользователи:\n"
    for uid, info in pend.items():
        text += f"- {uid} | {info.get('first_name','')} @{info.get('username','')} | PO_ID: {info.get('po_id','-')}\n"
    await message.reply(text)

@dp.message_handler(commands=["approve"])
async def cmd_approve(message: types.Message):
    if ADMIN_ID is None or message.from_user.id != ADMIN_ID:
        await message.reply("У тебя нет прав для этой команды.")
        return
    parts = message.text.strip().split()
    if len(parts) != 2:
        await message.reply("Использование: /approve <telegram_user_id>")
        return
    user_to = parts[1]
    if user_to in db.get("pending", {}):
        db.setdefault("approved", {})[user_to] = db["pending"].pop(user_to)
        save_db(db)
        await message.reply(f"Пользователь {user_to} одобрен.")
        try:
            await bot.send_message(int(user_to), "Тебе выдан доступ к сигналам! Используй /signal")
        except Exception:
            logger.exception("Не удалось отправить уведомление пользователю")
    else:
        await message.reply("Пользователь не найден в ожидающих.")

@dp.message_handler(commands=["revoke"])
async def cmd_revoke(message: types.Message):
    if ADMIN_ID is None or message.from_user.id != ADMIN_ID:
        await message.reply("У тебя нет прав для этой команды.")
        return
    parts = message.text.strip().split()
    if len(parts) != 2:
        await message.reply("Использование: /revoke <telegram_user_id>")
        return
    user_to = parts[1]
    if user_to in db.get("approved", {}):
        db.setdefault("pending", {})[user_to] = db["approved"].pop(user_to)
        save_db(db)
        await message.reply(f"Доступ пользователя {user_to} отозван и перенесён в ожидающие.")
        try:
            await bot.send_message(int(user_to), "Твой доступ к сигналам был отозван.")
        except Exception:
            logger.exception("Не удалось уведомить пользователя")
    else:
        await message.reply("Пользователь не найден в одобренных.")

@dp.message_handler(commands=["signal"])
async def cmd_signal(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id not in db.get("approved", {}):
        await message.reply("У тебя нет доступа. Сначала зарегистрируйся по ссылке и дождись подтверждения.")
        return
    await message.reply("Выбери валютную пару:", reply_markup=pairs_keyboard())

# Обработка выбора пары
@dp.callback_query_handler(lambda c: c.data and c.data.startswith("pair|"))
async def callback_pair(callback_query: types.CallbackQuery):
    await callback_query.answer()
    _, pair_slug = callback_query.data.split("|", 1)
    await bot.send_message(callback_query.from_user.id, "Выбери таймфрейм:", reply_markup=timeframes_keyboard(pair_slug))

# Обработка выбора таймфрейма
@dp.callback_query_handler(lambda c: c.data and c.data.startswith("tf|"))
async def callback_tf(callback_query: types.CallbackQuery):
    await callback_query.answer()
    _, pair_slug, tf_code = callback_query.data.split("|", 2)

    user_id = str(callback_query.from_user.id)
    if user_id not in db.get("approved", {}):
        await bot.send_message(callback_query.from_user.id, "У тебя нет доступа к сигналам.")
        return

    pair_name = next((k for k, v in PAIRS.items() if v == pair_slug), pair_slug)
    tf_name = next((k for k, v in TIMEFRAMES.items() if v == tf_code), tf_code)

    try:
        direction, raw_label = get_investing_signal(pair_slug, tf_code)
    except Exception:
        logger.exception("Ошибка парсинга Investing.com")
        await bot.send_message(callback_query.from_user.id, "Не удалось получить сигнал. Попробуйте позже.")
        return

    emoji = "📈" if direction == "Вверх" else "📉" if direction == "Вниз" else "⚪"
    text = (
        f"📢 Сигнал для {pair_name} ({tf_name})\n"
        f"Направление: {direction} {emoji}\n\n"
        f"🎁 Бонус к пополнению: {BONUS_TEXT}\n"
        f"Регистрация и бонус: {REF_LINK}"
    )
    await bot.send_message(callback_query.from_user.id, text)

# --------------------- Парсер Investing.com ---------------------
def get_investing_signal(pair_slug: str, tf: str):
    '''
    Попытка извлечь итоговую рекомендацию для заданной пары и таймфрейма.
    Возвращает (direction, raw_label) — direction: "Вверх"/"Вниз"/"Неопределенно".
    '''
    url = f"https://www.investing.com/currencies/{pair_slug}-technical"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    resp = requests.get(url, headers=headers, timeout=15)
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}")

    soup = BeautifulSoup(resp.text, "html.parser")

    # 1) Попробуем найти таблицу с классом, содержащим "technicalSummaryTbl" или похожую
    label = None
    table = soup.find("table", {"class": lambda v: v and "technicalSummaryTbl" in v})
    if table:
        for row in table.find_all("tr"):
            cols = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
            if not cols:
                continue
            if tf.lower() in cols[0].lower():
                label = cols[-1]
                break

    # 2) Если не нашли, ищем в тексте страницы первые вхождения меток
    if not label:
        text = soup.get_text(separator=" ").strip()
        for candidate in ["Strong Buy", "Buy", "Neutral", "Sell", "Strong Sell"]:
            if candidate.lower() in text.lower():
                label = candidate
                break

    # 3) Больше эвристик: ищем конкретные блоки
    if not label:
        blocks = soup.find_all(lambda tag: tag.name in ["div", "section"] and "summary" in (tag.get("class") or []))
        for b in blocks:
            for candidate in ["Strong Buy", "Buy", "Neutral", "Sell", "Strong Sell"]:
                if candidate.lower() in b.get_text(separator=" ").lower():
                    label = candidate
                    break
            if label:
                break

    # 4) Если всё ещё не найдено — ищем прямо в HTML
    if not label:
        for candidate in ["Strong Buy", "Buy", "Neutral", "Sell", "Strong Sell"]:
            if candidate.lower() in resp.text.lower():
                label = candidate
                break

    if not label:
        return "Неопределенно", "Unknown"

    l = label.lower()
    if "buy" in l:
        return "Вверх", label
    if "sell" in l:
        return "Вниз", label
    return "Неопределенно", label

# --------------------- Запуск ---------------------
if __name__ == "__main__":
    save_db(db)  # инициализация файла
    if ADMIN_ID is None:
        logger.warning("ADMIN_ID не установлен. Установите переменную окружения ADMIN_ID или подставьте свой ID в коде, чтобы использовать админ-команды.")
    executor.start_polling(dp, skip_updates=True)
