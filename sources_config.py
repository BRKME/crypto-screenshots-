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
        "crop": {"top": 50, "right": 30, "bottom": 50, "left": 0}  # ✅ Обрезка сверху, справа и снизу
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
        "hide_elements": "table, ul, ol, [class*='token'], [class*='Token'], [class*='list'], [class*='List']",  # ✅ Скрыть список токенов
        "crop": {"top": 50, "right": 0, "bottom": 50, "left": 0}  # ✅ Обрезка сверху и снизу
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
        "hide_elements": "table, ul, ol, [class*='list'], [class*='List']",  # ✅ Скрыть лишние списки
        "crop": {"top": 50, "right": 0, "bottom": 50, "left": 0}  # ✅ Обрезка сверху и снизу
    },
    
    "eth_etf": {
        "name": "Ethereum ETF Tracker",
        "url": "https://coinmarketcap.com/etf/ethereum/",
        "selector": "[data-role='content-wrapper']",
        "wait_for": "[data-role='content-wrapper']",
        "telegram_title": "💎 Ethereum ETF Tracker",
        "telegram_hashtags": "#Ethereum #ETF #ETH",
        "enabled": True,
        "priority": 4,
        "skip_width_padding": True,
        "element_padding": {"top": 60, "right": 40, "bottom": 60, "left": 40},
        "scale": 1.0,
        "crop": {"top": 50, "right": 30, "bottom": 220, "left": 0},
        "extra_wait": 10
    },
    
    "btc_etf": {
        "name": "Bitcoin ETF Tracker",
        "url": "https://coinmarketcap.com/etf/bitcoin/",
        "selector": "[data-role='content-wrapper']",
        "wait_for": "[data-role='content-wrapper']",
        "telegram_title": "₿ Bitcoin ETF Tracker",
        "telegram_hashtags": "#Bitcoin #ETF #BTC",
        "enabled": True,
        "priority": 5,
        "skip_width_padding": True,
        "element_padding": {"top": 60, "right": 40, "bottom": 60, "left": 40},
        "scale": 1.0,
        "crop": {"top": 50, "right": 30, "bottom": 220, "left": 0},
        "extra_wait": 10
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
        "scale": 1.0,  # ✅ Уменьшаем scale до 1.0 (было 1.2)
        "crop": {"top": 20, "right": 20, "bottom": 20, "left": 20}  # ✅ Обрезка со всех сторон
    },
    
    "token_unlocks": {
        "name": "Token Unlocks Next 7 Days",
        "url": "https://dropstab.com/vesting",
        "selector": "body",
        "wait_for": "table tbody tr",
        "telegram_title": "🔓 Token Unlocks Next 7 Days",
        "telegram_hashtags": "#TokenUnlocks #Vesting #Crypto",
        "enabled": True,
        "priority": 8,
        "extra_wait": 20,
        "viewport_width": 1920,
        "viewport_height": 1080,
        "hide_elements": "aside, nav, header, footer, [class*='sidebar'], [class*='Sidebar'], [class*='menu'], [class*='Menu'], [class*='nav'], [class*='Nav'], table tbody tr:nth-child(n+7), [class*='banner'], [class*='Banner'], [class*='ad'], [class*='Ad'], [class*='advertisement'], iframe, [id*='ad'], .description, h1, h2, p, button, [role='banner'], [role='navigation'], [class*='cookie']",
        "crop": {"top": 150, "right": 300, "bottom": 400, "left": 300},
        "skip_ai": True
    },
    
    "heatmap": {
        "name": "Crypto Market Heatmap",
        "url": "https://coincodex.com/heatmap/",
        "selector": "canvas",
        "wait_for": "canvas",
        "telegram_title": "🗺️ Crypto Market Heatmap",
        "telegram_hashtags": "#Heatmap #MarketBreadth #Crypto",
        "enabled": True,
        "priority": 8,
        "extra_wait": 8,
        "viewport_width": 1920,
        "viewport_height": 1080
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

# ===============================================================================
# РАСПИСАНИЕ - ГИБКАЯ ЛОГИКА ПО ВРЕМЕНИ MSK
# ===============================================================================
# Новая схема публикаций по времени MSK
#
# 16:30–17:00 MSK → Daily Market Sentiment
#   Источники: fear_greed, altcoin_season, btc_dominance (ротация случайная)
#
# 18:30–19:00 MSK → Token Unlocks Watch
#   Источник: token_unlocks
#
# 20:00–21:00 MSK → ETF Flows Desk
#   Источники: btc_etf, eth_etf (ротация случайная)
#
# 22:00 MSK → Top Gainers Radar
#   Источник: top_gainers
#
# 01:00 MSK (опционально) → ETF Anomaly / Market Alert
#   Источники: btc_etf, eth_etf (только если поток >$100M)
#   
# MSK = UTC+3
# ===============================================================================

POST_SCHEDULE = {
    "market_breadth_morning": {
        "time_range_msk": (7.0, 7.83),
        "sources": ["heatmap"],
        "selection": "fixed"
    },
    "daily_market_sentiment": {
        "time_range_msk": (16.5, 17.0),
        "sources": ["fear_greed", "altcoin_season", "btc_dominance"],
        "selection": "random"
    },
    "token_unlocks_watch": {
        "time_range_msk": (18.5, 18.92),
        "sources": ["token_unlocks"],
        "selection": "fixed"
    },
    "market_breadth_evening": {
        "time_range_msk": (19.0, 19.83),
        "sources": ["heatmap"],
        "selection": "fixed"
    },
    "btc_etf_flows": {
        "time_range_msk": (20.0, 20.5),
        "sources": ["btc_etf"],
        "selection": "fixed"
    },
    "eth_etf_flows": {
        "time_range_msk": (20.5, 21.0),
        "sources": ["eth_etf"],
        "selection": "fixed"
    },
    "top_gainers_radar": {
        "time_range_msk": (22.0, 22.5),
        "sources": ["top_gainers"],
        "selection": "fixed"
    }
}

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
