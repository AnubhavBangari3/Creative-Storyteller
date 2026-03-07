from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIClient


class StoryGenerateAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_story_generate_validation(self):
        response = self.client.post(
            "/api/story/generate/",
            data={},
            format="json"
        )
        self.assertEqual(response.status_code, 400)

    @patch("story_agent.views.GeminiStoryService.generate_story")
    def test_story_generate_scene_structure(self, mock_generate_story):
        mock_generate_story.return_value = type(
            "MockStoryOutput",
            (),
            {
                "model_dump": lambda self: {
                    "title": "Echoes of Aethelgard",
                    "logline": "A journey into the ruins beneath the ocean.",
                    "overall_style": "Epic cinematic underwater fantasy",
                    "total_estimated_duration_seconds": 100,
                    "scenes": [
                        {
                            "scene_number": 1,
                            "title": "The Surface Horizon",
                            "narration": "Beyond the reach of the sun...",
                            "visual_prompt": "Cinematic wide shot of a deep blue ocean at sunset...",
                            "text_overlay": "Beyond the reach of the sun",
                            "audio_cue": "Muffled sound of crashing waves...",
                            "image_url": "",
                            "audio_url": "",
                            "duration_seconds": 15,
                        }
                    ],
                }
            },
        )()

        payload = {
            "topic": "A lost kingdom hidden under the ocean",
            "tone": "cinematic",
            "language": "English",
            "duration": "1-2 min",
            "audience": "General audience",
            "number_of_scenes": 5,
            "style_notes": "epic, mysterious, emotional",
        }

        response = self.client.post(
            "/api/story/generate/",
            data=payload,
            format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])

        scene = response.data["data"]["scenes"][0]

        self.assertIn("scene_number", scene)
        self.assertIn("title", scene)
        self.assertIn("narration", scene)
        self.assertIn("visual_prompt", scene)
        self.assertIn("text_overlay", scene)
        self.assertIn("audio_cue", scene)
        self.assertIn("image_url", scene)
        self.assertIn("audio_url", scene)
        self.assertIn("duration_seconds", scene)