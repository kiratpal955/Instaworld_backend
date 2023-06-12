from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

from story import views

router = DefaultRouter()

router.register(r'story', views.StoryView, basename='story'),
router.register(r'archive', views.ArchiveStoryView, basename='archive'),
router.register(r'highlights', views.HighlightStoryView, basename='highlights'),

#

urlpatterns = [


]+router.urls


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
