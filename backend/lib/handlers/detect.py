from typing import Any, Dict, Optional, Tuple, Union

import cv2
import numpy as np

from ..utils.logger import get_logger

logger = get_logger("detect")


class DetectHandler:
    def __init__(self, name: str = "yahboom", **kwargs: Any) -> None:
        if name == "yahboom":
            self.handler = YahboomDetectHandler(**kwargs)

    def process(self, frame: np.ndarray, debug: bool = False, **kwargs: Any) -> Dict[str, Any]:
        return self.handler.process(frame, debug=debug, **kwargs)


class YahboomDetectHandler:
    def __init__(
        self,
        color_hsv_thresholds: Dict[str, Tuple[Tuple[Tuple[int, int, int], Tuple[int, int, int]], ...]] = {
            "red": (((0, 70, 50), (10, 255, 255)), ((170, 70, 50), (180, 255, 255))),
            "green": (((34, 43, 46), (77, 255, 255)),),
            "blue": (((72, 205, 99), (122, 255, 229)),),
            "yellow": (((21, 172, 185), (33, 255, 242)),),
        },
        coord_mapping_configs: Dict[str, Any] = {
            "pixels_per_meter": [4200, 4000],
            "rotation_matrix": [[0, -1], [-1, 0]],
            "offset": [480 / 4000 + 0.15, 320 / 4200],
        },
    ) -> None:
        self.wnd_size: Optional[Tuple[int, int]] = None
        self.color_hsv_thresholds = color_hsv_thresholds
        self.coord_mapping_configs = coord_mapping_configs

    def _detect_square(self, frame: np.ndarray, color: str) -> Optional[np.ndarray]:
        if color == "red":
            return None

        im = frame.copy()
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        for lowerb, upperb in self.color_hsv_thresholds[color]:
            mask_ = cv2.inRange(hsv, np.array(lowerb, dtype=np.uint8), np.array(upperb, dtype=np.uint8))
            mask |= mask_

        im[mask == 0] = 0

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        im = cv2.morphologyEx(im, cv2.MORPH_CLOSE, kernel)
        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        _, threshold = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) == 0:
            return None

        contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(contour)

        if area < 1000:
            return None

        return contour

    def _coord_mapping(
        self, x: float, y: float, w: Optional[float] = None, h: Optional[float] = None
    ) -> Union[Tuple[float, float], Tuple[float, float, float, float]]:
        cfgs = self.coord_mapping_configs
        x /= cfgs["pixels_per_meter"][0]
        y /= cfgs["pixels_per_meter"][1]
        x_, y_ = x, y
        x = cfgs["rotation_matrix"][0][0] * x_ + cfgs["rotation_matrix"][0][1] * y_
        y = cfgs["rotation_matrix"][1][0] * x_ + cfgs["rotation_matrix"][1][1] * y_
        x += cfgs["offset"][0]
        y += cfgs["offset"][1]

        if w is not None and h is not None:
            # Create new float variables to make mypy happy
            w_float: float = w / cfgs["pixels_per_meter"][0]
            h_float: float = h / cfgs["pixels_per_meter"][1]

            # buggy code
            # w_float = cfgs["rotation_matrix"][0][0] * w_float + cfgs["rotation_matrix"][0][1] * h_float
            # h_float = cfgs["rotation_matrix"][1][0] * w_float + cfgs["rotation_matrix"][1][1] * h_float

            return x, y, w_float, h_float

        return x, y

    def process(self, frame: np.ndarray, do_coord_mapping: bool = True, debug: bool = False) -> Dict[str, Any]:
        h, w = frame.shape[:2]

        if debug and (not self.wnd_size or self.wnd_size != (h, w)):
            logger.info(f"Resizing window to {w}x{h}")
            cv2.namedWindow("Detect", cv2.WINDOW_GUI_NORMAL)
            cv2.resizeWindow("Detect", w, h)

            self.wnd_size = (h, w)

        detections = []
        im = frame.copy()

        for color in self.color_hsv_thresholds:
            contour = self._detect_square(frame, color)
            if contour is None:
                continue

            rotate_rect = cv2.minAreaRect(contour)
            (cx, cy), _, yaw = rotate_rect

            corners = np.array(cv2.boxPoints(rotate_rect), dtype=np.int32)

            cv2.drawContours(im, [corners], 0, (255, 0, 0), 3)
            cv2.circle(im, (int(cx), int(cy)), 5, (0, 0, 255), -1)
            cv2.putText(im, color, (int(cx - 15), int(cy - 15)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)

            x, y, w, h = cv2.boundingRect(contour)

            if do_coord_mapping:
                cx_, cy_ = cx, cy
                cx, cy = self._coord_mapping(cx_, cy_)  # type: ignore
                x, y, w, h = self._coord_mapping(x, y, w, h)  # type: ignore
                cv2.putText(
                    im,
                    f"({100 * cx:.3f}, {100 * cy:.3f})",
                    (int(cx_ - 60), int(cy_ + 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 0, 255),
                    2,
                )
            detections.append(
                {
                    "label": color,
                    "box": (x, y, w, h),
                    "center": (cx, cy),
                    "corners": corners,
                    "yaw": yaw,
                }
            )

        if debug:
            cv2.imshow("Detect", im)
            cv2.waitKey(10)

        return {"detections": detections, "processed_frame": im}
