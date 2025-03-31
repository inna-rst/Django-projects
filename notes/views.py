from django.shortcuts import render
from .models import Notes

# class Notes:
#     def __init__(self, note_id):
#         self.id = note_id
#         self.title="Заголовок заметки " + str(note_id)
#         self.content="Текст заметки " + str(note_id)
#
# notes_list=[]
# for i in range (1,11):
#     notes_list.append(Notes(i))

def index(request):
    notes_list=Notes.objects.all()
    return render(request, "notes/notes_list.html", {"notes": notes_list})
