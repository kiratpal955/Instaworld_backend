from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, CreateModelMixin, UpdateModelMixin, \
    DestroyModelMixin, RetrieveModelMixin
from rest_framework_simplejwt.tokens import RefreshToken
from post.models import Post, Comment
from post.serializers import PostSerializers, UserFollowersPostSerializer, PostSavedSerializer, PostListSerializer, \
    PostLikeSerializer, PostSaveSerializer, PostCommentSerializer, CreateCommentSerializer, SearchFeedPostSerializer


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class PostApi(GenericViewSet, ListModelMixin, CreateModelMixin, UpdateModelMixin,
              DestroyModelMixin, RetrieveModelMixin):
    serializer_class = PostSerializers
    queryset = Post.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        queryset = Post.objects.filter(user=user)
        post_id = self.request.query_params.get('post_id')
        if post_id:
            queryset = Post.objects.filter(pk=post_id)
        return queryset


class AllUserPostApi(GenericViewSet, ListModelMixin):
    serializer_class = PostSerializers
    queryset = Post.objects.all()
    permission_classes = [IsAuthenticated]


class UserFollowersPostApi(GenericViewSet, ListModelMixin, CreateModelMixin, UpdateModelMixin,
                           DestroyModelMixin, RetrieveModelMixin):
    serializer_class = UserFollowersPostSerializer
    permission_classes = [IsAuthenticated]
    queryset = Post.objects.all()

    def get_queryset(self):
        posts = self.request.user.userprofile.followers.all()
        return Post.objects.filter(user__in=posts).order_by('?')


class UserPostLikeApi(GenericViewSet, ListModelMixin, CreateModelMixin, UpdateModelMixin,
                      DestroyModelMixin, RetrieveModelMixin):
    serializer_class = PostSerializers
    permission_classes = [IsAuthenticated]
    queryset = Post

    def get_queryset(self):
        user = self.request.user
        return user.users_likes.all()


class PostsSavedAPIView(GenericViewSet, ListModelMixin, CreateModelMixin, UpdateModelMixin,
                        DestroyModelMixin, RetrieveModelMixin):
    serializer_class = PostSavedSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return user.saved_posts.all()


class PostListView(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = PostListSerializer
    queryset = Post.objects.all()

    def list(self, request, *args, **kwargs):
        user = self.request.query_params.get('user_id')
        print(user)
        serializer = PostListSerializer(Post.objects.filter(user__id=user), many=True)
        return Response(serializer.data)


class PostLikeView(GenericViewSet, ListModelMixin, RetrieveModelMixin, CreateModelMixin):
    serializer_class = PostLikeSerializer
    queryset = Post.objects.all()
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        user = self.request.query_params.get('user_id')
        serializer = PostLikeSerializer(Post.objects.filter(likes=user), many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        user = self.request.user
        post = self.request.POST["post"]
        post = Post.objects.get(id=post)
        if user in post.likes.all():
            post.likes.remove(user)
            serializer = PostLikeSerializer(post)
            return Response(serializer.data)
        else:
            post.likes.add(user)
            serializer = PostLikeSerializer(post)
            response_data = serializer.data
            return Response(response_data)


class PostSaveView(GenericViewSet, ListModelMixin, RetrieveModelMixin, CreateModelMixin):
    serializer_class = PostSaveSerializer
    queryset = Post.objects.all()

    def list(self, request, *args, **kwargs):
        user = self.request.query_params.get('user_id')
        serializer = PostSaveSerializer(Post.objects.filter(saved_by__id=user), many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        user = self.request.user
        post = self.request.POST["post"]
        post = Post.objects.get(id=post)
        if user in post.saved_by.all():
            post.saved_by.remove(user)
            return Response(False)
        else:
            post.saved_by.add(user)
            return Response(True)


class PostCommentView(GenericViewSet, ListModelMixin, RetrieveModelMixin, CreateModelMixin):
    serializer_class = PostCommentSerializer
    queryset = Post.objects.all()

    def list(self, request, *args, **kwargs):
        id = self.request.query_params.get('post_id')
        serializers = PostCommentSerializer(Post.objects.filter(id=id), many=True)
        return Response(serializers.data)


class SearchFeedPost(GenericViewSet, ListModelMixin):
    serializer_class = SearchFeedPostSerializer
    queryset = Post

    def get_queryset(self):
        followers = self.request.user.userprofile.followers.all()
        users_to_exclude = [follower for follower in followers]
        return Post.objects.exclude(user__in=users_to_exclude).order_by("?")


class CreateCommentView(GenericViewSet, CreateModelMixin):
    serializer_class = CreateCommentSerializer
    queryset = Comment.objects.all()
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        comment = self.request.POST["comment"]
        user = self.request.user
        post = self.request.POST["post"]
        post = Post.objects.get(id=post)
        create_comment = Comment.objects.create(user=user, comment=comment)
        post.comments.add(create_comment)
        post.save()
        return Response(CreateCommentSerializer(create_comment).data)
