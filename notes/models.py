from django.db import models

# Create your models here.
class Categories(models.Model):
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title

class Notes(models.Model):
    category = models.ForeignKey(Categories, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    text  = models.TextField()
    reminder = models.CharField(max_length=200)

    def __str__(self):
        return self.title