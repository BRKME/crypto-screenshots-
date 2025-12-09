"""
Тестовый скрипт для проверки скриншотов БЕЗ отправки в Telegram/Twitter
Использование: python test_screenshot.py <source_key>
Пример: python test_screenshot.py fear_greed
"""

import asyncio
import sys
from playwright.async_api import async_playwright
from sources_config import SCREENSHOT_SOURCES, SCREENSHOT_SETTINGS
from screenshot_parser import accept_cookies, optimize_image_for_telegram
import os
from datetime import datetime, timezone

async def test_screenshot(source_key):
    """Тестирует создание скриншота для указанного источника"""
    
    if source_key not in SCREENSHOT_SOURCES:
        print(f"❌ Источник '{source_key}' не найден!")
        print(f"Доступные источники: {', '.join(SCREENSHOT_SOURCES.keys())}")
        return False
    
    source_config = SCREENSHOT_SOURCES[source_key]
    
    print("="*70)
    print(f"🧪 ТЕСТИРОВАНИЕ: {source_config['name']}")
    print("="*70)
    print(f"URL: {source_config['url']}")
    print(f"Selector: {source_config.get('selector', 'Full page')}")
    print()
    
    try:
        async with async_playwright() as p:
            print("🌐 Запуск браузера...")
            browser = await p.chromium.launch(headless=False)  # headless=False для отладки
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                viewport={
                    'width': SCREENSHOT_SETTINGS['viewport_width'], 
                    'height': SCREENSHOT_SETTINGS['viewport_height']
                }
            )
            
            page = await context.new_page()
            
            # Загружаем страницу
            print(f"📥 Загрузка страницы...")
            await page.goto(source_config['url'], wait_until='domcontentloaded', timeout=30000)
            print("✅ Страница загружена")
            
            # Cookies
            await accept_cookies(page)
            
            # Ждем элемент
            wait_for = source_config.get('wait_for')
            if wait_for:
                print(f"⏳ Ожидание элемента: {wait_for}")
                try:
                    await page.wait_for_selector(wait_for, timeout=15000)
                    print("✅ Элемент найден")
                except:
                    print("⚠️ Элемент не найден за 15 сек, продолжаем")
            
            # Дополнительное ожидание
            await asyncio.sleep(SCREENSHOT_SETTINGS['wait_after_load'])
            
            # Создаем директорию если нужно
            os.makedirs('screenshots', exist_ok=True)
            
            # Делаем скриншот
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            screenshot_path = f"screenshots/{source_key}_test_{timestamp}.png"
            
            selector = source_config.get('selector')
            
            print(f"📸 Создание скриншота...")
            
            if selector:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        await element.screenshot(path=screenshot_path)
                        print(f"✅ Скриншот элемента создан")
                    else:
                        print("⚠️ Элемент не найден, создаю скриншот страницы")
                        await page.screenshot(path=screenshot_path, full_page=False)
                except Exception as e:
                    print(f"⚠️ Ошибка скриншота элемента: {e}")
                    await page.screenshot(path=screenshot_path, full_page=False)
            else:
                await page.screenshot(path=screenshot_path, full_page=False)
                print(f"✅ Скриншот страницы создан")
            
            # Оптимизируем
            print(f"🔧 Оптимизация для Telegram...")
            optimized_path = optimize_image_for_telegram(screenshot_path)
            
            print()
            print("="*70)
            print("✅ ТЕСТ ЗАВЕРШЕН УСПЕШНО!")
            print("="*70)
            print(f"Оригинал: {screenshot_path}")
            print(f"Оптимизированный: {optimized_path}")
            print()
            print(f"Telegram заголовок: {source_config['telegram_title']}")
            print(f"Telegram хэштеги: {source_config['telegram_hashtags']}")
            print()
            
            await browser.close()
            return True
            
    except Exception as e:
        print()
        print("="*70)
        print(f"❌ ОШИБКА: {e}")
        print("="*70)
        import traceback
        traceback.print_exc()
        return False


def main():
    if len(sys.argv) < 2:
        print("Использование: python test_screenshot.py <source_key>")
        print()
        print("Доступные источники:")
        for key, config in SCREENSHOT_SOURCES.items():
            status = "✅" if config.get('enabled', True) else "❌"
            print(f"  {status} {key:20} - {config['name']}")
        sys.exit(1)
    
    source_key = sys.argv[1]
    success = asyncio.run(test_screenshot(source_key))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
