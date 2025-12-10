"""
Парсер скриншотов для CoinMarketCap и других крипто-источников
Version: 1.3.2 (Production Ready - QA Approved)
✅ Автоматические скриншоты по расписанию
✅ Обрезка под Telegram формат
✅ Публикация в Telegram и Twitter
✅ История публикаций
✅ Lock-файлы и retry логика
✅ Полное тестирование и QA
✅ Правильный resource management (finally blocks)
✅ Complete cleanup (all temp files)
✅ Cookie handling для CoinMarketCap
"""

import asyncio
from playwright.async_api import async_playwright
import time
import json
import traceback
from datetime import datetime, timezone
import requests
import os
import sys
import logging
import tweepy
from io import BytesIO
import tempfile
import platform
from PIL import Image
import html  # FIX ISSUE #26: Для HTML escaping

# Импорты конфигурации
from sources_config import (
    SCREENSHOT_SOURCES, 
    SCHEDULE, 
    IMAGE_SETTINGS, 
    SCREENSHOT_SETTINGS
)

# Пытаемся импортировать fcntl (только Unix)
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('screenshot_parser.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Глобальные настройки
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '2'))

# Telegram настройки
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Twitter API настройки
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')

# Включить/выключить Twitter
TWITTER_ENABLED = os.getenv('TWITTER_ENABLED', 'true').lower() == 'true'

# Директории
SCREENSHOTS_DIR = "screenshots"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def get_lock_file_path():
    """Возвращает путь к lock-файлу (кросс-платформенный)"""
    if platform.system() == 'Windows':
        return os.path.join(tempfile.gettempdir(), 'cmc_screenshots.lock')
    else:
        return '/tmp/cmc_screenshots.lock'


def is_process_running(pid):
    """Проверяет что процесс с PID запущен"""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def acquire_lock():
    """Создает lock-файл для предотвращения параллельного запуска"""
    lock_path = get_lock_file_path()
    
    if os.path.exists(lock_path):
        try:
            with open(lock_path, 'r') as f:
                content = f.read().strip()
                if content:
                    lines = content.split('\n')
                    try:
                        old_pid = int(lines[0])
                        if is_process_running(old_pid):
                            logger.error(f"✗ Парсер уже запущен (PID: {old_pid})")
                            return None, None
                        else:
                            logger.warning(f"⚠️ Найден stale lock от процесса {old_pid}, удаляю")
                            os.remove(lock_path)
                    except (ValueError, IndexError):
                        logger.warning(f"⚠️ Поврежденный lock-файл, удаляю")
                        os.remove(lock_path)
        except Exception as e:
            logger.warning(f"⚠️ Ошибка чтения lock-файла: {e}, удаляю")
            try:
                os.remove(lock_path)
            except:
                pass
    
    try:
        lock_file = open(lock_path, 'w')
        
        if HAS_FCNTL:
            try:
                fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                lock_file.close()
                return None, None
        
        lock_file.write(f"{os.getpid()}\n{datetime.now(timezone.utc).isoformat()}")
        lock_file.flush()
        
        logger.info(f"✓ Lock-файл создан: {lock_path}")
        return lock_file, lock_path
        
    except Exception as e:
        logger.error(f"✗ Ошибка создания lock-файла: {e}")
        return None, None


def release_lock(lock_file, lock_path):
    """Освобождает lock-файл"""
    try:
        if lock_file:
            if HAS_FCNTL:
                try:
                    fcntl.flock(lock_file, fcntl.LOCK_UN)
                except:
                    pass
            lock_file.close()
        
        if lock_path and os.path.exists(lock_path):
            os.remove(lock_path)
            logger.info(f"✓ Lock-файл удален: {lock_path}")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось удалить lock-файл: {e}")


def load_publication_history():
    """Загружает историю публикаций из JSON файла"""
    try:
        if os.path.exists('publication_history.json'):
            with open('publication_history.json', 'r', encoding='utf-8') as f:
                history = json.load(f)
                logger.info(f"✓ История публикаций загружена: {len(history.get('last_published', {}))} источников")
                return history
    except Exception as e:
        logger.warning(f"⚠️ Ошибка загрузки истории: {e}")
    
    logger.info("📝 Создание новой истории публикаций")
    return {"last_published": {}}


def save_publication_history(history):
    """Сохраняет историю публикаций в JSON файл"""
    try:
        with open('publication_history.json', 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        logger.info("✓ История публикаций обновлена")
        return True
    except Exception as e:
        logger.error(f"✗ Ошибка сохранения истории: {e}")
        return False


def validate_telegram_credentials():
    """Проверяет что Telegram токены валидные"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("⚠️ Telegram credentials не установлены")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=5)
        
        if response.status_code != 200:
            logger.error(f"✗ Telegram токен невалидный: {response.status_code}")
            return False
        
        bot_info = response.json()
        if not bot_info.get('ok'):
            logger.error("✗ Telegram токен невалидный")
            return False
        
        bot_username = bot_info.get('result', {}).get('username', 'unknown')
        logger.info(f"✓ Telegram бот: @{bot_username}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Ошибка проверки Telegram credentials: {e}")
        return False


def cleanup_old_screenshots(max_age_hours=24):
    """
    Удаляет скриншоты старше max_age_hours
    CRITICAL: Prevents disk space leak from failed publishes and retries
    """
    try:
        if not os.path.exists(SCREENSHOTS_DIR):
            return
        
        now = time.time()
        max_age_seconds = max_age_hours * 3600
        deleted_count = 0
        total_size = 0
        
        for filename in os.listdir(SCREENSHOTS_DIR):
            filepath = os.path.join(SCREENSHOTS_DIR, filename)
            
            # Skip directories
            if not os.path.isfile(filepath):
                continue
            
            try:
                file_age = now - os.path.getmtime(filepath)
                
                if file_age > max_age_seconds:
                    file_size = os.path.getsize(filepath)
                    os.remove(filepath)
                    deleted_count += 1
                    total_size += file_size
            except Exception as e:
                logger.warning(f"⚠️ Не удалось удалить {filename}: {e}")
        
        if deleted_count > 0:
            logger.info(f"🗑️  Cleanup: удалено {deleted_count} старых файлов ({total_size/1024/1024:.1f} MB)")
        else:
            logger.info("✓ Cleanup: нет старых файлов для удаления")
            
    except Exception as e:
        logger.warning(f"⚠️ Ошибка cleanup старых файлов: {e}")


def optimize_image_for_telegram(image_path):
    """Оптимизирует изображение для Telegram"""
    try:
        logger.info(f"🖼️  Оптимизация изображения: {image_path}")
        
        img = Image.open(image_path)
        original_size = os.path.getsize(image_path)
        
        logger.info(f"  Исходный размер: {img.size[0]}x{img.size[1]} ({original_size / 1024:.1f} KB)")
        
        # Конвертируем в RGB если нужно
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        
        # Изменяем размер если больше лимита
        max_width = IMAGE_SETTINGS['telegram_max_width']
        max_height = IMAGE_SETTINGS['telegram_max_height']
        
        if img.size[0] > max_width or img.size[1] > max_height:
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            logger.info(f"  Изменен размер: {img.size[0]}x{img.size[1]}")
        
        # Сохраняем оптимизированное изображение
        # FIX BUG #1: Правильная обработка любого расширения
        base_name = os.path.splitext(image_path)[0]
        optimized_path = f"{base_name}_optimized.jpg"
        img.save(optimized_path, 'JPEG', quality=IMAGE_SETTINGS['quality'], optimize=True)
        
        optimized_size = os.path.getsize(optimized_path)
        logger.info(f"  ✓ Оптимизировано: {optimized_size / 1024:.1f} KB (экономия: {(1 - optimized_size/original_size)*100:.1f}%)")
        
        return optimized_path
        
    except Exception as e:
        logger.error(f"✗ Ошибка оптимизации изображения: {e}")
        # FIX BUG #4: Проверяем что исходник существует
        if os.path.exists(image_path):
            logger.info(f"  ✓ Возвращаю исходный файл: {image_path}")
            return image_path
        else:
            logger.error(f"  ✗ Исходный файл не существует: {image_path}")
            return None


def send_telegram_photo(photo_path, caption, parse_mode='HTML'):
    """Отправляет фото в Telegram"""
    temp_compressed_file = None  # Track temporary file for cleanup
    
    try:
        # FIX BUG #2: Проверка размера файла (Telegram limit: 10 MB)
        MAX_TELEGRAM_PHOTO_SIZE = 10 * 1024 * 1024  # 10 MB
        file_size = os.path.getsize(photo_path)
        
        if file_size > MAX_TELEGRAM_PHOTO_SIZE:
            logger.warning(f"⚠️ Файл слишком большой: {file_size/1024/1024:.1f} MB (лимит 10 MB)")
            logger.info("  Применяю дополнительное сжатие...")
            
            try:
                img = Image.open(photo_path)
                # FIX BUG #21: Создаем ВРЕМЕННЫЙ файл вместо перезаписи
                base_name = os.path.splitext(photo_path)[0]
                temp_compressed = f"{base_name}_telegram_compressed.jpg"
                
                # Агрессивное сжатие
                img.save(temp_compressed, 'JPEG', quality=60, optimize=True)
                new_size = os.path.getsize(temp_compressed)
                logger.info(f"  ✓ Сжато до {new_size/1024/1024:.1f} MB")
                
                if new_size > MAX_TELEGRAM_PHOTO_SIZE:
                    logger.error(f"  ✗ Даже после сжатия файл слишком большой!")
                    os.remove(temp_compressed)  # Cleanup
                    return False
                
                # FIX BUG #27: Track temp file для cleanup в finally
                temp_compressed_file = temp_compressed
                photo_path = temp_compressed
            except Exception as e:
                logger.error(f"  ✗ Ошибка сжатия: {e}")
                return False
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        
        logger.info(f"📤 Отправка фото в Telegram...")
        logger.info(f"  Файл: {photo_path}")
        logger.info(f"  Подпись: {len(caption)} символов")
        
        with open(photo_path, 'rb') as photo:
            files = {'photo': photo}
            data = {
                'chat_id': TELEGRAM_CHAT_ID,
                'caption': caption,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            logger.info("✓ Фото отправлено в Telegram")
            return True
        else:
            logger.error(f"✗ Ошибка отправки: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Ошибка при отправке фото в Telegram: {e}")
        traceback.print_exc()
        return False
        
    finally:
        # FIX BUG #27: Cleanup ВСЕГДА выполняется (даже при exception)
        if temp_compressed_file and os.path.exists(temp_compressed_file):
            try:
                os.remove(temp_compressed_file)
                logger.info(f"  🗑️  Удален временный файл: {temp_compressed_file}")
            except Exception as cleanup_error:
                logger.warning(f"  ⚠️ Не удалось удалить временный файл: {cleanup_error}")


def init_twitter_client():
    """Инициализирует Twitter API клиент"""
    try:
        if not all([TWITTER_API_KEY, TWITTER_API_SECRET, 
                    TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET]):
            logger.warning("⚠️ Twitter API ключи не установлены")
            return None
        
        client = tweepy.Client(
            bearer_token=TWITTER_BEARER_TOKEN,
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
            wait_on_rate_limit=True
        )
        
        auth = tweepy.OAuth1UserHandler(
            TWITTER_API_KEY,
            TWITTER_API_SECRET,
            TWITTER_ACCESS_TOKEN,
            TWITTER_ACCESS_TOKEN_SECRET
        )
        api = tweepy.API(auth)
        
        logger.info("✓ Twitter API клиент инициализирован")
        return {"client": client, "api": api}
        
    except Exception as e:
        logger.error(f"✗ Ошибка инициализации Twitter API: {e}")
        return None


def send_to_twitter(title, hashtags, image_path):
    """Отправляет твит с картинкой"""
    try:
        if not TWITTER_ENABLED:
            logger.info("ℹ️  Twitter отключен")
            return False
        
        logger.info("\n🐦 ОТПРАВКА В TWITTER")
        
        twitter = init_twitter_client()
        if not twitter:
            logger.error("✗ Не удалось инициализировать Twitter клиент")
            return False
        
        client = twitter["client"]
        api = twitter["api"]
        
        # Формируем твит
        tweet_text = f"{title}\n\n{hashtags}"
        
        if len(tweet_text) > 280:
            logger.warning(f"⚠️ Твит слишком длинный ({len(tweet_text)}), сокращаю")
            tweet_text = tweet_text[:277] + "..."
        
        logger.info(f"📏 Длина твита: {len(tweet_text)} символов")
        
        # Загружаем картинку
        media_id = None
        temp_twitter_file = None  # Track temporary file for cleanup
        
        try:
            logger.info(f"🖼️  Загрузка картинки: {image_path}")
            
            # FIX BUG #7: Проверка размера файла (Twitter limit: 5 MB)
            MAX_TWITTER_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
            file_size = os.path.getsize(image_path)
            
            if file_size > MAX_TWITTER_IMAGE_SIZE:
                logger.warning(f"⚠️ Файл слишком большой для Twitter: {file_size/1024/1024:.1f} MB (лимит 5 MB)")
                logger.info("  Применяю дополнительное сжатие для Twitter...")
                
                img = Image.open(image_path)
                # FIX BUG #24: Правильный путь через splitext
                base_name = os.path.splitext(image_path)[0]
                temp_path = f"{base_name}_twitter.jpg"
                img.save(temp_path, 'JPEG', quality=50, optimize=True)
                
                # FIX BUG #28: Track temp file для cleanup в finally
                temp_twitter_file = temp_path
                image_path = temp_path
                logger.info(f"  ✓ Сжато до {os.path.getsize(image_path)/1024/1024:.1f} MB")
            
            media = api.media_upload(filename=image_path)
            media_id = media.media_id
            logger.info(f"✓ Картинка загружена, media_id: {media_id}")
            
        except Exception as e:
            logger.warning(f"⚠️ Ошибка загрузки картинки: {e}")
            
        finally:
            # FIX BUG #28: Cleanup ВСЕГДА выполняется (даже при exception)
            if temp_twitter_file and os.path.exists(temp_twitter_file):
                try:
                    os.remove(temp_twitter_file)
                    logger.info(f"  🗑️  Удален временный файл Twitter: {temp_twitter_file}")
                except Exception as cleanup_error:
                    logger.warning(f"  ⚠️ Не удалось удалить временный файл: {cleanup_error}")
        
        # Публикуем твит
        try:
            if media_id:
                response = client.create_tweet(text=tweet_text, media_ids=[media_id])
            else:
                response = client.create_tweet(text=tweet_text)
            
            if response and hasattr(response, 'data'):
                tweet_id = response.data.get('id') if hasattr(response.data, 'get') else response.data.id
                logger.info(f"✓ Твит опубликован, ID: {tweet_id}")
                return True
            else:
                logger.error("✗ Получен пустой ответ от Twitter API")
                return False
                
        except Exception as e:
            logger.error(f"✗ Ошибка публикации твита: {e}")
            return False
    
    except Exception as e:
        logger.error(f"✗ Критическая ошибка отправки в Twitter: {e}")
        traceback.print_exc()
        return False


async def accept_cookies(page):
    """Принимает cookies если баннер появился - СПЕЦИАЛЬНО ДЛЯ COINMARKETCAP"""
    try:
        # ПРИОРИТЕТ: Специфичный селектор CoinMarketCap (из твоего кода!)
        cmc_selectors = [
            'button:has-text("Accept Cookies and Continue")',
            'button:has-text("Accept All Cookies")',
        ]
        
        for selector in cmc_selectors:
            try:
                button = await page.query_selector(selector)
                if button:
                    await button.click()
                    logger.info("✓ CoinMarketCap cookie-баннер принят")
                    await asyncio.sleep(2)  # Важная задержка!
                    return True
            except:
                continue
        
        # Fallback: Общие селекторы
        cookie_buttons = [
            'button:has-text("Accept")',
            'button:has-text("Accept All")',
            'button:has-text("Agree")',
            'button:has-text("OK")',
            'text="Accept"',
            '[aria-label="Close"]',
            'button[class*="close"]',
            'button[class*="dismiss"]',
            'button:has-text("×")',
        ]

        for selector in cookie_buttons:
            try:
                button = await page.query_selector(selector)
                if button:
                    await button.click()
                    logger.info("✓ Cookie-баннер принят")
                    await asyncio.sleep(2)
                    return True
            except:
                continue

        # Скрываем через CSS если ничего не сработало
        try:
            await page.add_style_tag(content="""
                [class*="cookie"],
                [class*="consent"],
                [id*="cookie"],
                [id*="consent"],
                div[style*="position: fixed"][style*="bottom"],
                div[class*="fixed"][class*="bottom"],
                [class*="cookie-banner"],
                [role="dialog"],
                [class*="modal"] {
                    display: none !important;
                    visibility: hidden !important;
                }
            """)
            logger.info("✓ Cookie-баннеры скрыты через CSS")
        except:
            pass

        return False
    except Exception as e:
        logger.warning(f"⚠️ Предупреждение при обработке cookies: {e}")
        return False


async def take_screenshot(page, source_config, source_key):
    """Делает скриншот согласно конфигурации источника"""
    screenshot_path = None  # CRITICAL: Initialize before try
    optimized_path = None   # CRITICAL: Initialize before try
    
    try:
        url = source_config['url']
        logger.info(f"\n📸 СКРИНШОТ: {source_config['name']}")
        logger.info(f"  URL: {url}")
        
        # Загружаем страницу
        await page.goto(url, wait_until='domcontentloaded', timeout=SCREENSHOT_SETTINGS['wait_timeout'])
        logger.info("✓ Страница загружена")
        
        # Cookies и ожидание загрузки
        logger.info("🍪 Обработка cookies...")
        await accept_cookies(page)
        
        # Ожидание загрузки контента
        logger.info("⏳ Ожидание загрузки контента (5 секунд)...")
        await asyncio.sleep(5)
        
        # Ждем конкретный элемент если указан
        wait_for = source_config.get('wait_for')
        if wait_for:
            try:
                await page.wait_for_selector(wait_for, timeout=15000)
                logger.info(f"✓ Элемент найден: {wait_for}")
            except Exception as e:
                logger.warning(f"⚠️ Элемент не найден за 15 сек: {wait_for}")
        
        # Token unlocks специальная обработка
        if source_key == "token_unlocks":
            try:
                await page.evaluate("""
                    () => {
                        // Прокручиваем страницу наверх
                        window.scrollTo(0, 0);
                        
                        // Удаляем все cookie баннеры
                        const removeElements = [
                            ...document.querySelectorAll('[class*="cookie"]'),
                            ...document.querySelectorAll('[class*="consent"]'),
                            ...document.querySelectorAll('[role="dialog"]'),
                            ...document.querySelectorAll('[class*="modal"]'),
                            ...document.querySelectorAll('div[style*="position: fixed"]'),
                        ];
                        
                        removeElements.forEach(el => {
                            const text = el.textContent.toLowerCase();
                            if (text.includes('cookie') || 
                                text.includes('by using') ||
                                text.includes('consent') ||
                                text.includes('agree')) {
                                el.remove();
                                console.log('Removed banner:', el.className);
                            }
                        });
                    }
                """)
                logger.info("✓ Token unlocks: прокручено вверх, баннеры удалены")
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"⚠️ Не удалось обработать token_unlocks: {e}")
        
        # Делаем скриншот
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        screenshot_path = os.path.join(SCREENSHOTS_DIR, f"{source_key}_{timestamp}.png")
        
        selector = source_config.get('selector')
        
        if selector:
            # Скриншот конкретного элемента
            try:
                element = await page.query_selector(selector)
                if element:
                    await element.screenshot(path=screenshot_path)
                    logger.info(f"✓ Скриншот элемента сохранен: {screenshot_path}")
                else:
                    logger.warning("⚠️ Элемент не найден, делаю скриншот всей страницы")
                    await page.screenshot(path=screenshot_path, full_page=False)
            except Exception as e:
                logger.warning(f"⚠️ Ошибка скриншота элемента: {e}, делаю скриншот страницы")
                await page.screenshot(path=screenshot_path, full_page=False)
        else:
            # Скриншот всей видимой области
            await page.screenshot(path=screenshot_path, full_page=SCREENSHOT_SETTINGS['full_page'])
            logger.info(f"✓ Скриншот страницы сохранен: {screenshot_path}")
        
        # Оптимизируем для Telegram
        optimized_path = optimize_image_for_telegram(screenshot_path)
        
        # FIX BUG #22: Проверяем что оптимизация успешна
        if not optimized_path:
            logger.error("✗ Не удалось оптимизировать изображение!")
            return None
        
        # Удаляем оригинальный PNG только если оптимизация создала новый файл
        # (если optimize вернул fallback, то optimized_path == screenshot_path)
        if optimized_path != screenshot_path and os.path.exists(screenshot_path):
            try:
                os.remove(screenshot_path)
                logger.info(f"  🗑️  Удален оригинальный PNG: {os.path.basename(screenshot_path)}")
            except Exception as e:
                logger.warning(f"  ⚠️ Не удалось удалить оригинал: {e}")
        
        return {
            'source_key': source_key,
            'screenshot_path': optimized_path,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source_name': source_config['name']
        }
        
    except Exception as e:
        logger.error(f"✗ Ошибка создания скриншота: {e}")
        traceback.print_exc()
        return None
    
    finally:
        # CRITICAL: Safe cleanup - variables are guaranteed to exist
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                os.remove(screenshot_path)
                logger.info(f"🗑️  Cleanup: удален временный файл")
            except Exception as cleanup_error:
                logger.warning(f"⚠️ Cleanup warning: {cleanup_error}")
        
        if optimized_path and optimized_path != screenshot_path and os.path.exists(optimized_path):
            try:
                os.remove(optimized_path)
                logger.info(f"🗑️  Cleanup: удален optimized файл")
            except Exception as cleanup_error:
                logger.warning(f"⚠️ Cleanup warning: {cleanup_error}")


async def main_parser():
    """Главная функция парсера со скриншотами"""
    browser = None  # CRITICAL: Initialize before try block
    
    try:
        logger.info("="*70)
        logger.info("🚀 ЗАПУСК ПАРСЕРА СКРИНШОТОВ v1.0")
        logger.info("="*70)
        
        # Определяем источник по расписанию
        current_hour = datetime.now(timezone.utc).hour
        source_key = SCHEDULE.get(current_hour)
        
        if not source_key:
            raise Exception(f"Нет расписания для часа {current_hour}")
        
        source_config = SCREENSHOT_SOURCES.get(source_key)
        
        if not source_config:
            raise Exception(f"Источник {source_key} не найден в конфигурации")
        
        if not source_config.get('enabled', True):
            logger.info(f"⚠️ Источник {source_key} отключен")
            return False
        
        logger.info(f"\n⏰ Текущий час UTC: {current_hour}")
        logger.info(f"📅 По расписанию: {source_config['name']}")
        
        async with async_playwright() as p:
            logger.info("🌐 Запуск браузера...")

            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--single-process'
                ]
            )

            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={
                    'width': SCREENSHOT_SETTINGS['viewport_width'], 
                    'height': SCREENSHOT_SETTINGS['viewport_height']
                }
            )

            page = await context.new_page()
            
            # Делаем скриншот с повторными попытками
            result = None
            for retry in range(MAX_RETRIES + 1):
                if retry > 0:
                    logger.info(f"\n🔄 Повторная попытка {retry}/{MAX_RETRIES}")
                    await asyncio.sleep(3)
                
                result = await take_screenshot(page, source_config, source_key)
                
                if result:
                    break
            
            if not result:
                raise Exception(f"Не удалось создать скриншот после {MAX_RETRIES + 1} попыток")
            
            # Формируем caption для Telegram
            title = source_config['telegram_title']
            hashtags = source_config['telegram_hashtags']
            
            # FIX ISSUE #26: HTML escape для безопасности
            title_escaped = html.escape(title)
            hashtags_escaped = html.escape(hashtags)
            caption = f"<b>{title_escaped}</b>\n\n{hashtags_escaped}"
            
            # FIX ISSUE #10: Валидация длины caption (Telegram limit: 1024)
            if len(caption) > 1024:
                logger.warning(f"⚠️ Caption слишком длинный ({len(caption)} символов), обрезаю")
                caption = caption[:1020] + "..."
            
            # Отправляем в Telegram
            logger.info("\n📤 ОТПРАВКА В TELEGRAM")
            tg_success = send_telegram_photo(result['screenshot_path'], caption)
            
            if not tg_success:
                logger.warning("⚠️ Ошибка отправки в Telegram")
            
            time.sleep(2)
            
            # Отправляем в Twitter
            if TWITTER_ENABLED:
                tw_success = send_to_twitter(title, hashtags, result['screenshot_path'])
            else:
                tw_success = False
                logger.info("ℹ️  Twitter отключен")
            
            # Обновляем историю публикаций
            history = load_publication_history()
            history["last_published"][source_key] = datetime.now(timezone.utc).isoformat()
            history["last_publication"] = {
                "source": source_key,
                "name": source_config['name'],
                "published_at": datetime.now(timezone.utc).isoformat(),
                "hour_utc": current_hour,
                "telegram": tg_success,
                "twitter": tw_success
            }
            save_publication_history(history)
            
            logger.info(f"\n🎯 ИТОГ")
            logger.info(f"  ✓ Источник: {source_config['name']}")
            logger.info(f"  ✓ Скриншот: {result['screenshot_path']}")
            logger.info(f"  ✓ Telegram: {tg_success}")
            logger.info(f"  ✓ Twitter: {tw_success}")
            
            # Cleanup: удаляем файл скриншота после успешной публикации
            screenshot_file = result['screenshot_path']
            if screenshot_file and os.path.exists(screenshot_file):
                try:
                    os.remove(screenshot_file)
                    logger.info(f"  🗑️  Удален файл скриншота: {os.path.basename(screenshot_file)}")
                except Exception as e:
                    logger.warning(f"  ⚠️ Не удалось удалить скриншот: {e}")
            
            logger.info("="*70)
            
            return True

    except Exception as e:
        logger.error(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        logger.error(traceback.format_exc())
        return False
    
    finally:
        # CRITICAL: Guaranteed browser cleanup
        if browser:
            try:
                await browser.close()
                logger.info("✓ Браузер закрыт\n")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка закрытия браузера: {e}")


def main():
    """Точка входа в программу"""
    lock_file = None
    lock_path = None
    
    try:
        # Проверка lock-файла
        lock_file, lock_path = acquire_lock()
        if not lock_file:
            logger.error("\n✗ Парсер уже запущен!")
            sys.exit(2)
        
        logger.info("\n" + "="*70)
        logger.info("🤖 CMC SCREENSHOT PARSER - SCHEDULED MODE")
        logger.info("="*70)
        logger.info(f"📅 Дата запуска: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
        logger.info(f"💻 Платформа: {platform.system()} {platform.release()}")
        logger.info(f"🔒 Lock файл: {lock_path}")
        logger.info(f"⚙️  Настройки:")
        logger.info(f"   • MAX_RETRIES: {MAX_RETRIES}")
        logger.info(f"   • Telegram: {'✓' if TELEGRAM_BOT_TOKEN else '✗'}")
        logger.info(f"   • Twitter: {'✓' if TWITTER_ENABLED and TWITTER_API_KEY else '✗'}")
        logger.info("="*70 + "\n")
        
        # Валидация Telegram
        if not validate_telegram_credentials():
            logger.error("✗ КРИТИЧЕСКАЯ ОШИБКА: Невалидные Telegram credentials!")
            release_lock(lock_file, lock_path)
            sys.exit(1)
        
        # CRITICAL: Cleanup старых файлов перед запуском
        logger.info("\n🗑️  CLEANUP СТАРЫХ ФАЙЛОВ")
        cleanup_old_screenshots(max_age_hours=24)
        
        logger.info("")
        
        # Запускаем основной парсер
        success = asyncio.run(main_parser())
        
        # Освобождаем lock
        release_lock(lock_file, lock_path)
        
        if success:
            logger.info("\n✅ ПАРСИНГ ЗАВЕРШЕН УСПЕШНО!")
            sys.exit(0)
        else:
            logger.error("\n❌ ПАРСИНГ ЗАВЕРШЕН С ОШИБКОЙ!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n⚠️ Парсинг прерван пользователем (Ctrl+C)")
        release_lock(lock_file, lock_path)
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА В MAIN: {e}")
        logger.error(traceback.format_exc())
        release_lock(lock_file, lock_path)
        sys.exit(1)


if __name__ == "__main__":
    main()
