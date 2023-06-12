from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from post import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register("post", views.PostApi, basename="post")
router.register("user_followers_post", views.UserFollowersPostApi, basename="followers_post")
router.register("all_user_post", views.AllUserPostApi, basename="all_user_post")
router.register("user_likes_post", views.UserPostLikeApi, basename="user_likes_post")
router.register("saved_post", views.PostsSavedAPIView, basename="saved_post")
router.register("particular_user_post", views.PostListView, basename="particular_user_post")
router.register("particular_user_post_like", views.PostLikeView, basename="particular_user_post_like")
router.register("particular_user_post_save", views.PostSaveView, basename="particular_user_post_save")
router.register("particular_user_post_comment", views.PostCommentView, basename="particular_user_post_comment")
router.register("search_feed_post", views.SearchFeedPost, basename="search_feed_post")
router.register("create_comment", views.CreateCommentView, basename="create_comment")
urlpatterns = [
    path('', include(router.urls))

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
