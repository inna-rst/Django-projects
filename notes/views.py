from django.shortcuts import render
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import DetailView
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.views import View


from .models import Notes
from .forms import NotesForm, NoteSearchForm

# class Notes:
#     def __init__(self, note_id):
#         self.id = note_id
#         self.title="Заголовок заметки " + str(note_id)
#         self.content="Текст заметки " + str(note_id)
#
# notes_list=[]
# for i in range (1,11):
#     notes_list.append(Notes(i))

class AddNotesView(CreateView):
    model = Notes
    form_class = NotesForm
    template_name = 'notes/notes_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Заметка успешно создана!')
        return super().form_valid(form)

    def get_success_url(self):
        # Перенаправляем на детальную страницу заметки
        return self.object.get_absolute_url()


class NoteUpdateView(UpdateView):
    model = Notes
    form_class = NotesForm
    template_name = 'notes/notes_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактирование заметки'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Заметка успешно обновлена!')
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()


class NoteDeleteView(DeleteView):
    """Удаление заметки"""
    model = Notes
    template_name = 'notes/note_confirm_delete.html'
    # success_url = reverse_lazy('notes:index')

    def delete(self, request, *args, **kwargs):
        note = self.get_object()  # Получаем объект заметки перед удалением
        response = super().delete(request, *args, **kwargs)


    def get_success_url(self):
        title = self.object.title  # self.object доступен после удаления
        messages.success(self.request, f'Заметка "{title}" успешно удалена!')
        return reverse_lazy('notes:index')

class NoteDetailView(DetailView):
    model = Notes
    template_name = 'notes/note_detail.html'
    context_object_name = 'note'

def index(request):
    notes_list=Notes.objects.all()

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
            notes_list = notes_list.filter(reminder__date=reminder_filter)


    return render(request, "notes/notes_list.html", {"notes": notes_list, "form": form})
