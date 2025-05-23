from typing import Dict, Optional, Tuple, Union

import cv2
import numpy as np

from .base import BaseHandler


class CalibrateHandler(BaseHandler):
    def __init__(self) -> None:
        self.calibration_matrix: Optional[np.ndarray] = None
        self.scale_transform: Optional[np.ndarray] = None
        self._inverse_scale_transform: Optional[np.ndarray] = None

        # Cache parameters to avoid recalculation
        self._cached_frame_shape: Optional[Tuple[int, int]] = None
        self._cached_world_bounds: Optional[Tuple[float, float, float, float]] = None
        self._cached_max_size: Optional[int] = None
        self._cached_output_size: Optional[Tuple[int, int]] = None
        self._cached_combined_matrix: Optional[np.ndarray] = None
        self._cached_calibration_matrix_id: Optional[int] = None

    def reset(self) -> None:
        """Clear calibration matrix, scale transforms, and cached parameters"""
        self.calibration_matrix = None
        self.scale_transform = None
        self._inverse_scale_transform = None
        self._cached_frame_shape = None
        self._cached_world_bounds = None
        self._cached_max_size = None
        self._cached_output_size = None
        self._cached_combined_matrix = None
        self._cached_calibration_matrix_id = None

    def _needs_recalculation(
        self, frame_shape: Tuple[int, int], world_bounds: Optional[Tuple[float, float, float, float]], max_size: int
    ) -> bool:
        """Check if combined calibration matrix needs recalculation due to parameter changes"""
        current_calibration_id = id(self.calibration_matrix) if self.calibration_matrix is not None else None

        return (
            self.scale_transform is None
            or self._cached_frame_shape != frame_shape
            or self._cached_world_bounds != world_bounds
            or self._cached_max_size != max_size
            or self._cached_calibration_matrix_id != current_calibration_id
        )

    def _calculate_combined_calibration_matrix(
        self, frame_shape: Tuple[int, int], world_bounds: Optional[Tuple[float, float, float, float]], max_size: int
    ) -> None:
        """Calculate and cache scale transform, its inverse, and combined calibration matrix"""
        # Type assertion: This method should only be called when calibration_matrix is not None
        assert self.calibration_matrix is not None, "Calibration matrix must be set before calling this method"

        h, w = frame_shape

        # Cache the INPUT parameters first (before any modifications)
        self._cached_frame_shape = frame_shape
        self._cached_world_bounds = world_bounds  # Cache the input (could be None)
        self._cached_max_size = max_size
        self._cached_calibration_matrix_id = id(self.calibration_matrix)

        # Calculate world_bounds if not provided
        if world_bounds is None:
            # Transform the four corners of the input image to world coordinates
            image_corners = np.array(
                [
                    [0, 0],  # Top-left
                    [w - 1, 0],  # Top-right
                    [w - 1, h - 1],  # Bottom-right
                    [0, h - 1],  # Bottom-left
                ],
                dtype=np.float32,
            )

            # Transform image corners to world coordinates
            world_corners = cv2.perspectiveTransform(image_corners.reshape(-1, 1, 2), self.calibration_matrix).reshape(
                -1, 2
            )

            # Find bounding rectangle of the transformed corners
            min_x, min_y = world_corners.min(axis=0)
            max_x, max_y = world_corners.max(axis=0)

            world_bounds = (min_x, min_y, max_x, max_y)

        min_x, min_y, max_x, max_y = world_bounds

        # Calculate world coordinate dimensions and aspect ratio
        world_width = max_x - min_x
        world_height = max_y - min_y
        world_aspect_ratio = world_width / world_height

        # Calculate output dimensions preserving world aspect ratio
        if world_aspect_ratio > 1:  # Wider than tall
            output_width = max_size
            output_height = int(max_size / world_aspect_ratio)
        else:  # Taller than wide
            output_height = max_size
            output_width = int(max_size * world_aspect_ratio)

        # Create simple scaling transformation: world_bounds → (0, 0, output_width, output_height)
        scale_x = (output_width - 1) / world_width
        scale_y = (output_height - 1) / world_height

        # Create transformation matrix for scaling and translation
        self.scale_transform = np.array(
            [[scale_x, 0, -min_x * scale_x], [0, scale_y, -min_y * scale_y], [0, 0, 1]], dtype=np.float32
        )

        # Pre-calculate inverse for efficient coordinate transformation
        self._inverse_scale_transform = np.linalg.inv(self.scale_transform)

        # Calculate combined matrix: image → world → scaled output
        combined_matrix = np.dot(self.scale_transform, self.calibration_matrix)

        # Cache calculated results
        self._cached_output_size = (output_width, output_height)
        self._cached_combined_matrix = combined_matrix

    def calculate_calibration_matrix(
        self, image_points: np.ndarray, world_points: np.ndarray, method: str = "perspective"
    ) -> bool:
        """
        Calculate calibration matrix from point pairs.

        Args:
            image_points: Array of (x, y) coordinates in image pixels, shape (N, 2)
            world_points: Array of (x, y) coordinates in world units, shape (N, 2)
            method: "perspective" (requires 4+ points) or "affine" (requires 3+ points)

        Returns:
            True if calibration successful, False otherwise
        """
        min_points = 4 if method == "perspective" else 3

        if len(image_points) < min_points or len(image_points) != len(world_points):
            return False

        src_pts = image_points.astype(np.float32)
        dst_pts = world_points.astype(np.float32)

        try:
            if method == "perspective":
                if len(image_points) == 4:
                    # Exact solution for 4 points
                    self.calibration_matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
                else:
                    # Least squares solution for 5+ points
                    self.calibration_matrix, _ = cv2.findHomography(
                        src_pts, dst_pts, cv2.RANSAC, ransacReprojThreshold=1.0
                    )
            else:  # affine
                self.calibration_matrix = cv2.getAffineTransform(src_pts[:3], dst_pts[:3])

            return self.calibration_matrix is not None
        except cv2.error:
            return False

    def get_coords_image_to_world(self, image_points: np.ndarray) -> Optional[np.ndarray]:
        """Transform points from image coordinates to world coordinates

        Args:
            image_points: Array of (x, y) coordinates in image pixels, shape (N, 2)

        Returns:
            Array of (x, y) coordinates in world units, shape (N, 2), or None if not calibrated
        """
        if self.calibration_matrix is None:
            return None

        # Reshape for cv2.perspectiveTransform: (N, 1, 2)
        points_reshaped = image_points.astype(np.float32).reshape(-1, 1, 2)

        if self.calibration_matrix.shape[0] == 3:  # Perspective transform
            transformed = cv2.perspectiveTransform(points_reshaped, self.calibration_matrix)
        else:  # Affine transform
            # Convert affine matrix to perspective format for consistency
            affine_3x3 = np.vstack([self.calibration_matrix, [0, 0, 1]])
            transformed = cv2.perspectiveTransform(points_reshaped, affine_3x3)

        return transformed.reshape(-1, 2)

    def get_coords_processed_image_to_world(self, processed_points: np.ndarray) -> Optional[np.ndarray]:
        """Transform points from processed frame coordinates to world coordinates

        Args:
            processed_points: Array of (x, y) coordinates in processed frame pixels, shape (N, 2)

        Returns:
            Array of (x, y) coordinates in world units, shape (N, 2), or None if not calibrated
        """
        if self._inverse_scale_transform is None:
            return None

        # Reshape for cv2.perspectiveTransform: (N, 1, 2)
        points_reshaped = processed_points.astype(np.float32).reshape(-1, 1, 2)

        transformed = cv2.perspectiveTransform(points_reshaped, self._inverse_scale_transform)
        return transformed.reshape(-1, 2)

    def process(
        self,
        frame: np.ndarray,
        world_bounds: Optional[Tuple[float, float, float, float]] = None,
        max_size: int = 640,
    ) -> Dict[str, Union[bool, np.ndarray]]:
        """
        Process frame with calibration. Returns perspective-corrected frame and calibration status.

        Args:
            frame: Input frame
            world_bounds: (min_x, min_y, max_x, max_y) in world coordinates to show
                         If None, uses entire camera field of view
            max_size: Maximum width or height of output, aspect ratio preserved

        Returns:
            Dict with 'calibrated' (bool) and 'processed_frame' (np.ndarray) keys
        """
        h, w = frame.shape[:2]
        frame_shape = (h, w)

        if self.calibration_matrix is None:
            return {"calibrated": False, "processed_frame": frame.copy()}

        # Check if we need to recalculate combined calibration matrix
        if self._needs_recalculation(frame_shape, world_bounds, max_size):
            self._calculate_combined_calibration_matrix(frame_shape, world_bounds, max_size)

        # Safety check: Ensure cached values are available
        if self._cached_combined_matrix is None or self._cached_output_size is None:
            return {"calibrated": False, "processed_frame": frame.copy()}

        # Use cached values
        combined_matrix = self._cached_combined_matrix
        output_width, output_height = self._cached_output_size

        # Apply the transformation
        processed_frame = cv2.warpPerspective(frame, combined_matrix, (output_width, output_height))

        return {"calibrated": True, "processed_frame": processed_frame}
