from typing import Optional, Dict, Any, List
import asyncio
import time
from ..config import settings
from ..services.aruco import ArucoDetector
from ..core.exceptions import DroneOperationError
from enhanced_tello import EnhancedTello  # Your provided class

class DroneController:
    def __init__(self):
        self.drone = EnhancedTello(
            local_ip=settings.LOCAL_IP,
            cmd_port=settings.LOCAL_PORT
        )
        self.aruco_detector = ArucoDetector()
        self.mission_in_progress = False
        self.current_mission: Optional[Dict[str, Any]] = None
        self.image_buffer: List[np.ndarray] = []
        
    async def initialize(self):
        """Initialize drone connection and video stream"""
        if not self.drone.start_video_stream():
            raise DroneOperationError("Failed to start video stream")
        await asyncio.sleep(2)  # Wait for video stream to stabilize
        
    async def execute_mission(self, location_id: str) -> Dict[str, Any]:
        """Execute a complete mission to a predefined location"""
        if self.mission_in_progress:
            raise DroneOperationError("Another mission is already in progress")
            
        location_data = settings.locations.get(location_id)
        if not location_data:
            raise DroneOperationError(f"Unknown location: {location_id}")
            
        self.mission_in_progress = True
        self.current_mission = {
            'location_id': location_id,
            'start_time': time.time(),
            'status': 'in_progress'
        }
        
        try:
            # Take off and move to initial height
            await self._takeoff_sequence()
            
            # Execute predefined path to location
            await self._execute_path(location_data['path'])
            
            # Capture images/video at location
            await self._capture_location(location_data.get('capture_points', []))
            
            # Return home
            await self._return_home()
            
            self.current_mission['status'] = 'completed'
            return self.current_mission
            
        except Exception as e:
            self.current_mission['status'] = 'failed'
            self.current_mission['error'] = str(e)
            raise DroneOperationError(f"Mission failed: {str(e)}")
        finally:
            self.mission_in_progress = False
            
    async def _takeoff_sequence(self):
        """Execute takeoff sequence with home marker alignment"""
        # Check battery level before takeoff
        battery = self.drone.get_battery()
        if battery < 20:
            raise DroneOperationError(f"Battery too low for mission: {battery}%")
        
        # Ensure we can see the home marker
        frame = self.drone.get_frame()
        if frame is None:
            raise DroneOperationError("No video frame available")
            
        _, alignment = self.aruco_detector.get_landing_alignment(frame)
        if alignment is None:
            raise DroneOperationError("Cannot detect home marker before takeoff")
        
        # Execute takeoff
        if not self.drone._send_command('takeoff'):
            raise DroneOperationError("Takeoff command failed")
            
        # Move to mission height
        if not self.drone._send_command(f'up {int(settings.TAKEOFF_HEIGHT * 100)}'):
            raise DroneOperationError("Failed to reach takeoff height")
    
    async def _execute_path(self, path_commands: List[Dict[str, Any]]):
        """Execute a series of movement commands"""
        for cmd in path_commands:
            command = f"{cmd['direction']} {int(cmd['distance'] * 100)}"
            if not self.drone._send_command(command):
                raise DroneOperationError(f"Path command failed: {command}")
            await asyncio.sleep(cmd.get('delay', 2))
    
    async def _capture_location(self, capture_points: List[Dict[str, Any]]):
        """Capture images/video at specified points"""
        self.image_buffer.clear()
        
        for point in capture_points:
            # Move to capture position if specified
            if 'position' in point:
                await self._execute_path([point['position']])
            
            # Capture frames
            frames_to_capture = point.get('frames', 1)
            for _ in range(frames_to_capture):
                frame = self.drone.get_frame()
                if frame is not None:
                    self.image_buffer.append(frame)
                await asyncio.sleep(0.5)
    
    async def _return_home(self):
        """Return to home position and land"""
        # Execute return path
        return_path = settings.locations['home']['return_path']
        await self._execute_path(return_path)
        
        # Align with landing marker
        aligned = False
        attempts = 0
        
        while not aligned and attempts < 3:
            frame = self.drone.get_frame()
            if frame is None:
                raise DroneOperationError("No video frame available for landing")
                
            aligned, alignment = self.aruco_detector.get_landing_alignment(frame)
            
            if not aligned:
                # Make small adjustments based on marker position
                if alignment:
                    if alignment['distance_from_center'] > 50:
                        # Move to center the marker
                        dx = alignment['translation'][0]
                        dy = alignment['translation'][1]
                        
                        if abs(dx) > 0.2:
                            cmd = f"{'right' if dx > 0 else 'left'} 20"
                            self.drone._send_command(cmd)
                            
                        if abs(dy) > 0.2:
                            cmd = f"{'forward' if dy > 0 else 'back'} 20"
                            self.drone._send_command(cmd)
                
            attempts += 1
            await asyncio.sleep(1)
        
        if not aligned:
            raise DroneOperationError("Failed to align with landing marker")
            
        # Execute landing
        if not self.drone._send_command('land'):
            raise DroneOperationError("Landing command failed")
            
    def get_status(self) -> Dict[str, Any]:
        """Get current drone status"""
        return {
            'battery': self.drone.get_battery(),
            'mission_in_progress': self.mission_in_progress,
            'current_mission': self.current_mission
        }
        
    def cleanup(self):
        """Cleanup drone resources"""
        self.drone.stop_video_stream()
        # Additional cleanup as needed
