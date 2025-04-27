import cv2
import numpy as np

from utils.logger import get_logger

logger = get_logger("calibrate")


class CalibrateHandler:
    def __init__(self, name="yahboom", **kwargs):
        if name == "yahboom":
            self.handler = YahboomCalibrateHandler()

    def process(self, frame, debug=False, **kwargs):
        return self.handler.process(frame, debug=debug, **kwargs)


class YahboomCalibrateHandler:
    def __init__(self, binary_threshold=140):
        self.wnd_size = None
        self.binary_threshold = binary_threshold

    def process(self, frame, debug=False):
        h, w = frame.shape[:2]

        if debug and (not self.wnd_size or self.wnd_size != (h, w)):
            logger.info(f"Resizing window to {w}x{h}")
            cv2.namedWindow("Calibrate", cv2.WINDOW_GUI_NORMAL)
            cv2.resizeWindow("Calibrate", w, h)

            cv2.namedWindow("PerspectiveTransform", cv2.WINDOW_GUI_NORMAL)
            cv2.resizeWindow("PerspectiveTransform", w, h)

            self.wnd_size = (h, w)

        im = frame.copy()
        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 1)
        _, threshold = cv2.threshold(gray, self.binary_threshold, 255, cv2.THRESH_BINARY)

        kernel = np.ones((3, 3), np.uint8)
        blur = cv2.morphologyEx(threshold, cv2.MORPH_OPEN, kernel, iterations=4)

        contours, _ = cv2.findContours(blur, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        im_area = h * w
        perspective_img = np.zeros((h, w, 3), dtype=np.uint8)
        succeed = False

        for contour in contours:
            contour_area = cv2.contourArea(contour)
            if im_area / 2 < contour_area < im_area:
                cv2.drawContours(im, [contour], -1, (0, 0, 255), 2)
                approx = cv2.approxPolyDP(contour, 100, True)  # Renamed dp to approx for clarity
                cv2.drawContours(im, [approx], -1, (0, 255, 0), 2)
                dp = np.squeeze(approx)

                if len(dp) == 4:
                    # Ensure points are in a consistent order (e.g., top-left, top-right, bottom-right, bottom-left)
                    # This simple sorting works for convex quadrilaterals but might need refinement
                    # for more complex cases. Summing coordinates helps sort TL/BR, diff helps sort TR/BL.
                    s = dp.sum(axis=1)
                    diff = np.diff(dp, axis=1)

                    src_pts = np.float32(
                        [
                            dp[np.argmin(s)],  # Top-left point has smallest sum
                            dp[np.argmin(diff)],  # Top-right point has smallest difference
                            dp[np.argmax(s)],  # Bottom-right point has largest sum
                            dp[np.argmax(diff)],  # Bottom-left point has largest difference
                        ]
                    )

                    dst_pts = np.float32(
                        [
                            [0, 0],  # Top-left
                            [w - 1, 0],  # Top-right
                            [w - 1, h - 1],  # Bottom-right
                            [0, h - 1],  # Bottom-left
                        ]
                    )

                    matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
                    succeed = True
                    break

        if debug:
            if succeed:
                perspective_img = cv2.warpPerspective(frame, matrix, (w, h))

            cv2.imshow("Calibrate", im)
            cv2.imshow("PerspectiveTransform", perspective_img)  # Show the result (transformed or black)
            cv2.waitKey(10)

        return {"pt_matrix": matrix if succeed else None}
