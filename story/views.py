from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import CreateModelMixin, ListModelMixin, UpdateModelMixin, DestroyModelMixin
from .models import Story
from django.utils import timezone

from .serializers import StorySerializer, ArchiveStorySerializer, HighlightStorySerializer


class StoryView(GenericViewSet, CreateModelMixin, ListModelMixin, DestroyModelMixin):
    queryset = Story
    serializer_class = StorySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        now = timezone.now()
        following_users = User.objects.filter(userprofile__followers=self.request.user)
        Story.objects.filter(created_at__lte=now - timezone.timedelta(hours=24)).update(is_archived=True)
        queryset = Story.objects.filter(
            (Q(user=self.request.user) | Q(user__in=following_users)),
            created_at__lt=now,
            is_archived=False,
        )
        return queryset


class ArchiveStoryView(GenericViewSet, CreateModelMixin, ListModelMixin, DestroyModelMixin):
    queryset = Story
    serializer_class = ArchiveStorySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        now = timezone.now()
        Story.objects.filter(created_at__lte=now - timezone.timedelta(hours=24)).update(is_archived=True)

        queryset = Story.objects.filter(user=self.request.user, is_archived=True)
        return queryset


class HighlightStoryView(GenericViewSet, ListModelMixin, UpdateModelMixin):
    queryset = Story
    serializer_class = HighlightStorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Story.objects.filter(user=self.request.user, is_highlighted=True)

    def update(self, request, *args, **kwargs):
        story_id = self.request.data.get("story_id")
        user = request.user
        story = Story.objects.get(user=user, is_archived=True, id=story_id)
        if not story.is_highlighted:
            story.is_highlighted = True
        elif story.is_highlighted:
            story.is_highlighted = False
        story.save()
        return Response({'message': 'Stories highlighted successfully'}, status=status.HTTP_200_OK)
