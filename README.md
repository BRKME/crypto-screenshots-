# 📸 CMC Screenshots - Automated Crypto Market Screenshots

Автоматический парсер для создания скриншотов крипто-рынков с публикацией в Telegram и Twitter.

## 🎯 Возможности

- ✅ Автоматические скриншоты крипто-рынков по расписанию
- ✅ Умная обрезка и оптимизация изображений под Telegram
- ✅ Публикация в Telegram с картинками и подписями
- ✅ Публикация в Twitter (опционально)
- ✅ История публикаций
- ✅ Lock-файлы (предотвращение параллельного запуска)
- ✅ Retry логика при ошибках
- ✅ Полное логирование

## 📊 Источники данных

1. **Fear & Greed Index** - индекс страха и жадности
2. **Altcoin Season Index** - индекс сезона альткоинов
3. **Bitcoin Dominance** - доминация Bitcoin
4. **Bitcoin ETF Tracker** - трекер Bitcoin ETF
5. **Ethereum ETF Tracker** - трекер Ethereum ETF
6. **Derivatives Market** - рынок деривативов
7. **Top Gainers** - топ растущих монет
8. **Token Unlocks** - календарь разблокировок токенов

## ⏰ Расписание

Скриншоты публикуются каждые 3 часа:

- **00:00 UTC** - Fear & Greed Index
- **03:00 UTC** - Bitcoin Dominance
- **06:00 UTC** - Bitcoin ETF Tracker
- **09:00 UTC** - Altcoin Season Index
- **12:00 UTC** - Derivatives Market
- **15:00 UTC** - Ethereum ETF Tracker
- **18:00 UTC** - Top Gainers
- **21:00 UTC** - Token Unlocks

## 🚀 Установка

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/BRKME/CMC_Screenshots.git
cd CMC_Screenshots
```

### 2. Установите зависимости

```bash
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium
```

### 3. Настройте переменные окружения

Создайте файл `.env` или установите переменные окружения:

```bash
# Telegram (обязательно)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Twitter (опционально)
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_ENABLED=true

# Настройки
MAX_RETRIES=2
```

### 4. Запустите парсер

```bash
python screenshot_parser.py
```

## 🤖 GitHub Actions (Автоматизация)

Проект настроен для автоматического запуска через GitHub Actions каждые 3 часа.

### Настройка Secrets в GitHub:

1. Перейдите в `Settings` → `Secrets and variables` → `Actions`
2. Добавьте следующие секреты:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `TWITTER_API_KEY` (опционально)
   - `TWITTER_API_SECRET` (опционально)
   - `TWITTER_ACCESS_TOKEN` (опционально)
   - `TWITTER_ACCESS_TOKEN_SECRET` (опционально)
   - `TWITTER_BEARER_TOKEN` (опционально)

### Настройка Variables:

1. Перейдите в `Variables` (рядом с Secrets)
2. Добавьте:
   - `TWITTER_ENABLED` = `true` или `false`

## 📁 Структура проекта

```
CMC_Screenshots/
├── screenshot_parser.py      # Основной парсер
├── sources_config.py          # Конфигурация источников
├── requirements.txt           # Зависимости Python
├── publication_history.json   # История публикаций (создается автоматически)
├── screenshots/               # Директория со скриншотами (создается автоматически)
├── .github/
│   └── workflows/
│       └── screenshot_parser.yml  # GitHub Actions workflow
└── README.md
```

## 🛠️ Конфигурация

### Добавление нового источника

Отредактируйте `sources_config.py`:

```python
SCREENSHOT_SOURCES = {
    "new_source": {
        "name": "Название источника",
        "url": "https://example.com",
        "selector": "CSS селектор элемента",  # или None для полной страницы
        "wait_for": "селектор для ожидания",
        "telegram_title": "📊 Заголовок",
        "telegram_hashtags": "#Hash #Tags",
        "enabled": True,
        "priority": 1
    }
}
```

### Изменение расписания

Отредактируйте `SCHEDULE` в `sources_config.py`:

```python
SCHEDULE = {
    0: "fear_greed",    # 00:00 UTC
    3: "new_source",    # 03:00 UTC
    # ...
}
```

## 📝 Логирование

Все действия логируются в файл `screenshot_parser.log`:

```bash
tail -f screenshot_parser.log
```

## 🐛 Решение проблем

### Скриншоты не создаются

1. Проверьте установку Playwright:
```bash
playwright install chromium
playwright install-deps chromium
```

2. Проверьте логи:
```bash
cat screenshot_parser.log
```

### Ошибки Telegram

1. Проверьте токен бота:
```bash
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
```

2. Проверьте Chat ID:
```bash
curl https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
```

### Ошибки Twitter

1. Убедитесь что все ключи API установлены
2. Проверьте права доступа в Developer Portal
3. Временно отключите Twitter: `TWITTER_ENABLED=false`

## 📊 Мониторинг

### Проверка истории публикаций

```bash
cat publication_history.json
```

### Просмотр последних скриншотов

```bash
ls -lht screenshots/ | head
```

## 🔒 Безопасность

- Никогда не коммитьте `.env` файл с секретами
- Используйте GitHub Secrets для CI/CD
- Регулярно обновляйте зависимости:
```bash
pip install --upgrade -r requirements.txt
```

## 📜 Лицензия

MIT License

## 👤 Автор

**BRKME**

- GitHub: [@BRKME](https://github.com/BRKME)
- Основано на логике проекта [CMC_AI](https://github.com/BRKME/CMC_AI)

## 🤝 Вклад

Pull requests приветствуются! Для крупных изменений сначала откройте issue.

## 📞 Поддержка

Если у вас возникли проблемы или вопросы, создайте [issue](https://github.com/BRKME/CMC_Screenshots/issues).

---

⭐ Если проект полезен, поставьте звезду на GitHub!
