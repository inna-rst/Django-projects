from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from notes.models import Notes, Categories
import datetime


class CategoriesModelTest(TestCase):
    """Тесты для модели Category"""

    def setUp(self):
        self.category = Categories.objects.create(title="Работа")

    def test_category_creation(self):
        """Тест создания категории"""
        self.assertEqual(self.category.title, "Работа")
        self.assertTrue(isinstance(self.category, Categories))
        self.assertEqual(str(self.category), "Работа")

    def test_category_unique_name(self):
        """Тест уникальности имени категории"""
        with self.assertRaises(Exception):
            Categories.objects.create(title="Работа")


class NotesModelTest(TestCase):
    """Тесты для модели Note"""

    def setUp(self):
        self.category = Categories.objects.create(title="Личное")
        self.note = Notes.objects.create(
            title="Тестовая заметка",
            text="Содержание тестовой заметки",
            reminder=timezone.now() + datetime.timedelta(days=1),
            category=self.category
        )

    def test_note_creation(self):
        """Тест создания заметки"""
        self.assertEqual(self.note.title, "Тестовая заметка")
        self.assertEqual(self.note.text, "Содержание тестовой заметки")
        self.assertTrue(isinstance(self.note, Notes))
        self.assertEqual(str(self.note), "Тестовая заметка")
        self.assertEqual(self.note.category, self.category)

    def test_note_ordering(self):
        """Тест сортировки заметок по дате создания (от новых к старым)"""
        older_note = Notes(
            title="Старая заметка",
            text="Содержание старой заметки"
        )
        older_note.created_at = timezone.now() - timedelta(days=1)
        older_note.save()

        notes = Notes.objects.all()
        self.assertEqual(notes[0], self.note)  # Новая заметка должна быть первой
        self.assertEqual(notes[1], older_note)

    def test_get_absolute_url(self):
        """Тест метода get_absolute_url"""
        self.assertEqual(
            self.note.get_absolute_url(),
            reverse('notes:note_detail', kwargs={'pk': self.note.pk})
        )

    def test_note_without_category(self):
        """Тест создания заметки без категории"""
        note_without_category = Notes.objects.create(
            title="Заметка без категории",
            text="Содержание заметки без категории"
        )
        self.assertIsNone(note_without_category.category)

    def test_note_without_reminder(self):
        """Тест создания заметки без напоминания"""
        note_without_reminder = Notes.objects.create(
            title="Заметка без напоминания",
            text="Содержание заметки без напоминания"
        )
        self.assertIsNone(note_without_reminder.reminder)