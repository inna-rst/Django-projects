from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.http import Http404
from asgiref.sync import sync_to_async
from django.db.models import Q

from .models import Notes
from .forms import NotesForm, NoteSearchForm

# Хелперные функции для работы с моделями асинхронно
get_object_or_404_async = sync_to_async(get_object_or_404)
render_async = sync_to_async(render)
redirect_async = sync_to_async(redirect)
messages_success_async = sync_to_async(messages.success)


# Асинхронный миксин для проверки авторизации
class AsyncLoginRequiredMixin:
    @method_decorator(login_required)
    async def dispatch(self, request, *args, **kwargs):
        return await sync_to_async(super().dispatch)(request, *args, **kwargs)


class AsyncAddNotesView(AsyncLoginRequiredMixin, CreateView):
    model = Notes
    form_class = NotesForm
    template_name = 'notes/notes_form.html'
    success_url = reverse_lazy('notes:index')  # Добавлен success_url

    async def get_context_data(self, **kwargs):
        # Получаем базовый контекст асинхронно
        sync_get_context = sync_to_async(super().get_context_data)
        context = await sync_get_context(**kwargs)

        # Асинхронно получаем группы пользователя
        user_groups = await sync_to_async(list)(self.request.user.note_groups.all())

        context.update({
            'title': 'Добавить новую заметку',
            'user_groups': user_groups
        })
        return context

    async def form_valid(self, form):
        # Привязываем заметку к текущему пользователю
        form.instance.user = self.request.user

        # Асинхронно сохраняем форму
        await sync_to_async(form.save)()

        # Асинхронное сообщение об успехе
        await messages_success_async(self.request, 'Заметка успешно создана!')

        # Перенаправляем на success_url
        return HttpResponseRedirect(self.get_success_url())


class AsyncNoteUpdateView(AsyncLoginRequiredMixin, UpdateView):
    model = Notes
    form_class = NotesForm
    template_name = 'notes/notes_form.html'

    async def dispatch(self, request, *args, **kwargs):
        try:
            # Получаем заметку асинхронно
            note = await sync_to_async(Notes.objects.get)(pk=self.kwargs['pk'])
            if note.user != self.request.user:
                context = {
                    'message': 'У вас нет прав для редактирования этой заметки',
                    'title': 'Доступ запрещен'
                }
                return await render_async(request, 'notes/access_denied.html', context, status=403)
            return await sync_to_async(super().dispatch)(request, *args, **kwargs)
        except Notes.DoesNotExist:
            context = {
                'message': 'Заметка не найдена',
                'title': 'Ошибка'
            }
            return await render_async(request, 'notes/access_denied.html', context, status=404)

    @sync_to_async
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактирование заметки'
        # Добавляем доступные группы пользователя в контекст
        context['user_groups'] = self.request.user.note_groups.all()
        return context


    async def form_valid(self, form):
        await messages_success_async(self.request, 'Заметка успешно обновлена!')
        return super().form_valid(form)

    @sync_to_async
    def get_success_url(self):
        return self.object.get_absolute_url()


class AsyncNoteDeleteView(AsyncLoginRequiredMixin, DeleteView):
    """Асинхронное удаление заметки"""
    model = Notes
    template_name = 'notes/note_confirm_delete.html'

    async def get_object(self, queryset=None):  # Добавлен async
        obj = await get_object_or_404_async(Notes, pk=self.kwargs['pk'])

        if obj.user != self.request.user:
            raise PermissionDenied("У вас нет прав для удаления этой заметки")

        return obj

    async def delete(self, request, *args, **kwargs):  # Добавлен async
        self.object = await self.get_object()
        await sync_to_async(self.object.delete)()

        await messages_success_async(
            self.request,
            f'Заметка "{self.object.title}" успешно удалена!'
        )

        return HttpResponseRedirect(await sync_to_async(reverse_lazy)('notes:index'))

    # Асинхронная версия get_success_url
    async def get_success_url(self):
        return await sync_to_async(reverse_lazy)('notes:index')

class AsyncNoteDetailView(AsyncLoginRequiredMixin, DetailView):
    model = Notes
    template_name = 'notes/note_detail.html'
    context_object_name = 'note'


    async def get_object(self, queryset=None):
        # Получаем объект заметки асинхронно
        obj = await get_object_or_404_async(Notes, pk=self.kwargs['pk'])

        # Проверяем, имеет ли пользователь доступ к заметке
        user = self.request.user
        user_groups = await sync_to_async(lambda: list(user.note_groups.all()))()

        user_has_access = (
            obj.user == user or
            (obj.group and obj.group in user_groups)
        )

        if not user_has_access:
            raise PermissionDenied("У вас нет прав для просмотра этой заметки")

        return obj


# Асинхронное представление для главной страницы
@login_required
async def index(request):
    # Получаем тип отображения из сессии или по умолчанию показываем личные заметки
    view_type = request.session.get('view_type', 'personal')

    # Используем функцию для асинхронной работы с QuerySet
    async def get_notes():
        if view_type == 'personal':
            # Только личные заметки пользователя (без группы)
            return await sync_to_async(list)(Notes.objects.filter(user=request.user, group=None))
        else:
            # Заметки групп, в которых состоит пользователь
            user_groups = await sync_to_async(list)(request.user.note_groups.all())
            return await sync_to_async(list)(Notes.objects.filter(group__in=user_groups))

    title = "Ваши личные заметки" if view_type == 'personal' else "Групповые заметки"
    notes_list = await get_notes()

    # Обработка формы поиска
    form = NoteSearchForm(request.GET)

    if form.is_valid():
        # Фильтрация результатов
        search_query = form.cleaned_data.get('search_query')
        category = form.cleaned_data.get('category')
        reminder_filter = form.cleaned_data.get('reminder_filter')

        # Фильтруем заметки на стороне Python (так как мы уже получили списки асинхронно)
        if search_query:
            notes_list = [note for note in notes_list if search_query.lower() in note.title.lower()]

        if category:
            notes_list = [note for note in notes_list if note.category == category]

        if reminder_filter:
            notes_list = [note for note in notes_list if
                          note.reminder and note.reminder.date() == reminder_filter.date()]

    return await render_async(
        request,
        "notes/notes_list.html",
        {
            "notes": notes_list,
            "form": form,
            "title": title,
            "view_type": view_type
        }
    )


# Асинхронное представление для переключения между личными и групповыми заметками
@login_required
async def toggle_view(request):
    # Переключение между личными и групповыми заметками
    current_view = request.session.get('view_type', 'personal')
    request.session['view_type'] = 'group' if current_view == 'personal' else 'personal'
    return await redirect_async('notes:index')


# Обработчики ошибок
async def custom_404(request, exception):
    return await render_async(request, '404.html', status=404)


async def permission_denied_view(request, exception, template_name='403.html'):
    """Обработчик ошибки 403 - Доступ запрещен"""
    context = {'exception': exception}
    return await render_async(request, template_name, context, status=403)


async def page_not_found_view(request, exception, template_name='404.html'):
    """Обработчик ошибки 404 - Страница не найдена"""
    context = {'exception': exception}
    return await render_async(request, template_name, context, status=404)


async def server_error_view(request, template_name='500.html'):
    """Обработчик ошибки 500 - Ошибка сервера"""
    return await render_async(request, template_name, status=500)

