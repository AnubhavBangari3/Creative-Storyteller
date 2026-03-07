from django.db import models


class StoryGenerationLog(models.Model):
    topic = models.CharField(max_length=500)
    tone = models.CharField(max_length=100, default="cinematic")
    language = models.CharField(max_length=50, default="English")
    duration = models.CharField(max_length=50, default="1-2 min")
    audience = models.CharField(max_length=200, blank=True, default="")
    number_of_scenes = models.PositiveIntegerField(default=5)
    style_notes = models.TextField(blank=True, default="")

    response_json = models.JSONField(null=True, blank=True)

    status = models.CharField(max_length=30, default="success")
    error_message = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.topic} ({self.created_at:%Y-%m-%d %H:%M})"