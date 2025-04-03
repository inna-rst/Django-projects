from django import forms
from .models import Categories, Notes


class NotesForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Categories.objects.all(),
        required=False,  # Разрешаем пустое значение
        widget=forms.Select(attrs={"class": "form-control"})
    )

    class Meta:
        model = Notes
        fields = ['title', 'text', 'category', 'reminder']

        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Name of notes'}),
            'text': forms.Textarea(attrs={'placeholder': 'Text of notes'}),
            'reminder': forms.DateTimeInput(attrs={'type': 'datetime-local'})
        }

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
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))