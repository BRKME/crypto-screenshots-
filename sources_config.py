"""
Конфигурация источников для скриншотов
Version: 1.3 - Automatic rotation every 30 minutes (no more SCHEDULE dict)
"""

# Конфигурация источников для скриншотов
SCREENSHOT_SOURCES = {
    "fear_greed": {
        "name": "Crypto Fear & Greed Index",
        "url": "https://coinmarketcap.com/charts/fear-and-greed-index/",
        "selector": "#__next > div.sc-97df1870-1.laPgsv.global-layout-v2 > div.main-content > div.cmc-body-wrapper > div > div > div.sc-65e7f566-0.jpCqhh > div > div > div.sc-65e7f566-0.izPDqH > div.sc-65e7f566-0.kijrGb",
        "wait_for": "div.sc-65e7f566-0.kijrGb",
        "telegram_title": "📊 Fear & Greed Index",
        "telegram_hashtags": "#FearAndGreed #CryptoSentiment #Bitcoin",
        "enabled": True,
        "priority": 1
    },
    
    "altcoin_season": {
        "name": "Altcoin Season Index",
        "url": "https://coinmarketcap.com/charts/altcoin-season-index/",
        "selector": "div.kunWxz",  # ✅ Контейнер с 3 блоками
        "wait_for": "div.kunWxz",
        "telegram_title": "🌈 Altcoin Season Index",
        "telegram_hashtags": "#AltcoinSeason #Altcoins #CryptoMarket",
        "enabled": True,
        "priority": 2
    },
    
    "btc_dominance": {
        "name": "Bitcoin Dominance",
        "url": "https://coinmarketcap.com/charts/bitcoin-dominance/",
        "selector": "#__next > div.sc-97df1870-1.laPgsv.global-layout-v2 > div.main-content > div.cmc-body-wrapper > div > div > div.sc-65e7f566-0.jpCqhh > div > div > div.sc-65e7f566-0.izPDqH > div.sc-65e7f566-0.gWkXfC > div.sc-65e7f566-0.cOcRup > div > div.sc-65e7f566-0.lhhnRU",
        "wait_for": "div.sc-65e7f566-0.lhhnRU",
        "telegram_title": "₿ Bitcoin Dominance",
        "telegram_hashtags": "#Bitcoin #BTC #Dominance",
        "enabled": True,
        "priority": 3
    },
    
    "eth_etf": {
        "name": "Ethereum ETF Tracker",
        "url": "https://coinmarketcap.com/etf/ethereum/",
        "selector": "#__next > div.sc-97df1870-1.laPgsv.global-layout-v2 > div.main-content > div.cmc-body-wrapper > div > div > div.sc-65e7f566-0.jpCqhh > div > div.sc-65e7f566-0.dyAjoq > div.sc-65e7f566-0.cXxTPe > div > div > div.sc-65e7f566-0.dUpMa-D > div > div:nth-child(1) > div > div.sc-65e7f566-0.kRIzHD > span",
        "wait_for": "div.sc-65e7f566-0.kRIzHD",
        "telegram_title": "💎 Ethereum ETF Tracker",
        "telegram_hashtags": "#Ethereum #ETF #ETH",
        "enabled": True,
        "priority": 4
    },
    
    "btc_etf": {
        "name": "Bitcoin ETF Tracker",
        "url": "https://coinmarketcap.com/etf/bitcoin/",
        "selector": "#__next > div.sc-97df1870-1.laPgsv.global-layout-v2 > div.main-content > div.cmc-body-wrapper > div > div > div.sc-65e7f566-0.jpCqhh > div > div.sc-65e7f566-0.dyAjoq > div.sc-65e7f566-0.cXxTPe > div > div > div.sc-65e7f566-0.dUpMa-D > div > div:nth-child(1) > div > div.sc-65e7f566-0.kRIzHD > span",
        "wait_for": "div.sc-65e7f566-0.kRIzHD",
        "telegram_title": "₿ Bitcoin ETF Tracker",
        "telegram_hashtags": "#Bitcoin #ETF #BTC",
        "enabled": True,
        "priority": 5
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
        "priority": 7
    },
    
    "token_unlocks": {
        "name": "Token Unlocks",
        "url": "https://dropstab.com/vesting",
        "selector": "main",  # ✅ Захватываем весь main, JS скроет лишние строки
        "wait_for": "table",
        "telegram_title": "🔓 Token Unlocks Calendar",
        "telegram_hashtags": "#TokenUnlocks #Vesting #Crypto",
        "enabled": True,
        "priority": 8
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
    "telegram_max_width": 1280,
    "telegram_max_height": 1280,
    "quality": 85,
    "format": "JPEG",
    "crop_padding": 20
}

# Настройки скриншотов
SCREENSHOT_SETTINGS = {
    "viewport_width": 1920,
    "viewport_height": 1080,
    "full_page": False,
    "wait_timeout": 30000,
    "wait_after_load": 5
}
