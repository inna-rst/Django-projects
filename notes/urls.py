from django.urls import path

from . import views


app_name = 'notes'
urlpatterns = [
    path("", views.index, name="index"),
    path("note/<int:pk>/", views.NoteDetailView.as_view(), name="note_detail"),
    path('note/<int:pk>/update/', views.NoteUpdateView.as_view(), name='note_update'),
    path('note/<int:pk>/delete/', views.NoteDeleteView.as_view(), name='note_delete'),
    path("add-note/", views.AddNotesView.as_view(), name="add_note"),
]