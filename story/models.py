from django.db import models
from django.contrib.auth.models import User


class Story(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    media = models.FileField(upload_to='media')
    created_at = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)
    is_highlighted = models.BooleanField(default=False)
    objects = models.Model
