from django.contrib import admin
from .models import Notes, Group


@admin.register(Notes)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'group', 'created_at')
    list_filter = ('user', 'group')
    search_fields = ('title', 'text')

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name',)
    filter_horizontal = ('members',)
