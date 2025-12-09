# 🚀 Быстрый старт

## Локальное тестирование (без Telegram/Twitter)

### 1. Установка

```bash
# Клонируйте репозиторий
git clone https://github.com/BRKME/CMC_Screenshots.git
cd CMC_Screenshots

# Установите зависимости
pip install -r requirements.txt

# Установите Playwright браузер
playwright install chromium
playwright install-deps chromium
```

### 2. Тестирование скриншотов

Протестируйте любой источник БЕЗ отправки в Telegram/Twitter:

```bash
# Показать список доступных источников
python test_screenshot.py

# Тест Fear & Greed Index
python test_screenshot.py fear_greed

# Тест Bitcoin Dominance
python test_screenshot.py btc_dominance

# Тест Altcoin Season
python test_screenshot.py altcoin_season
```

Скриншоты сохранятся в папку `screenshots/`

### 3. Настройка Telegram

Создайте файл `.env`:

```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
TWITTER_ENABLED=false
```

Получение токенов:
- Создайте бота через [@BotFather](https://t.me/BotFather)
- Получите Chat ID через [@userinfobot](https://t.me/userinfobot)

### 4. Тестовый запуск с Telegram

```bash
python screenshot_parser.py
```

Скрипт сделает скриншот согласно текущему часу UTC и отправит в Telegram.

## GitHub Actions (Автоматизация)

### 1. Форкните репозиторий

### 2. Добавьте Secrets

`Settings` → `Secrets and variables` → `Actions` → `New repository secret`:

- `TELEGRAM_BOT_TOKEN` = ваш токен бота
- `TELEGRAM_CHAT_ID` = ваш chat ID

### 3. Включите Actions

`Actions` → `I understand my workflows, go ahead and enable them`

### 4. Готово!

Скриншоты будут публиковаться автоматически каждые 3 часа.

## Расписание публикаций

| Время UTC | Источник |
|-----------|----------|
| 00:00 | Fear & Greed Index |
| 03:00 | Bitcoin Dominance |
| 06:00 | Bitcoin ETF |
| 09:00 | Altcoin Season |
| 12:00 | Derivatives |
| 15:00 | Ethereum ETF |
| 18:00 | Top Gainers |
| 21:00 | Token Unlocks |

## Настройка источников

Отредактируйте `sources_config.py`:

```python
SCREENSHOT_SOURCES = {
    "your_source": {
        "name": "Your Source Name",
        "url": "https://example.com",
        "selector": None,  # CSS selector или None
        "wait_for": "div",  # Элемент для ожидания
        "telegram_title": "📊 Your Title",
        "telegram_hashtags": "#Your #Tags",
        "enabled": True,
        "priority": 1
    }
}

SCHEDULE = {
    0: "your_source"  # Час UTC
}
```

## Полезные команды

```bash
# Просмотр логов
tail -f screenshot_parser.log

# Просмотр истории
cat publication_history.json

# Список скриншотов
ls -lh screenshots/

# Очистка старых скриншотов
find screenshots/ -name "*.jpg" -mtime +1 -delete
```

## Устранение проблем

### Playwright не находит браузер
```bash
playwright install chromium
playwright install-deps chromium
```

### Ошибка "selector not found"
1. Проверьте селектор на актуальной странице
2. Используйте `test_screenshot.py` с `headless=False` для отладки
3. Увеличьте `wait_after_load` в `sources_config.py`

### Telegram не отправляет
1. Проверьте токен: `curl https://api.telegram.org/bot<TOKEN>/getMe`
2. Проверьте Chat ID
3. Убедитесь что бот добавлен в чат

## Дополнительно

- 📖 Полная документация: [README.md](README.md)
- 🐛 Сообщить о проблеме: [Issues](https://github.com/BRKME/CMC_Screenshots/issues)
- ⭐ Поставьте звезду если проект полезен!
