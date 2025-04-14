import os
import asyncio
from django.core.management.base import BaseCommand
from notes.models import Notes
from django.utils import timezone
from telegram import Bot
from asgiref.sync import sync_to_async

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

class Command(BaseCommand):
    help = 'Отправляет заметки с напоминанием в телеграм'

    def handle(self, *args, **kwargs):
        asyncio.run(self.send_notes())

    async def send_notes(self):
        now = timezone.now()

        # оборачиваем синхронный ORM-запрос
        notes = await sync_to_async(list)(
            Notes.objects.filter(reminder__lte=now, reminder__isnull=False)
        )

        bot = Bot(token=TELEGRAM_TOKEN)

        for note in notes:
            text = f"📌 <b>{note.title}</b>\n\n{note.text}"

            # отправляем сообщение
            await bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="HTML")

            # сбрасываем напоминание
            note.reminder = None
            await sync_to_async(note.save)()

