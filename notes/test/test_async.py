rom
django.test
import TestCase
from django.urls import reverse
from .models import Notes


class AsyncAddNoteTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Создаем тестовые данные
        cls.user = User.objects.create_user(username='testuser', password='12345')
        cls.note_data = {'title': 'Test Note', 'content': 'Test Content'}

    async def test_async_add_note_view(self):
        # Асинхронный клиент для тестирования
        from django.test import AsyncClient
        client = AsyncClient()

        # Логиним пользователя
        await client.force_login(self.user)

        # GET-запрос
        response = await client.get(reverse('add_note'))
        self.assertEqual(response.status_code, 200)

        # POST-запрос
        response = await client.post(reverse('add_note'), data=self.note_data)
        self.assertEqual(response.status_code, 302)  # Проверяем редирект
        self.assertEqual(response.url, reverse('notes:index'))

        # Проверяем создание заметки
        note_count = await Notes.objects.acount()
        self.assertEqual(note_count, 1)