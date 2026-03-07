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