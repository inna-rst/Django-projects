from django import forms
from .models import Categories, Notes


class NotesForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Categories.objects.all(),
        required=False,  # Разрешаем пустое значение
        widget=forms.Select(attrs={'class': 'form-select'}),
        label = "Выберите категорию"
    )

    class Meta:
        model = Notes
        fields = ['title', 'text', 'category', 'reminder', 'group']

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название заметки'}),
            'text': forms.Textarea(attrs={'class': 'form-control','placeholder': 'Текст заметки'}),
            'reminder': forms.DateTimeInput(attrs={'class': 'form-control','type': 'date'})
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(NotesForm, self).__init__(*args, **kwargs)

        # Если пользователь передан, ограничиваем выбор групп только теми,
        # в которых состоит пользователь
        if user:
            self.fields['group'].queryset = user.note_groups.all()
            self.fields['group'].empty_label = "Личная заметка (без группы)"

        # Добавляем CSS-классы и другие атрибуты для полей
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class NoteSearchForm(forms.Form):
    search_query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Поиск по заголовку'}),
        label="Поиск"
    )
    category = forms.ModelChoiceField(
        queryset=Categories.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Категория",
        empty_label="Все категории"
    )

    reminder_filter=forms.DateTimeField(
        required=False,
        label="Напоминания",
        widget=forms.DateTimeInput(attrs={'class': 'form-control',"type": "date"}))