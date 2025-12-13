"""
Конфигурация источников для скриншотов
Version: 1.3 - Automatic rotation every 30 minutes (no more SCHEDULE dict)
"""

# Конфигурация источников для скриншотов
SCREENSHOT_SOURCES = {
    "fear_greed": {
        "name": "Crypto Fear & Greed Index",
        "url": "https://coinmarketcap.com/charts/fear-and-greed-index/",
        "selector": "div.sc-65e7f566-0.kijrGb",  # ✅ Упрощенный селектор - основной контейнер
        "wait_for": "div.sc-65e7f566-0.kijrGb",
        "telegram_title": "📊 Fear & Greed Index",
        "telegram_hashtags": "#FearAndGreed #CryptoSentiment #Bitcoin",
        "enabled": True,
        "priority": 1,
        "skip_width_padding": True,  # ✅ БЕЗ огромных полей
        "element_padding": {"top": 40, "right": 30, "bottom": 40, "left": 30},  # Небольшие отступы
        "scale": 1.0,  # ✅ Нормальный размер
        "hide_elements": "p, [class*='description'], [class*='Description'], [data-role='description']",  # ✅ Скрыть текстовые описания
        "crop": {"top": 10, "right": 30, "bottom": 0, "left": 0}  # ✅ НОВОЕ: Обрезка справа и сверху
    },
    
    "altcoin_season": {
        "name": "Altcoin Season Index",
        "url": "https://coinmarketcap.com/charts/altcoin-season-index/",
        "selector": "div.kunWxz",  # ✅ Контейнер с основными блоками
        "wait_for": "div.kunWxz",
        "telegram_title": "🌈 Altcoin Season Index",
        "telegram_hashtags": "#AltcoinSeason #Altcoins #CryptoMarket",
        "enabled": True,
        "priority": 2,
        "skip_width_padding": True,  # ✅ БЕЗ огромных полей
        "element_padding": {"top": 40, "right": 30, "bottom": 40, "left": 30},  # Небольшие отступы
        "scale": 1.0,  # ✅ Нормальный размер
        "hide_elements": "table, ul, ol, [class*='token'], [class*='Token'], [class*='list'], [class*='List']"  # ✅ Скрыть список токенов
    },
    
    "btc_dominance": {
        "name": "Bitcoin Dominance",
        "url": "https://coinmarketcap.com/charts/bitcoin-dominance/",
        "selector": "div.gWkXfC",  # ✅ Контейнер со всеми 3 блоками
        "wait_for": "div.gWkXfC",
        "telegram_title": "₿ Bitcoin Dominance",
        "telegram_hashtags": "#Bitcoin #BTC #Dominance",
        "enabled": True,
        "priority": 3,
        "skip_width_padding": True,  # ✅ БЕЗ огромных полей
        "element_padding": {"top": 40, "right": 30, "bottom": 40, "left": 30},  # Небольшие отступы
        "scale": 1.0,  # ✅ Нормальный размер
        "hide_elements": "table, ul, ol, [class*='list'], [class*='List']"  # ✅ Скрыть лишние списки
    },
    
    "eth_etf": {
        "name": "Ethereum ETF Tracker",
        "url": "https://coinmarketcap.com/etf/ethereum/",
        "selector": "[data-role='content-wrapper']",  # ✅ Селектор с 3 карточками
        "wait_for": "[data-role='content-wrapper']",
        "telegram_title": "💎 Ethereum ETF Tracker",
        "telegram_hashtags": "#Ethereum #ETF #ETH",
        "enabled": True,
        "priority": 4,
        "skip_width_padding": True,  # ✅ БЕЗ огромных полей
        "element_padding": {"top": 60, "right": 40, "bottom": 60, "left": 40},  # Небольшие отступы
        "scale": 1.0  # ✅ Без увеличения (карточки нормального размера)
    },
    
    "btc_etf": {
        "name": "Bitcoin ETF Tracker",
        "url": "https://coinmarketcap.com/etf/bitcoin/",
        "selector": "[data-role='content-wrapper']",  # ✅ Селектор с 3 карточками
        "wait_for": "[data-role='content-wrapper']",
        "telegram_title": "₿ Bitcoin ETF Tracker",
        "telegram_hashtags": "#Bitcoin #ETF #BTC",
        "enabled": True,
        "priority": 5,
        "skip_width_padding": True,  # ✅ БЕЗ огромных полей
        "element_padding": {"top": 60, "right": 40, "bottom": 60, "left": 40},  # Небольшие отступы
        "scale": 1.0  # ✅ Без увеличения (карточки нормального размера)
    },
    
    "derivatives": {
        "name": "Crypto Derivatives",
        "url": "https://coinmarketcap.com/charts/perpetual-markets/",
        "selector": None,
        "wait_for": "table",
        "telegram_title": "📈 Crypto Derivatives Market",
        "telegram_hashtags": "#Derivatives #Futures #Trading",
        "enabled": False,  # ❌ Отключен: CMC anti-bot защита
        "priority": 6
    },
    
    "top_gainers": {
        "name": "Top Gainers",
        "url": "https://dropstab.com/",
        "selector": "#__next > div.z-app.relative > div > div.lg\\:ml-auto.w-full.flex.flex-col.lg\\:w-\\[calc\\(100\\%-72px\\)\\].xl\\:w-\\[calc\\(100\\%-256px\\)\\] > main > div > div.relative.z-0.w-full.styles_carousel__lIy83.mb-4.lg\\:mb-6 > div > div > div:nth-child(1) > div > section > span",
        "wait_for": "section",
        "telegram_title": "🚀 Top Gainers Today",
        "telegram_hashtags": "#TopGainers #Crypto #Movers",
        "enabled": True,
        "priority": 7,
        "skip_width_padding": True,  # ✅ НЕ добавлять белый padding по бокам
        "element_padding": {"top": 40, "right": 30, "bottom": 40, "left": 30},  # Небольшие отступы
        "scale": 1.2  # ✅ Немного увеличить для читаемости
    },
    
    "token_unlocks": {
        "name": "Token Unlocks",
        "url": "https://tokenomist.ai/",
        "selector": "[role='group'][aria-roledescription='slide']",  # ✅ Селектор для карточки
        "wait_for": "[role='group'][aria-roledescription='slide']",
        "telegram_title": "🔓 Cliff Unlocks Next 7D",
        "telegram_hashtags": "#TokenUnlocks #Vesting #Crypto",
        "enabled": True,
        "priority": 8,
        "skip_width_padding": True,  # ✅ БЕЗ огромных полей
        "element_padding": {"top": 40, "right": 30, "bottom": 40, "left": 30},  # Небольшие отступы
        "scale": 1.0,  # ✅ Нормальный размер
        "hide_elements": "table, [class*='dashboard'], [class*='Dashboard'], [class*='trending'], [class*='Trending']"  # ✅ Скрыть таблицы и trending
    },
    
    "heatmap": {
        "name": "Crypto Heatmap",
        "url": "https://coin360.com/",
        "selector": None,
        "wait_for": "canvas",
        "telegram_title": "🔥 Crypto Market Map",
        "telegram_hashtags": "#Heatmap #Crypto #Market",
        "enabled": False,  # ❌ ОТКЛЮЧЕН - выглядит плохо
        "priority": 9,
        "close_modal": True
    }
}

# ===============================================================================
# РАСПИСАНИЕ - АВТОМАТИЧЕСКАЯ РОТАЦИЯ
# ===============================================================================
# Источники публикуются автоматически по кругу каждые 30 минут.
# Логика: 48 слотов в сутки (24 часа × 2), источники берутся по порядку из
# SCREENSHOT_SOURCES (только enabled=True).
#
# При 7 активных источниках (derivatives отключен):
# - 00:00 → fear_greed
# - 00:30 → btc_dominance  
# - 01:00 → btc_etf
# - 01:30 → altcoin_season
# - 02:00 → eth_etf
# - 02:30 → top_gainers
# - 03:00 → token_unlocks
# - 03:30 → fear_greed (снова по кругу)
# - ...и так далее
#
# ⚠️ ВАЖНО: Порядок источников в SCREENSHOT_SOURCES определяет порядок публикации!
# ===============================================================================

# Настройки для обработки изображений
IMAGE_SETTINGS = {
    "telegram_max_width": 1200,  # ✅ Увеличено до 1200 для полной ширины в Telegram
    "telegram_min_width": 1000,  # ✅ Минимальная ширина (добавляем padding если меньше)
    "telegram_max_height": 1280,
    "quality": 85,
    "format": "JPEG",
    "crop_padding": 20,
    "add_padding_if_narrow": True,  # ✅ Добавлять padding если изображение узкое
    "padding_color": (255, 255, 255)  # Белый цвет padding (или (240, 242, 245) для светло-серого)
}

# Настройки скриншотов
SCREENSHOT_SETTINGS = {
    "viewport_width": 1920,
    "viewport_height": 1080,
    "full_page": False,
    "wait_timeout": 30000,
    "wait_after_load": 5
}
