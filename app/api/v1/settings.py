from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.config import settings

router = APIRouter(prefix="/settings", tags=["Settings"])

class SettingsUpdateRequest(BaseModel):
    google_ai_studio_api_key: Optional[str] = None
    gemini_model: Optional[str] = None

class SettingsResponse(BaseModel):
    has_gemini_key: bool
    gemini_model: str
    masked_key: Optional[str] = None

@router.get("", response_model=SettingsResponse)
async def get_settings():
    key = settings.GOOGLE_AI_STUDIO_API_KEY
    has_key = bool(key and not key.startswith("your_") and len(key) > 5)
    masked = f"{key[:4]}...{key[-4:]}" if has_key else None
    return {
        "has_gemini_key": has_key,
        "gemini_model": settings.GEMINI_MODEL,
        "masked_key": masked
    }

@router.post("")
async def update_settings(payload: SettingsUpdateRequest):
    if payload.google_ai_studio_api_key is not None:
        clean_key = payload.google_ai_studio_api_key.strip()
        settings.GOOGLE_AI_STUDIO_API_KEY = clean_key
    if payload.gemini_model is not None:
        settings.GEMINI_MODEL = payload.gemini_model.strip()

    return {
        "success": True,
        "message": "Settings updated successfully",
        "has_gemini_key": bool(settings.GOOGLE_AI_STUDIO_API_KEY and not settings.GOOGLE_AI_STUDIO_API_KEY.startswith("your_")),
        "gemini_model": settings.GEMINI_MODEL
    }
