import cv2
import numpy as np

from ..utils.logger import get_logger

logger = get_logger("detect")


class DetectHandler:
    def __init__(self, name="yahboom", **kwargs):
        if name == "yahboom":
            self.handler = YahboomDetectHandler(**kwargs)

    def process(self, frame, debug=False, **kwargs):
        return self.handler.process(frame, debug=debug, **kwargs)


class YahboomDetectHandler:
    def __init__(
        self,
        color_hsv_thresholds={
            "red": ((0, 43, 46), (10, 255, 255)),
            "green": ((35, 43, 46), (77, 255, 255)),
            "blue": ((100, 43, 46), (124, 255, 255)),
            "yellow": ((26, 43, 46), (34, 255, 255)),
        },
        coord_mapping_configs={
            "pixels_per_meter": [4200, 4000],
            "rotation_matrix": [[0, -1], [-1, 0]],
            "offset": [0.27, 0.0762],  # 480 / 4000 + 0.15, 320 / 4200
        },
    ):
        self.wnd_size = None
        self.color_hsv_thresholds = color_hsv_thresholds
        self.coord_mapping_configs = coord_mapping_configs

    def _detect_square(self, frame, color):
        (lowerb, upperb) = self.color_hsv_thresholds[color]
        im = frame.copy()
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        im[cv2.inRange(hsv, lowerb, upperb) == 0] = 0
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        im = cv2.morphologyEx(im, cv2.MORPH_CLOSE, kernel)
        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        _, threshold = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(contour)

        if area < 1000:
            return None

        return contour

    def _coord_mapping(self, x, y, w=None, h=None):
        cfgs = self.coord_mapping_configs
        x /= cfgs["pixels_per_meter"][0]
        y /= cfgs["pixels_per_meter"][1]
        x = cfgs["rotation_matrix"][0][0] * x + cfgs["rotation_matrix"][0][1] * y
        y = cfgs["rotation_matrix"][1][0] * x + cfgs["rotation_matrix"][1][1] * y
        x += cfgs["offset"][0]
        y += cfgs["offset"][1]

        if w is not None and h is not None:
            w /= cfgs["pixels_per_meter"][0]
            h /= cfgs["pixels_per_meter"][1]
            w = cfgs["rotation_matrix"][0][0] * w + cfgs["rotation_matrix"][0][1] * h
            h = cfgs["rotation_matrix"][1][0] * w + cfgs["rotation_matrix"][1][1] * h

            return x, y, w, h

        return x, y

    def process(self, frame, do_coord_mapping=True, debug=False):
        h, w = frame.shape[:2]

        if debug and (not self.wnd_size or self.wnd_size != (h, w)):
            logger.info(f"Resizing window to {w}x{h}")
            cv2.namedWindow("Detect", cv2.WINDOW_GUI_NORMAL)
            cv2.resizeWindow("Detect", w, h)

            self.wnd_size = (h, w)

        detections = []
        for color in self.color_hsv_thresholds:
            contour = self._detect_square(frame, color)
            if contour is None:
                continue

            rotate_rect = cv2.minAreaRect(contour)
            (cx, cy), _, yaw = rotate_rect

            corners = np.int64(cv2.boxPoints(rotate_rect))

            if debug:
                im = frame.copy()
                cv2.drawContours(im, [corners], 0, (255, 0, 0), 3)
                cv2.circle(im, (int(cx), int(cy)), 5, (0, 0, 255), -1)
                cv2.putText(im, color, (int(cx - 15), int(cy - 15)), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
                cv2.imshow("Detect", im)
                cv2.waitKey(10)

            x, y, w, h = cv2.boundingRect(contour)

            if do_coord_mapping:
                cx, cy = self._coord_mapping(cx, cy)
                x, y, w, h = self._coord_mapping(x, y, w, h)

            detections.append(
                {
                    "label": color,
                    "box": (x, y, w, h),
                    "center": (cx, cy),
                    "corners": corners,
                    "yaw": yaw,
                }
            )

        return detections
