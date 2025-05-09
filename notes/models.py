from django.utils import timezone
from django.db import models
from django.urls import reverse

from django.contrib.auth.models import User

# Create your models here.
class Categories(models.Model):
    title = models.CharField(max_length=100, unique=True, verbose_name="Название категории")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class Group(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название группы")
    members = models.ManyToManyField(User, related_name='note_groups', verbose_name="Участники")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"

class Notes(models.Model):
    category = models.ForeignKey(Categories, on_delete=models.SET_NULL, null=True, blank=True, related_name="notes", verbose_name="Категория")
    title = models.CharField(max_length=100, verbose_name="Заголовок")
    text  = models.TextField(verbose_name="Содержание")
    reminder = models.DateTimeField(null=True, blank=True, verbose_name="Напоминание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='notes',
                           verbose_name="Автор")
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='notes', verbose_name="Группа")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('notes:note_detail', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = "Заметка"
        verbose_name_plural = "Заметки"
        ordering = ['-created_at']