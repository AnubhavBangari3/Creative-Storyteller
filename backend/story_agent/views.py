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

from .serializers import StoryGenerateRequestSerializer,StoryImageGenerateRequestSerializer
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