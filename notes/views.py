from django.shortcuts import render, get_object_or_404
from django.core.exceptions import PermissionDenied

from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import DetailView
from django.views import View
from django.db.models import Q

from django.urls import reverse, reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, Http404

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from django.http import HttpResponseForbidden

from .models import Notes
from .forms import NotesForm, NoteSearchForm

from asgiref.sync import sync_to_async
from django.views.decorators.csrf import csrf_exempt
import json
import asyncio

# class Notes:
#     def __init__(self, note_id):
#         self.id = note_id
#         self.title="Заголовок заметки " + str(note_id)
#         self.content="Текст заметки " + str(note_id)
#
# notes_list=[]
# for i in range (1,11):
#     notes_list.append(Notes(i))

class AddNotesView(LoginRequiredMixin, CreateView):
    model = Notes
    form_class = NotesForm
    template_name = 'notes/notes_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавить новую заметку'
        # Добавляем доступные группы пользователя в контекст
        context['user_groups'] = self.request.user.note_groups.all()
        return context

    def form_valid(self, form):
        # Привязываем заметку к текущему пользователю
        form.instance.user = self.request.user
        messages.success(self.request, 'Заметка успешно создана!')
        return super().form_valid(form)

    def get_success_url(self):
        # Перенаправляем на детальную страницу заметки
        return self.object.get_absolute_url()


class NoteUpdateView(LoginRequiredMixin, UpdateView):
    model = Notes
    form_class = NotesForm
    template_name = 'notes/notes_form.html'

    def dispatch(self, request, *args, **kwargs):
        try:
            note = Notes.objects.get(pk=self.kwargs['pk'])
            if note.user != self.request.user:
                context = {
                    'message': 'У вас нет прав для редактирования этой заметки',
                    'title': 'Доступ запрещен'
                }
                return render(request, 'notes/access_denied.html', context, status=403)
            return super().dispatch(request, *args, **kwargs)
        except Notes.DoesNotExist:
            context = {
                'message': 'Заметка не найдена',
                'title': 'Ошибка'
            }
            return render(request, 'notes/access_denied.html', context, status=404)

    # def get_object(self, queryset=None):
    #     # Получаем объект заметки и проверяем, принадлежит ли он текущему пользователю
    #     obj = super().get_object(queryset)
    #     if obj.user != self.request.user:
    #         raise Http404("Заметка не найдена или не принадлежит вам.")
    #     return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактирование заметки'
        # Добавляем доступные группы пользователя в контекст
        context['user_groups'] = self.request.user.note_groups.all()
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Заметка успешно обновлена!')
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()



class NoteDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление заметки"""
    model = Notes
    template_name = 'notes/note_confirm_delete.html'
    # success_url = reverse_lazy('notes:index')

    def get_object(self, queryset=None):
        # Получаем объект заметки
        obj = get_object_or_404(Notes, pk=self.kwargs['pk'])

        # Проверяем, принадлежит ли заметка текущему пользователю
        if obj.user != self.request.user:
            # Если нет - вызываем исключение PermissionDenied
            raise PermissionDenied("У вас нет прав для удаления этой заметки")

        return obj

    def delete(self, request, *args, **kwargs):
        note = self.get_object()  # Получаем объект заметки перед удалением
        response = super().delete(request, *args, **kwargs)


    def get_success_url(self):
        title = self.object.title  # self.object доступен после удаления
        messages.success(self.request, f'Заметка "{title}" успешно удалена!')
        return reverse_lazy('notes:index')

class NoteDetailView(LoginRequiredMixin, DetailView):
    model = Notes
    template_name = 'notes/note_detail.html'
    context_object_name = 'note'

    def get_object(self, queryset=None):
        # Получаем объект заметки
        obj = get_object_or_404(Notes, pk=self.kwargs['pk'])

        # Проверяем, имеет ли пользователь доступ к заметке
        user_has_access = (
                obj.user == self.request.user or  # Автор заметки
                (obj.group and obj.group in self.request.user.note_groups.all())  # Член группы
        )

        if not user_has_access:
            raise PermissionDenied("У вас нет прав для просмотра этой заметки")

        return obj

    # def get_queryset(self):
    #     # Пользователь может видеть свои заметки или заметки групп, в которых он состоит
    #     user_groups = self.request.user.note_groups.all()
    #     return Notes.objects.filter(
    #         Q(user=self.request.user) | Q(group__in=user_groups)
    #     )

@login_required
def index(request):
    # Получаем тип отображения из сессии или по умолчанию показываем личные заметки
    view_type = request.session.get('view_type', 'personal')

    if view_type == 'personal':
        # Только личные заметки пользователя (без группы)
        notes_list = Notes.objects.filter(user=request.user, group=None)
        title = "Ваши личные заметки"
    else:
        # Заметки групп, в которых состоит пользователь
        user_groups = request.user.note_groups.all()
        notes_list = Notes.objects.filter(group__in=user_groups)
        title = "Групповые заметки"

    form = NoteSearchForm(request.GET)

    if form.is_valid():
        # Поиск по заголовку
        search_query = form.cleaned_data.get('search_query')
        if search_query:
            notes_list = notes_list.filter(title__icontains=search_query)

        # Фильтр по категории
        category = form.cleaned_data.get('category')
        if category:
            notes_list = notes_list.filter(category=category)

        reminder_filter = form.cleaned_data.get('reminder_filter')
        if reminder_filter:
            notes_list = notes_list.filter(reminder__date=reminder_filter.date())

    return render(request, "notes/notes_list.html", {
        "notes": notes_list,
        "form": form,
        "title": title,
        "view_type": view_type
    })

# Добавим новое представление для переключения между личными и групповыми заметками
@login_required
def toggle_view(request):
    # Переключение между личными и групповыми заметками
    current_view = request.session.get('view_type', 'personal')
    request.session['view_type'] = 'group' if current_view == 'personal' else 'personal'
    return redirect('notes:index')

def custom_404(request, exception):
    return render(request, '404.html', status=404)


def permission_denied_view(request, exception, template_name='403.html'):
    """Обработчик ошибки 403 - Доступ запрещен"""
    context = {'exception': exception}
    return render(request, template_name, context, status=403)

def page_not_found_view(request, exception, template_name='404.html'):
    """Обработчик ошибки 404 - Страница не найдена"""
    context = {'exception': exception}
    return render(request, template_name, context, status=404)

def server_error_view(request, template_name='500.html'):
    """Обработчик ошибки 500 - Ошибка сервера"""
    return render(request, template_name, status=500)


