from rest_framework import serializers


class StoryGenerateRequestSerializer(serializers.Serializer):
    topic = serializers.CharField(max_length=500)
    tone = serializers.CharField(max_length=100, default="cinematic")
    language = serializers.CharField(max_length=50, default="English")
    duration = serializers.CharField(max_length=50, default="1-2 min")
    audience = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        default=""
    )
    number_of_scenes = serializers.IntegerField(
        required=False,
        min_value=3,
        max_value=12,
        default=5
    )
    style_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default=""
    )
class StoryImageGenerateRequestSerializer(serializers.Serializer):
    scenes = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )

class StoryAudioGenerateRequestSerializer(serializers.Serializer):
    scenes = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )