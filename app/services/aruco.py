import cv2
import numpy as np
from typing import Tuple, Optional, List
from ..config import settings

class ArucoDetector:
    def __init__(self):
        # Get the appropriate ArUco dictionary
        self.aruco_dict = cv2.aruco.Dictionary_get(
            getattr(cv2.aruco, settings.ARUCO_DICT_TYPE)
        )
        self.aruco_params = cv2.aruco.DetectorParameters_create()
        
        # Camera matrix and distortion coefficients (can be calibrated later)
        self.camera_matrix = np.array([
            [921.170702, 0.000000, 459.904354],
            [0.000000, 919.018377, 351.238301],
            [0.000000, 0.000000, 1.000000]])
        self.dist_coeffs = np.zeros((4,1))

    def detect_markers(self, frame: np.ndarray) -> Tuple[List[int], List[np.ndarray]]:
        """Detect ArUco markers in the frame"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = cv2.aruco.detectMarkers(
            gray, self.aruco_dict, parameters=self.aruco_params
        )
        
        if ids is None:
            return [], []
            
        return ids.flatten().tolist(), corners

    def estimate_marker_pose(self, corners: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Estimate pose of a marker given its corners"""
        rvec, tvec, _ = cv2.aruco.estimatePoseSingleMarkers(
            corners, settings.ARUCO_MARKER_SIZE, 
            self.camera_matrix, self.dist_coeffs
        )
        return rvec, tvec

    def get_landing_alignment(self, frame: np.ndarray) -> Tuple[bool, Optional[dict]]:
        """
        Analyze frame for home markers and determine if drone is aligned for landing
        Returns: (is_aligned, alignment_data)
        """
        ids, corners = self.detect_markers(frame)
        
        if settings.HOME_MARKER_ID not in ids:
            return False, None
            
        # Get index of home marker
        marker_idx = ids.index(settings.HOME_MARKER_ID)
        marker_corners = corners[marker_idx]
        
        # Get pose estimation
        rvec, tvec = self.estimate_marker_pose(marker_corners)
        
        # Calculate marker center in image
        marker_center = marker_corners[0].mean(axis=0)
        frame_center = np.array([frame.shape[1]/2, frame.shape[0]/2])
        
        # Calculate distance from center and marker size
        distance_from_center = np.linalg.norm(marker_center - frame_center)
        marker_size = cv2.contourArea(marker_corners[0].astype(np.float32))
        
        # Define alignment criteria
        size_threshold = frame.shape[0] * frame.shape[1] * 0.1  # 10% of frame
        center_threshold = 50  # pixels
        
        is_aligned = (
            distance_from_center < center_threshold and 
            marker_size > size_threshold
        )
        
        alignment_data = {
            'distance_from_center': float(distance_from_center),
            'marker_size': float(marker_size),
            'translation': tvec[0].tolist(),
            'rotation': rvec[0].tolist(),
            'is_aligned': is_aligned
        }
        
        return is_aligned, alignment_data
