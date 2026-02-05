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
        "selector": "[data-role='main-wrapper']",
        "wait_for": "[data-role='main-wrapper']",
        "telegram_title": "🌈 Altcoin Season Index",
        "telegram_hashtags": "#AltcoinSeason #Altcoins #CryptoMarket",
        "enabled": True,
        "priority": 2,
        "viewport_width": 1280,
        "viewport_height": 800,
        "hide_elements": "aside, nav, header, footer, [class*='sidebar'], [class*='banner'], [class*='ad'], iframe, .description, h1:not(:first-of-type), table, svg[class*='chart']",
        "crop": {"top": 100, "right": 400, "bottom": 400, "left": 400}
    },
    
    "btc_dominance": {
        "name": "Bitcoin Dominance",
        "url": "https://coinmarketcap.com/charts/bitcoin-dominance/",
        "selector": ".qAEmk",
        "wait_for": "h2",
        "telegram_title": "₿ Bitcoin Dominance",
        "telegram_hashtags": "#Bitcoin #BTC #Dominance",
        "enabled": True,
        "priority": 3,
        "viewport_width": 1280,
        "viewport_height": 800,
        "hide_elements": "aside, nav, header, footer, [class*='sidebar'], [class*='banner'], [class*='ad'], iframe, .description, h1:not(:first-of-type), table, svg[class*='chart']",
        "crop": {"top": 0, "right": 0, "bottom": 20, "left": 0}
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
        "enabled": False,
        "priority": 8,
        "extra_wait": 20,
        "viewport_width": 1920,
        "viewport_height": 1080,
        "hide_elements": "aside, nav, header, footer, [class*='sidebar'], [class*='Sidebar'], [class*='menu'], [class*='Menu'], [class*='nav'], [class*='Nav'], table tbody tr:nth-child(n+7), [class*='banner'], [class*='Banner'], [class*='ad'], [class*='Ad'], [class*='advertisement'], iframe, [id*='ad'], .description, h1, h2, p, button, [role='banner'], [role='navigation'], [class*='cookie']",
        "crop": {"top": 150, "right": 300, "bottom": 400, "left": 300},
        "skip_ai": True
    },
    
    # ========================================================================
    # HEATMAP SOURCES - НОВЫЕ (COIN360, BLOCKCHAIN.COM, NDAX)
    # ========================================================================
    
    # HEATMAP V1: Coin360 (Canvas-based с текстом)
    "heatmap_v1_coin360": {
        "name": "Crypto Market Heatmap - Coin360",
        "url": "https://coin360.com/",
        "selector": "div#MAP_ID",
        "wait_for": "canvas",
        "telegram_title": "🗺️ Crypto Market Heatmap",
        "telegram_hashtags": "#Heatmap #MarketBreadth #Crypto",
        "enabled": True,
        "priority": 8,
        "extra_wait": 10,
        "viewport_width": 1920,
        "viewport_height": 1080,
        "close_modal": True,  # Закрыть модальное окно если появится
        "hide_elements": "header, nav, footer, aside, [class*='navbar'], [class*='sidebar'], [class*='banner'], [class*='ad'], [class*='cookie'], button, [class*='button']",
        "crop": {"top": 100, "right": 50, "bottom": 100, "left": 50},
        "skip_width_padding": True
    },
    
    # HEATMAP V2: Blockchain.com (Canvas-based)
    "heatmap_v2_blockchain": {
        "name": "Crypto Market Heatmap - Blockchain.com",
        "url": "https://www.blockchain.com/explorer/prices/heatmap",
        "selector": "canvas#heatmapCanvas",
        "wait_for": "canvas#heatmapCanvas",
        "telegram_title": "🗺️ Crypto Market Heatmap",
        "telegram_hashtags": "#Heatmap #MarketBreadth #Crypto",
        "enabled": True,
        "priority": 8,
        "extra_wait": 10,
        "viewport_width": 1920,
        "viewport_height": 1080,
        "element_padding": {"top": 50, "right": 50, "bottom": 50, "left": 50},
        "hide_elements": "header, nav, footer, aside, [class*='navbar'], [class*='Navigation'], [class*='sidebar'], [class*='banner'], [class*='ad'], [class*='cookie']",
        "crop": {"top": 0, "right": 0, "bottom": 0, "left": 0},
        "skip_width_padding": True
    },
    
    # HEATMAP V3: NDAX (Fallback - стандартные селекторы)
    "heatmap_v3_ndax": {
        "name": "Crypto Market Heatmap - NDAX",
        "url": "https://ndax.io/en/markets/heatmap",
        "selector": "body",
        "wait_for": "canvas",
        "telegram_title": "🗺️ Crypto Market Heatmap",
        "telegram_hashtags": "#Heatmap #MarketBreadth #Crypto",
        "enabled": True,
        "priority": 8,
        "extra_wait": 15,
        "viewport_width": 1920,
        "viewport_height": 1080,
        "hide_elements": "header, nav, footer, aside, [class*='navbar'], [class*='sidebar'], [class*='banner'], [class*='ad'], [class*='cookie']",
        "crop": {"top": 150, "right": 100, "bottom": 150, "left": 100},
        "skip_width_padding": True
    }
}

# ===============================================================================
# РАСПИСАНИЕ - ГИБКАЯ ЛОГИКА ПО ВРЕМЕНИ MSK
# ===============================================================================

POST_SCHEDULE = {
    # HEATMAP TESTING - 3 НОВЫХ ИСТОЧНИКА
    # ⚠️ FIX: GitHub Actions cron неточный (может запускаться ±10 минут)
    # Добавлен буфер 10 минут перед каждым слотом
    "heatmap_test_v1": {
        "time_range_msk": (6.85, 8.0),  # 06:51-08:00 (Coin360)
        "sources": ["heatmap_v1_coin360"],
        "selection": "fixed"
    },
    "heatmap_test_v2": {
        "time_range_msk": (9.85, 11.0),  # 09:51-11:00 (Blockchain.com)
        "sources": ["heatmap_v2_blockchain"],
        "selection": "fixed"
    },
    "heatmap_test_v3": {
        "time_range_msk": (12.85, 14.0),  # 12:51-14:00 (NDAX)
        "sources": ["heatmap_v3_ndax"],
        "selection": "fixed"
    },
    
    # REGULAR SCHEDULE
    "daily_market_sentiment": {
        "time_range_msk": (16.35, 17.0),  # 16:21-17:00 (было 16:30-17:00)
        "sources": ["fear_greed", "altcoin_season", "btc_dominance"],
        "selection": "random"
    },
    "btc_etf_flows": {
        "time_range_msk": (19.85, 20.5),  # 19:51-20:30 (было 20:00-20:30)
        "sources": ["btc_etf"],
        "selection": "fixed"
    },
    "eth_etf_flows": {
        "time_range_msk": (20.35, 21.0),  # 20:21-21:00 (было 20:30-21:00)
        "sources": ["eth_etf"],
        "selection": "fixed"
    },
    "top_gainers_radar": {
        "time_range_msk": (21.85, 22.5),  # 21:51-22:30 (было 22:00-22:30)
        "sources": ["top_gainers"],
        "selection": "fixed"
    }
}

# Настройки для обработки изображений
IMAGE_SETTINGS = {
    "telegram_max_width": 1200,
    "telegram_min_width": 1000,
    "telegram_max_height": 1280,
    "quality": 85,
    "format": "JPEG",
    "crop_padding": 20,
    "add_padding_if_narrow": True,
    "padding_color": (255, 255, 255)
}

# Настройки скриншотов
SCREENSHOT_SETTINGS = {
    "viewport_width": 1920,
    "viewport_height": 1080,
    "full_page": False,
    "wait_timeout": 30000,
    "wait_after_load": 5
}
