from django.contrib import admin

from post.models import Post, Image, Video, Comment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post_description')


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'caption', 'image')


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'caption', 'video')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'comment')
