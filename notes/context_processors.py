from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission

def group_permissions(request):
    context = {}
    try:
        group = Group.objects.get(name='Editor')
        # Based on your screenshot, permissions seem to be in format "app_label | category | action"
        # Looking for "Notes | Заметка | Can add notes"
        context['can_group_add_notes'] = group.permissions.filter(
            content_type__app_label='Notes',
            codename='add_notes'  # Django typically uses add_modelname format
        ).exists()
    except Group.DoesNotExist:
        context['can_group_add_notes'] = False
    return context