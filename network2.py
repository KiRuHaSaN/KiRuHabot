import asyncio
import json
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.exceptions import (
    TelegramRetryAfter,
    TelegramForbiddenError,
    TelegramBadRequest,
    TelegramAPIError
)
from tqdm import tqdm

# Конфигурация
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
TARGET_IDS = [
    -1001234567890,  # супергруппа или канал
    -987654321,      # обычная группа
]

MESSAGE_TEXT = """📢 <b>Рассылка от бота</b>

✅ Версия с улучшенной обработкой ошибок
🔄 Автоматический повтор при flood control
📊 Подробная статистика отправки"""

# Настройки
SEND_DELAY = 0.3  # Задержка между сообщениями в секундах
LOG_FILE = "broadcast_log.json"  # Файл для сохранения логов

class BroadcastStats:
    def __init__(self):
        self.sent = 0
        self.failed = 0
        self.errors = {}
        self.start_time = None
        self.end_time = None
    
    def start(self):
        self.start_time = datetime.now()
    
    def finish(self):
        self.end_time = datetime.now()
    
    def add_success(self, chat_id):
        self.sent += 1
    
    def add_error(self, chat_id, error):
        self.failed += 1
        self.errors[chat_id] = str(error)
    
    def duration(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    def save_to_file(self):
        data = {
            "date": datetime.now().isoformat(),
            "sent": self.sent,
            "failed": self.failed,
            "errors": self.errors,
            "duration": str(self.duration())
        }
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

async def send_safe_message(bot: Bot, chat_id: int, stats: BroadcastStats):
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=MESSAGE_TEXT,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        stats.add_success(chat_id)
        print(f"✅ [{chat_id}] Успешно отправлено")
        return True
    
    except TelegramRetryAfter as e:
        wait_time = e.retry_after
        print(f"⚠️ [{chat_id}] Flood control. Ждем {wait_time} сек...")
        await asyncio.sleep(wait_time)
        return await send_safe_message(bot, chat_id, stats)  # Рекурсивный повтор
    
    except TelegramForbiddenError:
        stats.add_error(chat_id, "Бот удален/заблокирован")
        print(f"❌ [{chat_id}] Бот не имеет доступа")
        return False
    
    except TelegramBadRequest as e:
        stats.add_error(chat_id, f"Ошибка запроса: {e}")
        print(f"❌ [{chat_id}] Некорректный запрос: {e}")
        return False
    
    except TelegramAPIError as e:
        stats.add_error(chat_id, f"Ошибка API: {e}")
        print(f"❌ [{chat_id}] Ошибка Telegram API: {e}")
        return False
    
    except Exception as e:
        stats.add_error(chat_id, f"Неизвестная ошибка: {e}")
        print(f"❌ [{chat_id}] Неизвестная ошибка: {e}")
        return False

async def broadcast(bot: Bot):
    stats = BroadcastStats()
    stats.start()
    
    print(f"🚀 Начало рассылки для {len(TARGET_IDS)} чатов")
    
    for chat_id in tqdm(TARGET_IDS, desc="Рассылка"):
        await send_safe_message(bot, chat_id, stats)
        await asyncio.sleep(SEND_DELAY)  # Задержка между сообщениями
    
    stats.finish()
    
    # Вывод статистики
    print("\n📊 Итоговая статистика:")
    print(f"✅ Успешно отправлено: {stats.sent}")
    print(f"❌ Не удалось отправить: {stats.failed}")
    print(f"⏱ Общее время: {stats.duration()}")
    
    if stats.errors:
        print("\nПодробности ошибок:")
        for chat_id, error in stats.errors.items():
            print(f"  [{chat_id}]: {error}")
    
    stats.save_to_file()
    print(f"\n📝 Лог сохранен в {LOG_FILE}")

async def main():
    bot = Bot(token=BOT_TOKEN)
    try:
        # Подтверждение перед рассылкой
        confirm = input("Вы уверены, что хотите начать рассылку? (y/n): ")
        if confirm.lower() != 'y':
            print("Рассылка отменена")
            return
        
        await broadcast(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
