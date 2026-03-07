import json
from typing import List, Optional

from django.conf import settings
from pydantic import BaseModel, Field
from google import genai
from google.genai import types


class StoryScene(BaseModel):
    scene_number: int = Field(..., description="Scene order starting from 1")
    title: str = Field(..., description="Short scene title")
    narration: str = Field(..., description="Voiceover-ready narration")
    visual_prompt: str = Field(..., description="Detailed image-generation prompt")
    text_overlay: str = Field(..., description="Short on-screen text overlay for the scene")
    audio_cue: str = Field(..., description="Suggested sound design or music cue")
    image_url: str = Field(default="", description="Generated image URL for this scene, empty until image generation step")
    audio_url: str = Field(default="", description="Generated narration audio URL for this scene, empty until audio generation step")
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
   - text_overlay
   - audio_cue
   - image_url
   - audio_url
   - duration_seconds
5. visual_prompt should be rich enough for image generation.
6. narration should be usable as direct voiceover text.
7. text_overlay must be short, cinematic, and suitable for on-screen display.
8. image_url must be an empty string.
9. audio_url must be an empty string.
10. Keep scene flow coherent from beginning to end.
11. total_estimated_duration_seconds should approximately match the requested duration.
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
            parsed = response.parsed
            return self._normalize_output(parsed)

        if not getattr(response, "text", None):
            raise ValueError("Gemini returned an empty response.")

        data = json.loads(response.text)
        parsed = StoryOutput(**data)
        return self._normalize_output(parsed)

    def _normalize_output(self, output: StoryOutput) -> StoryOutput:
        """
        Ensures image_url and audio_url are always present as empty strings
        for T14, even if the model omits them.
        """
        normalized_scenes = []

        for scene in output.scenes:
            scene_data = scene.model_dump()

            if "image_url" not in scene_data or scene_data["image_url"] is None:
                scene_data["image_url"] = ""

            if "audio_url" not in scene_data or scene_data["audio_url"] is None:
                scene_data["audio_url"] = ""

            if "text_overlay" not in scene_data or not scene_data["text_overlay"]:
                scene_data["text_overlay"] = scene_data["title"]

            normalized_scenes.append(StoryScene(**scene_data))

        return StoryOutput(
            title=output.title,
            logline=output.logline,
            overall_style=output.overall_style,
            total_estimated_duration_seconds=output.total_estimated_duration_seconds,
            scenes=normalized_scenes,
        )