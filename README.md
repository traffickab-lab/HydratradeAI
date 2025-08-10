
README — Pocket Option Signals Bot
=================================

Содержимое архива:
- pocket_option_signals_bot.py  — основной код бота
- requirements.txt              — зависимости
- db.json (создаётся автоматически при первом запуске)

Краткая инструкция (локально):
1. Установи Python 3.8+.
2. В папке с файлами создай виртуальное окружение:
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS / Linux:
   source venv/bin/activate
3. Установи зависимости:
   pip install -r requirements.txt
4. Запусти бота:
   python pocket_option_signals_bot.py

Переменные окружения (необязательно — уже подставлены в код):
- TOKEN       — токен Telegram-бота (можно задать переменной окружения)
- REF_LINK    — реферальная ссылка Pocket Option
- BONUS_TEXT  — текст бонуса
- ADMIN_ID    — numeric Telegram ID, который имеет права подтверждать пользователей

Развёртывание на Railway (кратко):
1. Создай репозиторий на GitHub и залей файлы.
2. Зарегистрируйся на https://railway.app и подключи свой GitHub.
3. Создай новый проект -> Deploy from GitHub -> выбери репозиторий.
4. В настройках проекта добавь переменные окружения (TOKEN, REF_LINK, BONUS_TEXT, ADMIN_ID) — опционально, можно оставить значения в коде.
5. Start command: python pocket_option_signals_bot.py

Примечания:
- Токен — секрет. Если публиковал его публично, regenarate через @BotFather.
- Парсер Investing.com — HTML-эвристики. Если сайт изменит верстку, парсер может перестать работать; в этом случае пришли лог — я помогу исправить.
- База пользователей хранится в db.json в той же папке.

Удачи! Если нужно, могу подготовить инструкции по заливке на GitHub и подключению к Railway.
