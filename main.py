#!/usr/bin/env python3
"""
Crypto Radar Bot - Integrated Version
Интегрируется в проект crypto-screenshots

Функционал:
1. Crypto Market Heatmap - 2 раза в день (09:00, 21:00)
2. Cliff Unlocks - анлоки на ближайшие 7 дней (через AI анализ скриншота)
"""

import asyncio
import aiohttp
import os
import logging
from datetime import datetime
import json
import base64

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CryptoRadarBot:
    def __init__(self):
        # Telegram credentials
        self.telegram_token = os.getenv('TELEGRAM_TOKEN', '')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY', '')
        
        if not self.telegram_token or not self.chat_id:
            raise ValueError("❌ TELEGRAM_TOKEN и TELEGRAM_CHAT_ID обязательны!")
        
        if not self.anthropic_api_key:
            logger.warning("⚠️ ANTHROPIC_API_KEY не найден - Cliff Unlocks не будет работать")
        
        # URLs
        self.heatmap_url = "https://coinmarketcap.com/heatmap/"
        self.vesting_url = "https://dropstab.com/ru/vesting"
        
        # Расписание отправки (2 РАЗА В ДЕНЬ для heatmap!)
        self.heatmap_times = ['09:00', '21:00']
        self.cliff_unlocks_time = '10:00'
        
        # Трекинг последней отправки (защита от дублирования)
        self.last_heatmap_date = None
        self.last_heatmap_times = set()
        self.last_cliff_unlocks_date = None
    
    async def send_telegram_message(self, message, parse_mode='HTML'):
        """Отправляет сообщение в Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': False
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, timeout=30) as response:
                    if response.status == 200:
                        logger.info("✅ Сообщение отправлено")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Ошибка отправки: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Ошибка send_telegram_message: {e}")
            return False
    
    async def send_crypto_heatmap(self):
        """Отправляет Crypto Market Heatmap"""
        try:
            logger.info("📊 Отправка Crypto Market Heatmap...")
            
            now = datetime.now()
            current_time = now.strftime('%H:%M')
            current_date = now.strftime('%Y-%m-%d')
            
            # Проверка дублирования
            if self.last_heatmap_date == current_date and current_time in self.last_heatmap_times:
                logger.info(f"⏭️ Heatmap уже отправлен в {current_time} сегодня")
                return True
            
            message = (
                "📊 <b>CRYPTO MARKET HEATMAP</b>\n\n"
                f"🕐 {current_time} MSK\n"
                f"📅 {now.strftime('%d.%m.%Y')}\n\n"
                f"🔗 <a href='{self.heatmap_url}'>Открыть интерактивную карту</a>"
            )
            
            success = await self.send_telegram_message(message)
            
            if success:
                # Обновляем трекер
                self.last_heatmap_date = current_date
                self.last_heatmap_times.add(current_time)
                logger.info(f"✅ Heatmap отправлен в {current_time}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Ошибка send_crypto_heatmap: {e}")
            return False
    
    async def take_screenshot(self, url, wait_time=5):
        """Делает скриншот страницы через Playwright"""
        try:
            from playwright.async_api import async_playwright
            
            logger.info(f"📸 Создание скриншота {url}...")
            
            async with async_playwright() as p:
                # Запускаем браузер
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                
                # Создаём страницу
                page = await browser.new_page(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                
                # Переходим на страницу
                await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                
                # Ждём загрузки контента
                await asyncio.sleep(wait_time)
                
                # Делаем скриншот
                screenshot_bytes = await page.screenshot(full_page=True)
                
                await browser.close()
                
                logger.info(f"✅ Скриншот создан ({len(screenshot_bytes)} bytes)")
                return screenshot_bytes
                
        except ImportError:
            logger.error("❌ Playwright не установлен! Установите: pip install playwright && playwright install chromium")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка создания скриншота: {e}")
            return None
    
    async def analyze_unlocks_with_ai(self, screenshot_bytes):
        """Анализирует скриншот с unlocks через Claude API"""
        try:
            if not self.anthropic_api_key:
                logger.error("❌ ANTHROPIC_API_KEY не настроен")
                return None
            
            logger.info("🤖 Анализ скриншота через Claude AI...")
            
            # Конвертируем в base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Запрос к Claude API
            url = "https://api.anthropic.com/v1/messages"
            
            headers = {
                "x-api-key": self.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            prompt = """Проанализируй этот скриншот с сайта dropstab.com/ru/vesting.

Извлеки информацию об анлоках (token unlocks) на ближайшие 7 дней.

Для КАЖДОГО анлока выведи:
1. Название токена (например: OP, ARB, APT)
2. Сумму разлока (например: 32.21 M OP)
3. USD стоимость (например: $8.71 M)
4. Процент от капитализации (например: 1.66% от кап.)
5. Время до разлока (например: 0 дней 1 час 36 мин)

Формат вывода:
🔓 [ТОКЕН]
💰 Сумма: [количество] [тикер]
💵 Стоимость: $[сумма]
📊 От капитализации: [процент]%
⏰ Через: [время]

Если анлоков нет или их не видно - напиши "Нет данных об анлоках на ближайшие 7 дней"."""
            
            data = {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 2000,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": screenshot_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=60) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Извлекаем текст из ответа
                        if 'content' in result and len(result['content']) > 0:
                            text = result['content'][0].get('text', '')
                            logger.info("✅ AI анализ завершён")
                            return text
                        else:
                            logger.error("❌ Некорректный формат ответа от Claude")
                            return None
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Ошибка Claude API: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Ошибка analyze_unlocks_with_ai: {e}")
            return None
    
    async def send_cliff_unlocks(self):
        """Отправляет информацию о Cliff Unlocks"""
        try:
            logger.info("🔓 Отправка Cliff Unlocks...")
            
            now = datetime.now()
            current_date = now.strftime('%Y-%m-%d')
            
            # Проверка дублирования
            if self.last_cliff_unlocks_date == current_date:
                logger.info("⏭️ Cliff Unlocks уже отправлен сегодня")
                return True
            
            # Шаг 1: Делаем скриншот
            screenshot_bytes = await self.take_screenshot(self.vesting_url, wait_time=7)
            
            if not screenshot_bytes:
                logger.error("❌ Не удалось создать скриншот")
                await self.send_telegram_message(
                    "❌ <b>Cliff Unlocks</b>\n\n"
                    "Не удалось получить данные об анлоках.\n"
                    f"Проверьте вручную: {self.vesting_url}"
                )
                return False
            
            # Шаг 2: Анализируем через AI
            analysis = await self.analyze_unlocks_with_ai(screenshot_bytes)
            
            if not analysis:
                logger.error("❌ AI анализ не удался")
                await self.send_telegram_message(
                    "❌ <b>Cliff Unlocks</b>\n\n"
                    "Не удалось проанализировать данные.\n"
                    f"Проверьте вручную: {self.vesting_url}"
                )
                return False
            
            # Шаг 3: Форматируем и отправляем
            message = (
                f"🔓 <b>CLIFF UNLOCKS - Ближайшие 7 дней</b>\n\n"
                f"📅 {now.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"{analysis}\n\n"
                f"🔗 <a href='{self.vesting_url}'>Открыть Dropstab Vesting</a>"
            )
            
            success = await self.send_telegram_message(message)
            
            if success:
                self.last_cliff_unlocks_date = current_date
                logger.info("✅ Cliff Unlocks отправлен")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Ошибка send_cliff_unlocks: {e}")
            return False
    
    async def check_and_send_scheduled(self):
        """Проверяет время и отправляет сообщения по расписанию"""
        try:
            now = datetime.now()
            current_time = now.strftime('%H:%M')
            current_date = now.strftime('%Y-%m-%d')
            
            # Сброс трекера в новый день
            if self.last_heatmap_date != current_date:
                self.last_heatmap_times.clear()
                logger.info(f"🔄 Новый день: {current_date}")
            
            # Проверяем Heatmap (2 РАЗА В ДЕНЬ!)
            if current_time in self.heatmap_times:
                if current_time not in self.last_heatmap_times:
                    logger.info(f"⏰ Время для Heatmap: {current_time}")
                    await self.send_crypto_heatmap()
            
            # Проверяем Cliff Unlocks (1 раз в день)
            if current_time == self.cliff_unlocks_time:
                if self.last_cliff_unlocks_date != current_date:
                    logger.info(f"⏰ Время для Cliff Unlocks: {current_time}")
                    await self.send_cliff_unlocks()
                    
        except Exception as e:
            logger.error(f"❌ Ошибка в check_and_send_scheduled: {e}")
    
    async def run(self):
        """Основной цикл бота"""
        logger.info("🚀 Crypto Radar Bot запущен")
        logger.info(f"📊 Heatmap: {', '.join(self.heatmap_times)} (2 раза в день)")
        logger.info(f"🔓 Cliff Unlocks: {self.cliff_unlocks_time}")
        
        while True:
            try:
                # Проверяем и отправляем по расписанию
                await self.check_and_send_scheduled()
                
                # Ждём 30 секунд до следующей проверки
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"❌ Ошибка в главном цикле: {e}")
                await asyncio.sleep(60)

async def main():
    """Точка входа"""
    try:
        bot = CryptoRadarBot()
        await bot.run()
    except KeyboardInterrupt:
        logger.info("⏹️ Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
