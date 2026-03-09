from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def health_check(request):
    return Response({
        "status": "ok",
        "message": "Creative Storyteller backend is running"
    })


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import StoryGenerateRequestSerializer,StoryImageGenerateRequestSerializer,StoryDirectorRequestSerializer
from .services import GeminiStoryService
from .models import StoryGenerationLog


class StoryGenerateAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = StoryGenerateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated = serializer.validated_data

        try:
            service = GeminiStoryService()
            story = service.generate_story(**validated)
            story_data = story.model_dump()

            log = StoryGenerationLog.objects.create(
                topic=validated["topic"],
                tone=validated.get("tone", "cinematic"),
                language=validated.get("language", "English"),
                duration=validated.get("duration", "1-2 min"),
                audience=validated.get("audience", ""),
                number_of_scenes=validated.get("number_of_scenes", 5),
                style_notes=validated.get("style_notes", ""),
                response_json=story_data,
                status="success",
            )

            return Response(
                {
                    "success": True,
                    "message": "Story generated successfully.",
                    "story_id": log.id,
                    "data": story_data,
                },
                status=status.HTTP_200_OK,
            )

        except ValueError as exc:
            StoryGenerationLog.objects.create(
                topic=validated.get("topic", ""),
                tone=validated.get("tone", "cinematic"),
                language=validated.get("language", "English"),
                duration=validated.get("duration", "1-2 min"),
                audience=validated.get("audience", ""),
                number_of_scenes=validated.get("number_of_scenes", 5),
                style_notes=validated.get("style_notes", ""),
                status="failed",
                error_message=str(exc),
            )

            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as exc:
            StoryGenerationLog.objects.create(
                topic=validated.get("topic", ""),
                tone=validated.get("tone", "cinematic"),
                language=validated.get("language", "English"),
                duration=validated.get("duration", "1-2 min"),
                audience=validated.get("audience", ""),
                number_of_scenes=validated.get("number_of_scenes", 5),
                style_notes=validated.get("style_notes", ""),
                status="failed",
                error_message=str(exc),
            )

            return Response(
                {
                    "success": False,
                    "message": "Failed to generate story.",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
from .image_services import GeminiImageService
import traceback
class StoryImageGenerateAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = StoryImageGenerateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            service = GeminiImageService()
            updated_scenes = service.generate_images_for_scenes(
                serializer.validated_data["scenes"]
            )

            return Response(
                    {
                        "success": True,
                        "message": "Scene image processing completed.",
                        "images_generated": any(s.get("image_url") for s in updated_scenes),
                        "scenes": updated_scenes,
                    },
                    status=status.HTTP_200_OK,
                )
        except Exception as exc:
            print("IMAGE GENERATION ERROR:")
            traceback.print_exc()

            return Response(
                {
                    "success": False,
                    "message": "Failed to generate scene images.",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,)
        
from .serializers import (
    StoryGenerateRequestSerializer,
    StoryImageGenerateRequestSerializer,
    StoryAudioGenerateRequestSerializer,
)
from .audio_services import GeminiTTSService

class StoryAudioGenerateAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = StoryAudioGenerateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            service = GeminiTTSService()
            updated_scenes = service.generate_audio_for_scenes(
                serializer.validated_data["scenes"]
            )

            return Response(
                {
                    "success": True,
                    "message": "Scene audio generation completed.",
                    "audio_generated": any(s.get("audio_url") for s in updated_scenes),
                    "scenes": updated_scenes,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            print("AUDIO GENERATION ERROR:")
            traceback.print_exc()

            return Response(
                {
                    "success": False,
                    "message": "Failed to generate scene audio.",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
class StoryDirectorAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = StoryDirectorRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated = serializer.validated_data

        generate_images = validated.pop("generate_images", True)
        generate_audio = validated.pop("generate_audio", True)

        try:
            story_service = GeminiStoryService()
            story = story_service.generate_story(**validated)
            story_data = story.model_dump()

            scenes = story_data.get("scenes", [])

            image_generation_error = ""
            audio_generation_error = ""

            images_generated = False
            audio_generated = False

            if generate_images and scenes:
                try:
                    image_service = GeminiImageService()
                    scenes = image_service.generate_images_for_scenes(scenes)
                    images_generated = any(scene.get("image_url") for scene in scenes)
                except Exception as exc:
                    print("DIRECTOR IMAGE GENERATION ERROR:")
                    traceback.print_exc()
                    image_generation_error = str(exc)

                    fallback_scenes = []
                    for scene in scenes:
                        updated_scene = dict(scene)
                        if not updated_scene.get("image_url"):
                            updated_scene["image_url"] = ""
                        updated_scene["image_generation_skipped"] = True
                        updated_scene["image_generation_reason"] = f"director_pipeline_error: {exc}"
                        fallback_scenes.append(updated_scene)
                    scenes = fallback_scenes

            if generate_audio and scenes:
                try:
                    audio_service = GeminiTTSService()
                    scenes = audio_service.generate_audio_for_scenes(scenes)
                    audio_generated = any(scene.get("audio_url") for scene in scenes)
                except Exception as exc:
                    print("DIRECTOR AUDIO GENERATION ERROR:")
                    traceback.print_exc()
                    audio_generation_error = str(exc)

                    fallback_scenes = []
                    for scene in scenes:
                        updated_scene = dict(scene)
                        if not updated_scene.get("audio_url"):
                            updated_scene["audio_url"] = ""
                        updated_scene["audio_generation_skipped"] = True
                        updated_scene["audio_generation_reason"] = f"director_pipeline_error: {exc}"
                        fallback_scenes.append(updated_scene)
                    scenes = fallback_scenes

            story_data["scenes"] = scenes

            log = StoryGenerationLog.objects.create(
                topic=validated["topic"],
                tone=validated.get("tone", "cinematic"),
                language=validated.get("language", "English"),
                duration=validated.get("duration", "1-2 min"),
                audience=validated.get("audience", ""),
                number_of_scenes=validated.get("number_of_scenes", 5),
                style_notes=validated.get("style_notes", ""),
                response_json=story_data,
                status="success",
                error_message=" | ".join(
                    msg for msg in [
                        f"image: {image_generation_error}" if image_generation_error else "",
                        f"audio: {audio_generation_error}" if audio_generation_error else "",
                    ] if msg
                ),
            )

            return Response(
                {
                    "success": True,
                    "message": "Director pipeline completed.",
                    "story_id": log.id,
                    "pipeline": {
                        "story_generated": True,
                        "images_requested": generate_images,
                        "audio_requested": generate_audio,
                        "images_generated": images_generated,
                        "audio_generated": audio_generated,
                        "image_generation_error": image_generation_error,
                        "audio_generation_error": audio_generation_error,
                    },
                    "data": story_data,
                },
                status=status.HTTP_200_OK,
            )

        except ValueError as exc:
            StoryGenerationLog.objects.create(
                topic=validated.get("topic", ""),
                tone=validated.get("tone", "cinematic"),
                language=validated.get("language", "English"),
                duration=validated.get("duration", "1-2 min"),
                audience=validated.get("audience", ""),
                number_of_scenes=validated.get("number_of_scenes", 5),
                style_notes=validated.get("style_notes", ""),
                status="failed",
                error_message=str(exc),
            )

            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as exc:
            StoryGenerationLog.objects.create(
                topic=validated.get("topic", ""),
                tone=validated.get("tone", "cinematic"),
                language=validated.get("language", "English"),
                duration=validated.get("duration", "1-2 min"),
                audience=validated.get("audience", ""),
                number_of_scenes=validated.get("number_of_scenes", 5),
                style_notes=validated.get("style_notes", ""),
                status="failed",
                error_message=str(exc),
            )

            return Response(
                {
                    "success": False,
                    "message": "Director pipeline failed.",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )