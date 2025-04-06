from django.test import TestCase
from django.utils import timezone
from notes.forms import NotesForm, NoteSearchForm
from notes.models import Categories, Notes
import datetime


class NoteFormTest(TestCase):
    """Тесты для формы NoteForm"""

    def setUp(self):
        self.category = Categories.objects.create(title="Учеба")

    def test_valid_form(self):
        """Тест валидации формы с корректными данными"""
        reminder_date = timezone.now() + datetime.timedelta(days=1)
        data = {
            'title': 'Новая заметка',
            'text': 'Содержание новой заметки',
            'reminder': reminder_date,
            'category': self.category.pk
        }
        form = NotesForm(data=data)
        self.assertTrue(form.is_valid())

    def test_empty_title(self):
        """Тест валидации формы с пустым заголовком"""
        data = {
            'title': '',
            'text': 'Содержание заметки',
            'category': self.category.pk
        }

        form = NotesForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_optional_fields(self):
        """Тест валидации формы без необязательных полей"""
        data = {
            'title': 'Заметка без необязательных полей',
            'text': 'Содержание заметки'
        }
        form = NotesForm(data=data)
        self.assertTrue(form.is_valid())

    def test_future_reminder_date(self):
        """Тест валидации формы с будущей датой напоминания"""
        future_date = timezone.now() + datetime.timedelta(days=7)
        data = {
            'title': 'Заметка с будущим напоминанием',
            'text': 'Содержание заметки',
            'reminder': future_date
        }
        form = NotesForm(data=data)
        self.assertTrue(form.is_valid())


class NoteSearchFormTest(TestCase):
    """Тесты для формы NoteSearchForm"""

    def setUp(self):
        self.category = Categories.objects.create(title="Работа")

    def test_search_form_empty(self):
        """Тест формы поиска с пустыми данными"""
        form = NoteSearchForm(data={})
        self.assertTrue(form.is_valid())

    def test_search_form_with_query(self):
        """Тест формы поиска с поисковым запросом"""
        data = {'search_query': 'тестовый запрос'}
        form = NoteSearchForm(data=data)
        self.assertTrue(form.is_valid())

    def test_search_form_with_category(self):
        """Тест формы поиска с выбранной категорией"""
        data = {'category': self.category.pk}
        form = NoteSearchForm(data=data)
        self.assertTrue(form.is_valid())

    def test_search_form_with_reminder_filter(self):
        """Тест формы поиска с фильтром по напоминаниям"""
        today= timezone.now()
        data = {'reminder_filter': today}
        form = NoteSearchForm(data=data)
        self.assertTrue(form.is_valid())

    def test_search_form_with_all_filters(self):
        """Тест формы поиска со всеми фильтрами"""
        future_date = timezone.now() + datetime.timedelta(days=7)
        data = {
            'search_query': 'важно',
            'category': self.category.pk,
            'reminder_filter': future_date
        }
        form = NoteSearchForm(data=data)
        self.assertTrue(form.is_valid())