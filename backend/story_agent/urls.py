from django.urls import path
from .views import health_check,StoryGenerateAPIView,StoryImageGenerateAPIView

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("story/generate/", StoryGenerateAPIView.as_view(), name="story-generate"),
    path("story/generate-images/", StoryImageGenerateAPIView.as_view(), name="story-generate-images"),
]