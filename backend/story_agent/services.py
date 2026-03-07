import json
from typing import List

from django.conf import settings
from pydantic import BaseModel, Field
from google import genai
from google.genai import types


class StoryScene(BaseModel):
    scene_number: int = Field(..., description="Scene order starting from 1")
    title: str = Field(..., description="Short scene title")
    narration: str = Field(..., description="Voiceover-ready narration")
    visual_prompt: str = Field(..., description="Detailed image-generation prompt")
    audio_cue: str = Field(..., description="Suggested sound design or music cue")
    duration_seconds: int = Field(..., description="Estimated scene duration in seconds")


class StoryOutput(BaseModel):
    title: str = Field(..., description="Final story title")
    logline: str = Field(..., description="One-line story summary")
    overall_style: str = Field(..., description="Creative direction summary")
    total_estimated_duration_seconds: int = Field(..., description="Estimated full duration")
    scenes: List[StoryScene]


class GeminiStoryService:
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing in .env")

        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = getattr(settings, "GEMINI_MODEL", "gemini-3-flash-preview")

    def build_prompt(
        self,
        *,
        topic: str,
        tone: str,
        language: str,
        duration: str,
        audience: str,
        number_of_scenes: int,
        style_notes: str,
    ) -> str:
        return f"""
Create a cinematic story package with these inputs:

Topic: {topic}
Tone: {tone}
Language: {language}
Target Duration: {duration}
Audience: {audience or "General audience"}
Number of Scenes: {number_of_scenes}
Style Notes: {style_notes or "None"}

Requirements:
1. Return exactly {number_of_scenes} scenes.
2. The story must be emotionally engaging, visual, and cinematic.
3. Write the narration in {language}.
4. Each scene must contain:
   - scene_number
   - title
   - narration
   - visual_prompt
   - audio_cue
   - duration_seconds
5. visual_prompt should be rich enough for image generation.
6. narration should be usable as direct voiceover text.
7. Keep scene flow coherent from beginning to end.
8. total_estimated_duration_seconds should approximately match the requested duration.
"""

    def generate_story(
        self,
        *,
        topic: str,
        tone: str,
        language: str,
        duration: str,
        audience: str = "",
        number_of_scenes: int = 5,
        style_notes: str = "",
    ) -> StoryOutput:
        system_instruction = (
            "You are a cinematic storytelling director for an AI story platform. "
            "Generate structured story scenes only. "
            "Do not return markdown. "
            "Return only schema-compliant JSON."
        )

        prompt = self.build_prompt(
            topic=topic,
            tone=tone,
            language=language,
            duration=duration,
            audience=audience,
            number_of_scenes=number_of_scenes,
            style_notes=style_notes,
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.8,
                response_mime_type="application/json",
                response_schema=StoryOutput,
            ),
        )

        if getattr(response, "parsed", None):
            return response.parsed

        if not getattr(response, "text", None):
            raise ValueError("Gemini returned an empty response.")

        data = json.loads(response.text)
        return StoryOutput(**data)