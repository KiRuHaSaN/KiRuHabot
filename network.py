import asyncio
from aiogram import Bot, Dispatcher

# Токен бота, полученный у @BotFather
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# Список ID чатов и групп для рассылки
TARGET_IDS = [
    -1001234567890,  # супергруппа или канал
    -987654321,      # обычная группа
]

MESSAGE_TEXT = "📢 Привет! Это рассылка от бота на Aiogram 3."

async def broadcast(bot: Bot):
    sent = 0
    failed = 0

    for chat_id in TARGET_IDS:
        try:
            await bot.send_message(chat_id, MESSAGE_TEXT)
            print(f"✅ Отправлено в {chat_id}")
            sent += 1
        except Exception as e:
            print(f"❌ Ошибка при отправке в {chat_id}: {e}")
            failed += 1

    print(f"\nРассылка завершена: отправлено {sent}, ошибок {failed}")

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    await broadcast(bot)

    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
