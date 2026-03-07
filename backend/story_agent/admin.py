from django.contrib import admin
from .models import StoryGenerationLog


@admin.register(StoryGenerationLog)
class StoryGenerationLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "topic",
        "tone",
        "language",
        "number_of_scenes",
        "status",
        "created_at",
    )
    search_fields = ("topic", "tone", "language", "audience")
    list_filter = ("status", "tone", "language", "created_at")
    readonly_fields = ("created_at",)