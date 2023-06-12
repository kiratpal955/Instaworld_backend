from django.contrib import admin

from story.models import Story


# Register your models here.

@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'media', 'created_at', 'is_archived', 'is_highlighted']
