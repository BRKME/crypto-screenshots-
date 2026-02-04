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
from datetime import datetime, timezone, timedelta
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
    POST_SCHEDULE,  # ✅ НОВОЕ: Расписание постов
    IMAGE_SETTINGS, 
    SCREENSHOT_SETTINGS
)
import random  # ✅ НОВОЕ: Для случайного выбора источников

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
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# OpenAI Integration для AI комментариев (после logger!)
try:
    from openai_integration import get_ai_comment, add_alpha_take_to_caption
    OPENAI_ENABLED = True
    logger.info("✓ OpenAI integration loaded")
except ImportError as e:
    OPENAI_ENABLED = False
    logger.warning(f"⚠️ OpenAI integration not available: {e}")
    def get_ai_comment(*args, **kwargs):
        return None
    def add_alpha_take_to_caption(title, hashtags_fallback, *args, **kwargs):
        return f"<b>{title}</b>\n\n{hashtags_fallback}"
except Exception as e:
    OPENAI_ENABLED = False
    logger.warning(f"⚠️ OpenAI integration error: {e}")
    def get_ai_comment(*args, **kwargs):
        return None
    def add_alpha_take_to_caption(title, hashtags_fallback, *args, **kwargs):
        return f"<b>{title}</b>\n\n{hashtags_fallback}"

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


def optimize_image_for_telegram(image_path, skip_width_padding=False, crop=None):
    """Оптимизирует изображение для Telegram
    
    Args:
        image_path: Путь к изображению
        skip_width_padding: Пропустить добавление padding по ширине
        crop: Dict с параметрами обрезки {"top": N, "right": N, "bottom": N, "left": N} в пикселях
    """
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
        
        # ✅ НОВОЕ: Обрезка изображения
        if crop:
            top = crop.get('top', 0)
            right = crop.get('right', 0)
            bottom = crop.get('bottom', 0)
            left = crop.get('left', 0)
            
            width, height = img.size
            crop_box = (
                left,                    # left
                top,                     # top
                width - right,           # right
                height - bottom          # bottom
            )
            
            img = img.crop(crop_box)
            logger.info(f"  ✂️  Обрезано: {img.size[0]}x{img.size[1]} (top:{top}, right:{right}, bottom:{bottom}, left:{left})")
        
        # CRITICAL: Валидация размеров изображения
        if img.size[0] == 0 or img.size[1] == 0:
            logger.error(f"  ✗ ОШИБКА: Изображение имеет нулевые размеры: {img.size[0]}x{img.size[1]}")
            return None
        
        # Изменяем размер если больше лимита
        max_width = IMAGE_SETTINGS['telegram_max_width']
        max_height = IMAGE_SETTINGS['telegram_max_height']
        
        if img.size[0] > max_width or img.size[1] > max_height:
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            logger.info(f"  Изменен размер: {img.size[0]}x{img.size[1]}")
        
        # Добавляем padding если изображение слишком узкое (если не отключено)
        min_width = IMAGE_SETTINGS.get('telegram_min_width', 0)
        add_padding = IMAGE_SETTINGS.get('add_padding_if_narrow', False)
        
        if add_padding and not skip_width_padding and img.size[0] < min_width:
            padding_color = IMAGE_SETTINGS.get('padding_color', (255, 255, 255))
            
            # Валидация padding_color
            if not (isinstance(padding_color, tuple) and len(padding_color) == 3):
                logger.warning(f"  ⚠️ Некорректный padding_color: {padding_color}, используем белый")
                padding_color = (255, 255, 255)
            else:
                r, g, b = padding_color
                if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
                    logger.warning(f"  ⚠️ padding_color вне диапазона 0-255: {padding_color}, используем белый")
                    padding_color = (255, 255, 255)
            
            # Сохраняем исходную ширину для логирования
            original_width = img.size[0]
            
            # Создаем новое изображение с нужной шириной
            new_width = min_width
            new_height = img.size[1]
            new_img = Image.new('RGB', (new_width, new_height), padding_color)
            
            # Центрируем исходное изображение
            paste_x = (new_width - img.size[0]) // 2
            new_img.paste(img, (paste_x, 0))
            
            img = new_img
            logger.info(f"  ✓ Добавлен padding: {img.size[0]}x{img.size[1]} (было {original_width}px, padding {paste_x}px с каждой стороны)")
        
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
    success = False         # Track if operation succeeded
    
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
        base_wait = 5
        extra_wait = source_config.get('extra_wait', 0)
        total_wait = base_wait + extra_wait
        logger.info(f"⏳ Ожидание загрузки контента ({total_wait} секунд{' (+ ' + str(extra_wait) + ' extra)' if extra_wait > 0 else ''})...")
        await asyncio.sleep(total_wait)
        
        # Ждем конкретный элемент если указан
        wait_for = source_config.get('wait_for')
        if wait_for:
            try:
                await page.wait_for_selector(wait_for, timeout=15000)
                logger.info(f"✓ Элемент найден: {wait_for}")
            except Exception as e:
                logger.warning(f"⚠️ Элемент не найден за 15 сек: {wait_for}")
        
        # Специальная обработка для heatmap (coin360.com)
        if source_key == "heatmap":
            try:
                await asyncio.sleep(3)  # Дополнительная задержка для рендеринга canvas
                logger.info("✓ Heatmap: дополнительная задержка 3 сек для загрузки canvas")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось обработать heatmap: {e}")
        
        # Делаем скриншот
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        screenshot_path = os.path.join(SCREENSHOTS_DIR, f"{source_key}_{timestamp}.png")
        
        # Закрываем модальное окно если требуется
        close_modal = source_config.get('close_modal', False)
        if close_modal:
            try:
                # Метод 1: Нажать Escape
                await page.keyboard.press('Escape')
                await asyncio.sleep(0.5)
                logger.info("  ✓ Нажат Escape для закрытия модалки")
                
                # Метод 2: Клик по кнопкам закрытия
                closed = await page.evaluate("""() => {
                    // Попытка закрыть модальное окно разными способами
                    const closeSelectors = [
                        'button:has-text("Maybe Later")',  // Специально для COIN360
                        'button:has-text("Later")',
                        '[aria-label="Close"]',
                        '[data-dismiss="modal"]',
                        '.close',
                        '.modal-close',
                        'button[class*="close"]',
                        '[class*="closeButton"]',
                        'button[type="button"]',  // Любые кнопки
                        'svg[class*="close"]',    // SVG иконки закрытия
                        '[role="button"][aria-label*="close" i]'
                    ];
                    
                    for (const sel of closeSelectors) {
                        const btns = document.querySelectorAll(sel);
                        for (const btn of btns) {
                            // Проверяем что это похоже на кнопку закрытия
                            const text = btn.textContent?.toLowerCase() || '';
                            if (text.includes('close') || text.includes('later') || text.includes('×') || text.includes('✕') || !text) {
                                btn.click();
                                return true;
                            }
                        }
                    }
                    return false;
                }""")
                await asyncio.sleep(0.5)
                
                # Метод 3: Клик по backdrop (темный фон)
                await page.evaluate("""() => {
                    const backdrops = document.querySelectorAll('[class*="backdrop"], [class*="overlay"], [class*="modal-backdrop"]');
                    backdrops.forEach(el => el.click());
                }""")
                await asyncio.sleep(0.5)
                
                # Метод 4: Принудительное скрытие всех модальных элементов
                await page.evaluate("""() => {
                    // Ищем все элементы с position: fixed и высоким z-index
                    const allElements = document.querySelectorAll('*');
                    allElements.forEach(el => {
                        const style = window.getComputedStyle(el);
                        const zIndex = parseInt(style.zIndex);
                        const position = style.position;
                        
                        // Если fixed/absolute с высоким z-index - скрываем
                        if ((position === 'fixed' || position === 'absolute') && zIndex > 1000) {
                            el.style.display = 'none';
                        }
                    });
                    
                    // Также скрываем все явные модалки
                    const modals = document.querySelectorAll('[class*="modal"], [class*="Modal"], [class*="dialog"], [class*="Dialog"], [class*="popup"], [class*="Popup"]');
                    modals.forEach(el => {
                        el.style.display = 'none';
                        el.style.visibility = 'hidden';
                        el.style.opacity = '0';
                    });
                }""")
                await asyncio.sleep(1)
                
                logger.info("  ✓ Модальное окно закрыто (4 метода)")
            except Exception as e:
                logger.warning(f"  ⚠️ Не удалось закрыть модальное окно: {e}")
        
        # Скрываем ненужные элементы если указано
        hide_elements = source_config.get('hide_elements')
        if hide_elements:
            try:
                await page.evaluate("""(selector) => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        el.style.display = 'none';
                        el.style.visibility = 'hidden';
                    });
                }""", hide_elements)
                await asyncio.sleep(0.5)
                logger.info(f"  ✓ Скрыты элементы: {hide_elements}")
            except Exception as e:
                logger.warning(f"  ⚠️ Не удалось скрыть элементы: {e}")
        
        selector = source_config.get('selector')
        element_padding = source_config.get('element_padding', 0)  # Может быть int или dict
        scale = source_config.get('scale', 1.0)  # Масштаб элемента (CSS zoom)
        
        # Нормализуем element_padding в dict
        if isinstance(element_padding, (int, float)):
            padding_dict = {'top': element_padding, 'right': element_padding, 'bottom': element_padding, 'left': element_padding}
        elif isinstance(element_padding, dict):
            padding_dict = {
                'top': element_padding.get('top', 0),
                'right': element_padding.get('right', 0),
                'bottom': element_padding.get('bottom', 0),
                'left': element_padding.get('left', 0)
            }
        else:
            padding_dict = {'top': 0, 'right': 0, 'bottom': 0, 'left': 0}
        
        if selector:
            # Скриншот конкретного элемента
            try:
                element = await page.query_selector(selector)
                if element:
                    # Применяем масштабирование если нужно
                    if scale != 1.0:
                        try:
                            await page.evaluate("""(args) => {
                                const el = document.querySelector(args.selector);
                                if (el) {
                                    el.style.transform = 'scale(' + args.scale + ')';
                                    el.style.transformOrigin = 'top left';
                                }
                            }""", {"selector": selector, "scale": scale})
                            await asyncio.sleep(0.5)  # Даем время на применение стилей
                            logger.info(f"  ✓ Применен масштаб {scale}x")
                        except Exception as e:
                            logger.warning(f"  ⚠️ Не удалось применить масштаб: {e}")
                    
                    has_padding = any(v > 0 for v in padding_dict.values())
                    
                    if has_padding:
                        # Получаем bounding box элемента
                        box = await element.bounding_box()
                        if box:
                            # Учитываем масштаб при расчете размеров
                            scaled_width = box['width'] * scale
                            scaled_height = box['height'] * scale
                            
                            # Добавляем padding с учетом разных сторон
                            clip = {
                                'x': max(0, box['x'] - padding_dict['left']),
                                'y': max(0, box['y'] - padding_dict['top']),
                                'width': min(page.viewport_size['width'], scaled_width + padding_dict['left'] + padding_dict['right']),
                                'height': min(page.viewport_size['height'], scaled_height + padding_dict['top'] + padding_dict['bottom'])
                            }
                            await page.screenshot(path=screenshot_path, clip=clip)
                            logger.info(f"✓ Скриншот с padding (T:{padding_dict['top']} R:{padding_dict['right']} B:{padding_dict['bottom']} L:{padding_dict['left']}) и scale {scale}x")
                        else:
                            # Fallback: обычный скриншот элемента
                            await element.screenshot(path=screenshot_path)
                            logger.info(f"✓ Скриншот элемента сохранен: {screenshot_path}")
                    else:
                        # Обычный скриншот элемента без padding
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
        skip_width_padding = source_config.get('skip_width_padding', False)
        crop = source_config.get('crop', None)  # ✅ НОВОЕ: Получаем параметры обрезки
        optimized_path = optimize_image_for_telegram(screenshot_path, skip_width_padding=skip_width_padding, crop=crop)
        
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
        
        success = True  # Mark as successful before return
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
        # CRITICAL: Cleanup ONLY on failure (when success=False)
        if not success:
            if screenshot_path and os.path.exists(screenshot_path):
                try:
                    os.remove(screenshot_path)
                    logger.info(f"🗑️  Cleanup при ошибке: удален screenshot")
                except Exception as cleanup_error:
                    logger.warning(f"⚠️ Cleanup warning: {cleanup_error}")
            
            if optimized_path and os.path.exists(optimized_path):
                try:
                    os.remove(optimized_path)
                    logger.info(f"🗑️  Cleanup при ошибке: удален optimized")
                except Exception as cleanup_error:
                    logger.warning(f"⚠️ Cleanup warning: {cleanup_error}")


def get_source_by_schedule():
    """
    Определяет источник для публикации по расписанию MSK
    
    Returns:
        str: Ключ источника или None если не время публикации
    """
    # MSK = UTC+3
    now_utc = datetime.now(timezone.utc)
    now_msk = now_utc + timedelta(hours=3)
    
    hour_msk = now_msk.hour
    minute_msk = now_msk.minute
    current_time_msk = hour_msk + minute_msk / 60.0  # Время в виде float (например, 16.5 = 16:30)
    
    logger.info(f"\n⏰ Текущее время MSK: {hour_msk:02d}:{minute_msk:02d}")
    logger.info(f"⏰ Текущее время UTC: {now_utc.hour:02d}:{now_utc.minute:02d}")
    
    # Проходим по всем слотам расписания
    for slot_name, slot_config in POST_SCHEDULE.items():
        time_range = slot_config['time_range_msk']
        start_time, end_time = time_range
        
        # Проверяем попадание в временной диапазон
        if start_time <= current_time_msk < end_time:
            logger.info(f"📅 Слот расписания: {slot_name}")
            logger.info(f"⏰ Время слота: {int(start_time):02d}:{int((start_time % 1) * 60):02d} - {int(end_time):02d}:{int((end_time % 1) * 60):02d} MSK")
            
            sources = slot_config['sources']
            selection_type = slot_config['selection']
            
            # Случайный выбор из списка
            if selection_type == 'random':
                source_key = random.choice(sources)
                logger.info(f"🎲 Случайный выбор из {len(sources)} источников: {source_key}")
                return source_key
            
            # Фиксированный источник
            elif selection_type == 'fixed':
                source_key = sources[0]
                logger.info(f"📌 Фиксированный источник: {source_key}")
                return source_key
            
            # Условная логика (ETF Anomaly)
            elif selection_type == 'conditional':
                logger.info(f"⚠️ Условный слот: {slot_name}")
                logger.info(f"ℹ️ Пока пропускаем - аномалии проверяются вручную")
                # TODO: Реализовать проверку аномалий ETF
                return None
    
    logger.info(f"⏰ Не время для публикации (текущее время MSK: {hour_msk:02d}:{minute_msk:02d})")
    return None


async def setup_stealth_mode(page):
    """Cloudflare bypass: stealth mode + human behavior"""
    await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        window.chrome = {runtime: {}};
    """)
    
    await page.set_extra_http_headers({
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })


async def simulate_human_behavior(page):
    """Random delays and mouse movements"""
    await asyncio.sleep(random.uniform(1.5, 3.5))
    await page.mouse.move(random.randint(100, 300), random.randint(100, 300))


async def main_parser():
    """Главная функция парсера со скриншотами"""
    browser = None  # CRITICAL: Initialize before try block
    
    try:
        logger.info("="*70)
        logger.info("🚀 ЗАПУСК ПАРСЕРА СКРИНШОТОВ v2.0 - MSK SCHEDULE")
        logger.info("="*70)
        
        # ✅ НОВОЕ: Определяем источник по расписанию MSK
        source_key = get_source_by_schedule()
        
        if not source_key:
            logger.info("⏰ Сейчас не время для публикации по расписанию")
            return True  # ✅ Это не ошибка - просто не время
        
        # ✅ ЗАЩИТА ОТ ДУБЛЕЙ: Проверяем когда последний раз публиковался этот источник
        history = load_publication_history()
        last_published = history.get("last_published", {}).get(source_key)
        
        if last_published:
            try:
                last_time = datetime.fromisoformat(last_published)
                now = datetime.now(timezone.utc)
                time_since_last = (now - last_time).total_seconds() / 60  # минуты
                
                # Cooldown 30 минут - не публиковать один источник чаще
                if time_since_last < 30:
                    logger.info(f"⏸️  Источник {source_key} уже публиковался {int(time_since_last)} минут назад")
                    logger.info(f"⏸️  Cooldown: ждем еще {int(30 - time_since_last)} минут")
                    return True  # ✅ Это не ошибка - просто cooldown
            except (ValueError, TypeError) as e:
                logger.warning(f"⚠️ Невалидный формат времени в истории для {source_key}: {e}")
                logger.info(f"  Продолжаем выполнение...")
                # Продолжаем - публикуем, так как не можем определить когда была последняя публикация
        
        source_config = SCREENSHOT_SOURCES.get(source_key)
        
        if not source_config:
            raise Exception(f"Источник {source_key} не найден в конфигурации")
        
        if not source_config.get('enabled', True):
            logger.info(f"⚠️ Источник {source_key} отключен")
            return True  # ✅ Это не ошибка - источник просто отключен
        
        logger.info(f"📅 Выбранный источник: {source_config['name']}")
        
        async with async_playwright() as p:
            logger.info("🌐 Запуск браузера...")

            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--single-process',
                    '--disable-blink-features=AutomationControlled'  # ✅ Скрыть автоматизацию
                ]
            )

            # ✅ Получаем custom user-agent если задан в конфиге
            custom_ua = source_config.get('custom_user_agent')
            user_agent = custom_ua if custom_ua else 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
            
            # ✅ Получаем custom viewport если задан в конфиге
            viewport_width = source_config.get('viewport_width', SCREENSHOT_SETTINGS['viewport_width'])
            viewport_height = source_config.get('viewport_height', SCREENSHOT_SETTINGS['viewport_height'])
            
            context = await browser.new_context(
                user_agent=user_agent,
                viewport={
                    'width': viewport_width, 
                    'height': viewport_height
                },
                # ✅ Дополнительные headers для обхода блокировки
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1'
                }
            )

            # ✅ Удаляем webdriver флаги
            page = await context.new_page()
            
            # ✅ Stealth mode если включен
            if source_config.get('stealth_mode', False):
                await page.add_init_script("""
                    // Удаляем webdriver
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    
                    // Скрываем automation
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                    
                    // Chrome runtime
                    window.chrome = {
                        runtime: {}
                    };
                """)
            else:
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)
            
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
            
            # 🤖 ALPHA TAKE от OpenAI
            ai_result = None
            skip_ai = source_config.get('skip_ai', False)
            if OPENAI_ENABLED and not skip_ai:
                logger.info("\n🤖 ГЕНЕРАЦИЯ ALPHA TAKE")
                ai_result = get_ai_comment(source_key, result['screenshot_path'])
                if ai_result:
                    logger.info("  ✓ Alpha Take получен")
                else:
                    logger.info("  ⚠️ Alpha Take не получен")
            else:
                if skip_ai:
                    logger.info("  ℹ️  AI отключен для этого источника (skip_ai=True)")
                else:
                    logger.info("  ℹ️  OpenAI отключен")
            
            # Формируем финальный caption
            caption = add_alpha_take_to_caption(title_escaped, hashtags_escaped, ai_result)
            
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
            current_hour = datetime.now(timezone.utc).hour  # ✅ Добавил определение
            
            # ✅ ИСПРАВЛЕНИЕ БАГ #1: Инициализируем last_published если его нет
            if "last_published" not in history:
                history["last_published"] = {}
            
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
