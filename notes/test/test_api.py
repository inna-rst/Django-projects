from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from notes.models import Notes, Categories
import json
import datetime


class NotesAPITest(TestCase):
    """Интеграционные тесты для API заметок"""

    def setUp(self):
        # Инициализация тестового клиента
        self.client = Client()

        # Создание тестовых категорий
        self.category1 = Categories.objects.create(title="Работа")
        self.category2 = Categories.objects.create(title="Личное")

        # Создание тестовых заметок
        self.note1 = Notes.objects.create(
            title="Первая заметка",
            text="Содержание первой заметки",
            category=self.category1
        )

        self.note2 = Notes.objects.create(
            title="Вторая заметка",
            text="Содержание второй заметки",
            category=self.category2,
            reminder=timezone.now() + datetime.timedelta(days=1)
        )

        # URL-ы для тестов
        self.list_url = reverse('notes:index')
        self.detail_url = reverse('notes:note_detail', kwargs={'pk': self.note1.pk})
        self.create_url = reverse('notes:add_note')
        self.update_url = reverse('notes:note_update', kwargs={'pk': self.note1.pk})
        self.delete_url = reverse('notes:note_delete', kwargs={'pk': self.note1.pk})

    def test_note_list_integration(self):
        """Интеграционный тест списка заметок"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Первая заметка")
        self.assertContains(response, "Вторая заметка")
        self.assertContains(response, self.category1.title)
        self.assertContains(response, self.category2.title)

    def test_note_detail_integration(self):
        """Интеграционный тест детальной информации о заметке"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Первая заметка")
        self.assertContains(response, "Содержание первой заметки")

    def test_note_create_integration(self):
        """Интеграционный тест создания заметки"""
        note_count = Notes.objects.count()
        data = {
            'title': 'Новая тестовая заметка',
            'text': 'Содержание новой тестовой заметки',
            'category': self.category1.pk
        }
        response = self.client.post(self.create_url, data)
        # Проверяем редирект после успешного создания
        self.assertEqual(response.status_code, 302)
        # Проверяем, что заметка создана
        self.assertEqual(Notes.objects.count(), note_count + 1)
        # Проверяем данные созданной заметки
        created_note = Notes.objects.get(title='Новая тестовая заметка')
        self.assertEqual(created_note.text, 'Содержание новой тестовой заметки')
        self.assertEqual(created_note.category, self.category1)

    def test_note_update_integration(self):
        """Интеграционный тест обновления заметки"""
        data = {
            'title': 'Обновленная тестовая заметка',
            'text': 'Обновленное содержание тестовой заметки',
            'category': self.category2.pk
        }
        response = self.client.post(self.update_url, data)
        # Проверяем редирект после успешного обновления
        self.assertEqual(response.status_code, 302)
        # Обновляем данные заметки
        self.note1.refresh_from_db()
        # Проверяем обновленные данные
        self.assertEqual(self.note1.title, 'Обновленная тестовая заметка')
        self.assertEqual(self.note1.text, 'Обновленное содержание тестовой заметки')
        self.assertEqual(self.note1.category, self.category2)

    def test_note_delete_integration(self):
        """Интеграционный тест удаления заметки"""
        note_count = Notes.objects.count()
        response = self.client.post(self.delete_url)
        # Проверяем редирект после успешного удаления
        self.assertEqual(response.status_code, 302)
        # Проверяем, что заметка удалена
        self.assertEqual(Notes.objects.count(), note_count - 1)

    def test_filter_by_category_integration(self):
        """Интеграционный тест фильтрации по категории"""
        response = self.client.get(f"{self.list_url}?category={self.category1.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Первая заметка")
        self.assertNotContains(response, "Вторая заметка")

    def test_search_by_title_integration(self):
        """Интеграционный тест поиска по заголовку"""
        response = self.client.get(f"{self.list_url}?search_query=Первая")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Первая заметка")
        self.assertNotContains(response, "Вторая заметка")

    def test_filter_by_reminder_integration(self):
        """Интеграционный тест фильтрации по напоминаниям"""
        future_date = (timezone.now() + datetime.timedelta(days=1)).date()
        response = self.client.get(f"{self.list_url}?reminder_filter={future_date}")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Первая заметка")
        self.assertContains(response, "Вторая заметка")

    def test_form_validation_integration(self):
        """Интеграционный тест валидации формы"""
        # Пытаемся создать заметку без заголовка
        data = {'text': 'Содержание без заголовка'}
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, 200)  # Форма не отправлена, остаемся на странице
        self.assertContains(response, "This field is required.")  # Проверяем сообщение об ошибке
        # Убеждаемся, что заметка не создана
        self.assertFalse(Notes.objects.filter(text='Содержание без заголовка').exists())