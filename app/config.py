from pydantic_settings import BaseSettings
from typing import Dict, Any
import json
from pathlib import Path

class Settings(BaseSettings):
    # Drone settings
    TELLO_IP: str = "192.168.10.1"
    TELLO_PORT: int = 8889
    LOCAL_IP: str = ""
    LOCAL_PORT: int = 8889
    
    # ArUco settings
    ARUCO_DICT_TYPE: str = "DICT_6X6_250"
    ARUCO_MARKER_SIZE: float = 0.15  # meters
    HOME_MARKER_ID: int = 1
    
    # Mission settings
    TAKEOFF_HEIGHT: float = 1.0  # meters
    SAFE_LANDING_HEIGHT: float = 0.5  # meters
    MISSION_TIMEOUT: int = 180  # seconds
    
    # Video settings
    VIDEO_PORT: int = 11111
    FRAME_WIDTH: int = 960
    FRAME_HEIGHT: int = 720
    
    @property
    def locations(self) -> Dict[str, Any]:
        """Load predefined locations and paths from config file"""
        config_path = Path("config/locations.json")
        if not config_path.exists():
            return {}
        with open(config_path) as f:
            return json.load(f)

settings = Settings()
