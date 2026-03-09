from django.urls import path
from .views import health_check,StoryGenerateAPIView,StoryImageGenerateAPIView,StoryAudioGenerateAPIView,StoryDirectorAPIView

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("story/generate/", StoryGenerateAPIView.as_view(), name="story-generate"),
    path("story/generate-images/", StoryImageGenerateAPIView.as_view(), name="story-generate-images"),
    path("story/generate-audio/", StoryAudioGenerateAPIView.as_view(), name="story-generate-audio"),
    path("story/director/", StoryDirectorAPIView.as_view(), name="story-director"),
]