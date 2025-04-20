import cv2

from utils.logger import get_logger

logger = get_logger("calibrate")


class CalibrateHandler:
    def __init__(self):
        self.wnd_size = None

    def process(self, frame):
        if not self.wnd_size or self.wnd_size != frame.shape[:2]:
            logger.info(f"Resizing window to {frame.shape[1]}x{frame.shape[0]}")
            cv2.namedWindow("Calibrate", cv2.WINDOW_GUI_NORMAL)
            cv2.resizeWindow("Calibrate", frame.shape[1], frame.shape[0])
            self.wnd_size = frame.shape[:2]

        cv2.imshow("Calibrate", frame)
        cv2.waitKey(10)

        return

    @staticmethod
    def visualize(frame, res):
        return frame.copy()
