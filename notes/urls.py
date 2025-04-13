from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views
from . import async_views




app_name = 'notes'
urlpatterns = [
    path("", views.index, name="index"),
    path("note/<int:pk>/", views.NoteDetailView.as_view(), name="note_detail"),
    path('note/<int:pk>/update/', views.NoteUpdateView.as_view(), name='note_update'),
    path('note/<int:pk>/delete/', views.NoteDeleteView.as_view(), name='note_delete'),
    path("add-note/", views.AddNotesView.as_view(), name="add_note"),
    path('toggle-view/', views.toggle_view, name='toggle_view'),

    # Асинхронные представления
    path("a/", async_views.index, name="index"),
    path("anote/<int:pk>/", async_views.AsyncNoteDetailView.as_view(), name="note_detail"),
    path('anote/<int:pk>/update/', async_views.AsyncNoteUpdateView.as_view(), name='note_update'),
    path('anote/<int:pk>/delete/', async_views.AsyncNoteDeleteView.as_view(), name='note_delete'),
    path("aadd-note/", async_views.AsyncAddNotesView.as_view(), name="add_note"),
    path('atoggle-view/', async_views.toggle_view, name='toggle_view'),
]


