from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class MissionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class MissionRequest(BaseModel):
    location_id: str = Field(..., description="ID of the predefined location to visit")
    priority: int = Field(default=1, ge=1, le=5, description="Mission priority (1-5)")
    capture_settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional custom capture settings for this mission"
    )

class MissionResponse(BaseModel):
    mission_id: str
    location_id: str
    status: MissionStatus
    start_time: Optional[float] = None
    completion_time: Optional[float] = None
    images_captured: int = 0
    error_message: Optional[str] = None

class DroneStatus(BaseModel):
    battery_level: int
    mission_in_progress: bool
    current_mission: Optional[Dict[str, Any]]
    video_streaming: bool
    is_flying: bool
