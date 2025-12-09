"""
Конфигурация источников для скриншотов
Version: 1.0
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
        "name": "Top 100 Coins Performance (90 Days)",
        "url": "https://coinmarketcap.com/charts/altcoin-season-index/",
        "selector": None,  # Скриншот всей страницы с последующей обрезкой
        "wait_for": "canvas",  # Ждем загрузки графика
        "telegram_title": "🌈 Altcoin Season Index",
        "telegram_hashtags": "#AltcoinSeason #Altcoins #CryptoMarket",
        "enabled": True,
        "priority": 2
    },
    
    "btc_dominance": {
        "name": "Bitcoin Dominance",
        "url": "https://coinmarketcap.com/charts/bitcoin-dominance/",  # FIX BUG #5: Правильный URL
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
        "name": "Derivatives Market",
        "url": "https://coinmarketcap.com/charts/derivatives-market/",
        "selector": "#__next > div.sc-97df1870-1.laPgsv.global-layout-v2 > div.main-content > div.cmc-body-wrapper > div > div > div.sc-65e7f566-0.jpCqhh > div > div > div.sc-65e7f566-0.izPDqH > div.sc-65e7f566-0.hAaYGH > div.sc-65e7f566-0.fBknJk > div",
        "wait_for": "div.sc-65e7f566-0.fBknJk",
        "telegram_title": "📈 Derivatives Market",
        "telegram_hashtags": "#Derivatives #Futures #CryptoTrading",
        "enabled": True,
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
        "selector": None,  # Скриншот всей страницы с последующей обрезкой
        "wait_for": "table",
        "telegram_title": "🔓 Token Unlocks Calendar",
        "telegram_hashtags": "#TokenUnlocks #Vesting #Crypto",
        "enabled": True,
        "priority": 8
    }
}

# Расписание публикаций (час UTC : source_key)
# FIX BUG #8: Заполняем все 24 часа с fallback
SCHEDULE = {
    0: "fear_greed",
    1: "fear_greed",        # Fallback
    2: "btc_dominance",
    3: "btc_dominance",
    4: "btc_etf",
    5: "btc_etf",
    6: "btc_etf",
    7: "altcoin_season",
    8: "altcoin_season",
    9: "altcoin_season",
    10: "derivatives",
    11: "derivatives",
    12: "derivatives",
    13: "eth_etf",
    14: "eth_etf",
    15: "eth_etf",
    16: "top_gainers",
    17: "top_gainers",
    18: "top_gainers",
    19: "token_unlocks",
    20: "token_unlocks",
    21: "token_unlocks",
    22: "fear_greed",        # Fallback
    23: "btc_dominance"      # Fallback
}

# Настройки для обработки изображений
IMAGE_SETTINGS = {
    "telegram_max_width": 1280,
    "telegram_max_height": 1280,
    "quality": 85,
    "format": "JPEG",
    "crop_padding": 20  # Дополнительный отступ при обрезке
}

# Настройки скриншотов
SCREENSHOT_SETTINGS = {
    "viewport_width": 1920,
    "viewport_height": 1080,
    "full_page": False,  # По умолчанию - только видимая область
    "wait_timeout": 30000,  # 30 секунд
    "wait_after_load": 5  # Секунды ожидания после загрузки страницы
}
