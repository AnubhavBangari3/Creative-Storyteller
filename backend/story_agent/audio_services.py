import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

from django.conf import settings

from .storage_service import GCSStorageService

try:
    from google.cloud import texttospeech
except Exception:
    texttospeech = None


class GeminiTTSService:
    def __init__(self):
        self.provider = (getattr(settings, "TTS_PROVIDER", "browser") or "browser").lower().strip()
        self.language_code = (getattr(settings, "TTS_LANGUAGE_CODE", "en-US") or "en-US").strip()
        self.voice_name = (getattr(settings, "TTS_VOICE_NAME", "en-US-Neural2-F") or "en-US-Neural2-F").strip()
        self.audio_encoding = (getattr(settings, "TTS_AUDIO_ENCODING", "MP3") or "MP3").strip().upper()

        self.use_gcs_for_audio = getattr(settings, "USE_GCS_FOR_AUDIO", False)
        self.storage_service = GCSStorageService() if self.use_gcs_for_audio else None

        self.output_dir = Path(settings.MEDIA_ROOT) / "generated_audio"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.client: Optional[object] = None

        print("TTS SERVICE INITIALIZING...")
        print("TTS PROVIDER:", self.provider)
        print("TTS LANGUAGE CODE:", self.language_code)
        print("TTS VOICE NAME:", self.voice_name)
        print("TTS AUDIO ENCODING:", self.audio_encoding)
        print("USE GCS FOR AUDIO:", self.use_gcs_for_audio)

        if self.provider == "gcp":
            if texttospeech is None:
                raise ValueError("google-cloud-texttospeech package is not available.")

            # IMPORTANT:
            # On Cloud Run, Application Default Credentials are used automatically
            # from the attached service account.
            # Do NOT force GOOGLE_APPLICATION_CREDENTIALS here.
            self.client = texttospeech.TextToSpeechClient()

    def _get_audio_encoding(self):
        if texttospeech is None:
            raise ValueError("google-cloud-texttospeech package is not available.")

        encoding_map = {
            "MP3": texttospeech.AudioEncoding.MP3,
            "LINEAR16": texttospeech.AudioEncoding.LINEAR16,
            "OGG_OPUS": texttospeech.AudioEncoding.OGG_OPUS,
        }
        return encoding_map.get(self.audio_encoding, texttospeech.AudioEncoding.MP3)

    def _get_extension_for_encoding(self) -> str:
        if self.audio_encoding == "LINEAR16":
            return "wav"
        if self.audio_encoding == "OGG_OPUS":
            return "ogg"
        return "mp3"

    def _save_audio_locally(
        self,
        audio_bytes: bytes,
        extension: str = ".mp3",
        filename_prefix: str = "audio",
    ) -> str:
        if not audio_bytes:
            raise ValueError("Generated audio bytes are empty.")

        filename = f"{filename_prefix}-{uuid.uuid4().hex}{extension}"
        filepath = self.output_dir / filename

        with open(filepath, "wb") as f:
            f.write(audio_bytes)

        return f"{settings.MEDIA_URL}generated_audio/{filename}"

    def _upload_audio_to_gcs(
        self,
        audio_bytes: bytes,
        extension: str = "mp3",
        filename_prefix: str = "audio",
    ) -> str:
        if not self.storage_service:
            raise ValueError("GCS storage service is not initialized for audio.")

        if not audio_bytes:
            raise ValueError("Generated audio bytes are empty.")

        content_type_map = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "ogg": "audio/ogg",
        }

        filename = self.storage_service.generate_unique_filename(
            prefix=f"generated_audio/{filename_prefix}",
            extension=extension,
        )

        return self.storage_service.upload_bytes(
            file_bytes=audio_bytes,
            destination_blob_name=filename,
            content_type=content_type_map.get(extension.lower(), "audio/mpeg"),
        )

    def _store_audio(
        self,
        audio_bytes: bytes,
        extension: str,
        filename_prefix: str = "audio",
    ) -> str:
        if self.use_gcs_for_audio:
            return self._upload_audio_to_gcs(
                audio_bytes=audio_bytes,
                extension=extension,
                filename_prefix=filename_prefix,
            )

        return self._save_audio_locally(
            audio_bytes=audio_bytes,
            extension=f".{extension}",
            filename_prefix=filename_prefix,
        )

    def generate_audio_from_text(self, text: str, filename_prefix: str = "scene-audio") -> str:
        if not text or not text.strip():
            raise ValueError("Text for TTS is empty.")

        if self.provider == "browser":
            raise ValueError("browser_tts_selected")

        if self.provider != "gcp":
            raise ValueError(f"unsupported_tts_provider: {self.provider}")

        if not self.client:
            raise ValueError("Google TTS client is not initialized.")

        synthesis_input = texttospeech.SynthesisInput(text=text.strip())

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

        extension = self._get_extension_for_encoding()

        return self._store_audio(
            audio_bytes=response.audio_content,
            extension=extension,
            filename_prefix=filename_prefix,
        )

    # Backward-compatible aliases
    def synthesize_speech(self, text: str, filename_prefix: str = "scene-audio") -> str:
        return self.generate_audio_from_text(text=text, filename_prefix=filename_prefix)

    def text_to_speech(self, text: str, filename_prefix: str = "scene-audio") -> str:
        return self.generate_audio_from_text(text=text, filename_prefix=filename_prefix)

    def generate_audio_for_scenes(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        updated_scenes = []

        for index, scene in enumerate(scenes, start=1):
            scene_copy = dict(scene)
            narration = scene_copy.get("narration", "").strip()

            if not narration:
                scene_copy["audio_url"] = ""
                scene_copy["audio_generation_skipped"] = True
                scene_copy["audio_generation_reason"] = "missing_narration"
                scene_copy["audio_generation_error"] = ""
                updated_scenes.append(scene_copy)
                continue

            try:
                audio_url = self.generate_audio_from_text(
                    narration,
                    filename_prefix=f"scene-audio-{index}",
                )
                scene_copy["audio_url"] = audio_url
                scene_copy["audio_generation_skipped"] = False
                scene_copy["audio_generation_reason"] = ""
                scene_copy["audio_generation_error"] = ""
            except Exception as exc:
                raw_error = str(exc)
                error_text = raw_error.lower()

                print("AUDIO GENERATION ERROR:", raw_error)

                scene_copy["audio_url"] = ""
                scene_copy["audio_generation_skipped"] = True
                scene_copy["audio_generation_error"] = raw_error

                if "browser_tts_selected" in error_text:
                    reason = "browser_tts_selected"
                elif "permission" in error_text or "403" in error_text:
                    reason = "permission_denied"
                elif "unauthenticated" in error_text or "401" in error_text:
                    reason = "auth_failed"
                elif "quota" in error_text or "resource_exhausted" in error_text:
                    reason = "quota_exceeded"
                elif "credentials" in error_text:
                    reason = "provider_not_configured"
                elif "unsupported_tts_provider" in error_text:
                    reason = "unsupported_provider"
                else:
                    reason = "generation_failed"

                scene_copy["audio_generation_reason"] = reason

            updated_scenes.append(scene_copy)

        return updated_scenes