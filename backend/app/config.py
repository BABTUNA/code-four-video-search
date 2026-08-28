from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_DIRECTORY = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_DIRECTORY / ".env",
        extra="ignore",
    )

    video_directory: Path = PROJECT_DIRECTORY / "c4-videos"
    database_path: Path = PROJECT_DIRECTORY / "data" / "app.db"
    derived_directory: Path = PROJECT_DIRECTORY / "data" / "derived"
    frontend_origin: str = "http://localhost:3000"

    segment_video_height: int = 720
    ocr_frame_interval_seconds: float = 5.0
    max_concurrent_segments: int = 4

    processor_backend: Literal["fake", "openrouter"] = "fake"
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    visual_model: str = "google/gemini-3.7-flash"
    audio_model: str = "google/gemini-3.7-flash"
    transcript_model: str = "openai/gpt-4o-mini-transcribe"
    ocr_model: str = "google/gemini-3.7-flash"


settings = Settings()
