import os
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

from django.conf import settings

try:
    from google.cloud import texttospeech
except Exception:
    texttospeech = None


class GeminiTTSService:
    def __init__(self):
        self.provider = getattr(settings, "TTS_PROVIDER", "browser").lower()
        self.language_code = getattr(settings, "TTS_LANGUAGE_CODE", "en-US")
        self.voice_name = getattr(settings, "TTS_VOICE_NAME", "en-US-Neural2-F")
        self.audio_encoding = getattr(settings, "TTS_AUDIO_ENCODING", "MP3")

        self.output_dir = Path(settings.MEDIA_ROOT) / "generated_audio"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.client: Optional[object] = None

        if self.provider == "gcp":
            creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
            if not creds_path:
                raise ValueError(
                    "Google TTS is enabled but GOOGLE_APPLICATION_CREDENTIALS is not set."
                )
            if not os.path.exists(creds_path):
                raise ValueError(
                    f"Google TTS credentials file not found: {creds_path}"
                )
            if texttospeech is None:
                raise ValueError("google-cloud-texttospeech package is not available.")
            self.client = texttospeech.TextToSpeechClient()

    def _get_audio_encoding(self):
        encoding = self.audio_encoding.upper()

        if encoding == "MP3":
            return texttospeech.AudioEncoding.MP3
        if encoding == "LINEAR16":
            return texttospeech.AudioEncoding.LINEAR16
        if encoding == "OGG_OPUS":
            return texttospeech.AudioEncoding.OGG_OPUS

        return texttospeech.AudioEncoding.MP3

    def _save_audio_bytes(self, audio_bytes: bytes, extension: str = ".mp3") -> str:
        filename = f"{uuid.uuid4().hex}{extension}"
        filepath = self.output_dir / filename

        with open(filepath, "wb") as f:
            f.write(audio_bytes)

        return f"{settings.MEDIA_URL}generated_audio/{filename}"

    def generate_audio_from_text(self, text: str) -> str:
        if self.provider == "browser":
            raise ValueError("browser_tts_selected")

        if self.provider != "gcp":
            raise ValueError(f"unsupported_tts_provider: {self.provider}")

        synthesis_input = texttospeech.SynthesisInput(text=text)

        voice = texttospeech.VoiceSelectionParams(
            language_code=self.language_code,
            name=self.voice_name,
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=self._get_audio_encoding()
        )

        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
        )

        extension = ".mp3" if self.audio_encoding.upper() == "MP3" else ".wav"
        return self._save_audio_bytes(response.audio_content, extension)

    def generate_audio_for_scenes(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        updated_scenes = []

        for scene in scenes:
            scene_copy = dict(scene)
            narration = scene_copy.get("narration", "").strip()

            if not narration:
                scene_copy["audio_url"] = ""
                scene_copy["audio_generation_skipped"] = True
                scene_copy["audio_generation_reason"] = "missing_narration"
                updated_scenes.append(scene_copy)
                continue

            try:
                audio_url = self.generate_audio_from_text(narration)
                scene_copy["audio_url"] = audio_url
                scene_copy["audio_generation_skipped"] = False
                scene_copy["audio_generation_reason"] = ""
            except Exception as exc:
                scene_copy["audio_url"] = ""
                scene_copy["audio_generation_skipped"] = True
                scene_copy["audio_generation_reason"] = str(exc)

            updated_scenes.append(scene_copy)

        return updated_scenes