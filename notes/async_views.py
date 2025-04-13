from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from asgiref.sync import sync_to_async
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from .models import Notes
from .forms import NotesForm, NoteSearchForm
from django.views.generic.base import View

get_object_or_404_async = sync_to_async(get_object_or_404, thread_sensitive=True)
render_async = sync_to_async(render, thread_sensitive=True)
redirect_async = sync_to_async(redirect, thread_sensitive=True)
messages_success_async = sync_to_async(messages.success, thread_sensitive=True)
reverse_lazy_async = sync_to_async(reverse_lazy, thread_sensitive=True)

class AsyncLoginRequiredMixin:
    @method_decorator(login_required)
    async def dispatch(self, request, *args, **kwargs):
        return await super().dispatch(request, *args, **kwargs)


class AsyncView(View):
    """Базовый класс для асинхронных представлений"""

    async def dispatch(self, request, *args, **kwargs):
        handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
        return await handler(request, *args, **kwargs)

    async def http_method_not_allowed(self, request, *args, **kwargs):
        return HttpResponseRedirect("/")


class AsyncAddNotesView(AsyncLoginRequiredMixin, AsyncView):
    template_name = 'notes/notes_form.html'

    async def get_success_url(self):
        # Используем обертку sync_to_async для reverse_lazy
        return await sync_to_async(reverse_lazy)('notes:index')

    async def get_form(self, request):
        # Оборачиваем создание формы в sync_to_async
        if request.method == 'POST':
            form_class = sync_to_async(NotesForm)
            return await form_class(request.POST)
        else:
            form_class = sync_to_async(NotesForm)
            return await form_class()

    async def get_context_data(self, form=None):
        context = {
            'form': form,
            'title': 'Добавить новую заметку'
        }

        # Получаем группы пользователя асинхронно
        @sync_to_async
        def get_user_groups():
            return list(self.request.user.note_groups.all())

        context['user_groups'] = await get_user_groups()
        return context

    async def get(self, request, *args, **kwargs):
        # Используем функцию для безопасного создания формы
        @sync_to_async
        def create_form():
            return NotesForm()

        form = await create_form()
        context = await self.get_context_data(form=form)
        return await render_async(request, self.template_name, context)

    async def post(self, request, *args, **kwargs):
        # Используем функцию для безопасного создания формы с данными
        @sync_to_async
        def create_and_process_form():
            form = NotesForm(request.POST)
            form.instance.user = request.user
            return form, form.is_valid()

        form, is_valid = await create_and_process_form()

        if is_valid:
            # Сохраняем форму асинхронно
            @sync_to_async
            def save_form():
                form.save()

            await save_form()

            # Добавляем сообщение об успехе
            await messages_success_async(request, 'Заметка успешно создана!')

            # Получаем URL для перенаправления
            success_url = await self.get_success_url()
            return HttpResponseRedirect(success_url)
        else:
            # Форма не валидна, показываем ошибки
            context = await self.get_context_data(form=form)
            return await render_async(request, self.template_name, context)


class AsyncNoteUpdateView(AsyncLoginRequiredMixin, AsyncView):
    template_name = 'notes/notes_form.html'

    async def get_object(self):
        obj = await get_object_or_404_async(Notes, pk=self.kwargs['pk'])

        # Проверяем права доступа
        @sync_to_async
        def check_permissions():
            if obj.user != self.request.user:
                raise PermissionDenied("У вас нет прав для редактирования этой заметки")

        await check_permissions()
        return obj

    async def get_form(self, obj=None):
        # Оборачиваем создание формы в sync_to_async
        @sync_to_async
        def create_form_get():
            return NotesForm(instance=obj)

        @sync_to_async
        def create_form_post(post_data):
            return NotesForm(post_data, instance=obj)

        if self.request.method == 'POST':
            return await create_form_post(self.request.POST)
        return await create_form_get()

    async def get_context_data(self, form=None):
        context = {
            'form': form,
            'title': 'Редактирование заметки'
        }

        # Получаем группы пользователя асинхронно
        @sync_to_async
        def get_user_groups():
            return list(self.request.user.note_groups.all())

        context['user_groups'] = await get_user_groups()
        return context

    async def get_success_url(self):
        return await sync_to_async(reverse_lazy)('notes:index')

    async def get(self, request, *args, **kwargs):
        # Получаем объект
        obj = await self.get_object()
        # Создаем форму с объектом
        form = await self.get_form(obj)
        # Получаем контекст
        context = await self.get_context_data(form=form)
        return await render_async(request, self.template_name, context)

    async def post(self, request, *args, **kwargs):
        # Получаем объект
        obj = await self.get_object()
        # Создаем форму с данными запроса и объектом
        form = await self.get_form(obj)

        # Проверяем форму и сохраняем если валидна
        @sync_to_async
        def validate_and_save():
            if form.is_valid():
                form.save()
                return True
            return False

        is_valid = await validate_and_save()

        if is_valid:
            # Добавляем сообщение об успехе
            await messages_success_async(request, 'Заметка успешно обновлена!')
            # Получаем URL для перенаправления
            success_url = await self.get_success_url()
            return HttpResponseRedirect(success_url)
        else:
            # Форма не валидна, показываем ошибки
            context = await self.get_context_data(form=form)
            return await render_async(request, self.template_name, context)


class AsyncNoteDeleteView(AsyncLoginRequiredMixin, AsyncView):
    template_name = 'notes/note_confirm_delete.html'

    async def get_object(self):
        obj = await get_object_or_404_async(Notes, pk=self.kwargs['pk'])

        # Проверяем права доступа
        @sync_to_async
        def check_permissions():
            if obj.user != self.request.user:
                raise PermissionDenied("У вас нет прав для удаления этой заметки")

        await check_permissions()
        return obj

    async def get_context_data(self, obj=None):
        return {
            'object': obj,
            'title': 'Удаление заметки'
        }

    async def get_success_url(self):
        return await sync_to_async(reverse_lazy)('notes:index')

    async def get(self, request, *args, **kwargs):
        obj = await self.get_object()
        context = await self.get_context_data(obj=obj)
        return await render_async(request, self.template_name, context)

    async def post(self, request, *args, **kwargs):
        obj = await self.get_object()
        title = obj.title  # Сохраняем заголовок перед удалением

        # Удаляем объект
        @sync_to_async
        def delete_object():
            obj.delete()

        await delete_object()

        # Добавляем сообщение об успехе
        await messages_success_async(request, f'Заметка "{title}" успешно удалена!')

        # Перенаправляем на страницу со списком заметок
        success_url = await self.get_success_url()
        return HttpResponseRedirect(success_url)


class AsyncNoteDetailView(AsyncLoginRequiredMixin, AsyncView):
    template_name = 'notes/note_detail.html'

    async def get_object(self):
        obj = await get_object_or_404_async(Notes, pk=self.kwargs['pk'])

        # Проверяем доступ пользователя к заметке
        @sync_to_async
        def check_access():
            user_has_access = obj.user == self.request.user

            # Проверяем принадлежность к группе
            if obj.group:
                user_groups = list(self.request.user.note_groups.all())
                group_access = obj.group in user_groups
                user_has_access = user_has_access or group_access

            if not user_has_access:
                raise PermissionDenied("У вас нет прав для просмотра этой заметки")

        await check_access()
        return obj

    async def get_context_data(self, obj=None):
        context = {
            'note': obj,  # Используем имя 'note' как в оригинальном коде
            'title': 'Просмотр заметки'
        }

        # Получаем группы пользователя асинхронно
        @sync_to_async
        def get_user_groups():
            return list(self.request.user.note_groups.all())

        context['user_groups'] = await get_user_groups()
        return context

    async def get(self, request, *args, **kwargs):
        obj = await self.get_object()
        context = await self.get_context_data(obj=obj)
        return await render_async(request, self.template_name, context)


@login_required
async def index(request):
    view_type = request.session.get('view_type', 'personal')

    @sync_to_async
    def init_form():
        return NoteSearchForm(request.GET or None)

    form = await init_form()

    @sync_to_async
    def get_notes():
        if view_type == 'personal':
            qs = Notes.objects.filter(user=request.user, group=None)
        else:
            user_groups = list(request.user.note_groups.all())
            qs = Notes.objects.filter(group__in=user_groups)

        if form.is_valid():
            if form.cleaned_data.get('search_query'):
                qs = qs.filter(title__icontains=form.cleaned_data['search_query'])
            if form.cleaned_data.get('category'):
                qs = qs.filter(category=form.cleaned_data['category'])
            if form.cleaned_data.get('reminder_filter'):
                qs = qs.filter(reminder__date=form.cleaned_data['reminder_filter'])

        return list(qs.select_related('group', 'user'))

    notes_list = await get_notes()

    return await render_async(
        request,
        "notes/notes_list.html",
        {
            "notes": notes_list,
            "form": form,
            "title": "Ваши личные заметки" if view_type == 'personal' else "Групповые заметки",
            "view_type": view_type
        }
    )

@login_required
async def toggle_view(request):
    @sync_to_async
    def toggle():
        current_view = request.session.get('view_type', 'personal')
        request.session['view_type'] = 'group' if current_view == 'personal' else 'personal'

    await toggle()
    return await redirect_async('notes:index')

def custom_404(request, exception):
    return render(request, '404.html', status=404)

def permission_denied_view(request, exception, template_name='403.html'):
    return render(request, template_name, status=403)

def page_not_found_view(request, exception, template_name='404.html'):
    return render(request, template_name, status=404)

def server_error_view(request, template_name='500.html'):
    return render(request, template_name, status=500)
