import argparse
import json
import os
import socket
import time

import cv2
import imagezmq

from utils.factory import Factory, decode
from utils.load_handler import load_handler
from utils.logger import get_logger

logger = get_logger("streaming")


def stream(args):
    source, server = args.source, args.server
    max_size, keep_size = args.max_size, args.keep_size
    lossy, jpg_quality = args.lossy, args.jpg_quality
    autoplay, enable_freeze, write_to = args.autoplay, args.enable_freeze, args.write_to

    if write_to:
        assert os.path.exists(write_to)

    factory = Factory(source)
    client = imagezmq.ImageSender(connect_to=f"tcp://{server}:5555")
    rpi_name = socket.gethostname()

    fps, i_frame, d_frame = 0, 0, 10
    t0 = time.time()
    t_wait = 0 if (factory.type == "image" and not autoplay) else 10
    cv2.namedWindow("Demo", cv2.WINDOW_GUI_NORMAL)
    wnd_resized = False
    handler = load_handler(args.handler) if args.handler else None
    is_paused = False  # Flag to track pause state

    display_file_name = args.display_file_name and factory.type == "image"

    for msg in factory.pipeline(keep_size=keep_size, max_size=max_size, lossy=lossy, jpg_quality=jpg_quality):
        try:
            reply = client.send_jpg(rpi_name, msg)
            res = json.loads(reply)

        except Exception as err:
            logger.warning(f"Communication Error {err}!")

        i_frame += 1
        if not i_frame % d_frame:
            t1 = time.time()
            fps = d_frame / (t1 - t0)
            t0 = t1

        _, im = decode(msg)
        if handler:
            im = handler.visualize(im, res)
        h, w = im.shape[:2]

        if display_file_name:
            sourcePath = factory.source[i_frame - 1]
            fileName = sourcePath.split(source)

        cv2.putText(
            im,
            f"{fps:3.1f}fps {h}x{w} {fileName[1] if display_file_name else rpi_name}",
            (10, 25),
            cv2.FONT_HERSHEY_DUPLEX,
            0.4,
            (0, 255, 255),
            1,
        )

        if write_to:
            if factory.type == "image":
                savename = os.path.basename(factory.source[i_frame - 1])
            else:
                savename = f"{i_frame - 1:04d}.jpg"

            cv2.imwrite(
                os.path.join(write_to, savename),
                im,
                [int(cv2.IMWRITE_JPEG_QUALITY), 100],
            )

        cv2.imshow("Demo", im)
        if factory.type == "image" or not wnd_resized:
            cv2.resizeWindow("Demo", (w, h))
            wnd_resized = True

        key = cv2.waitKey(0 if enable_freeze and is_paused else t_wait) & 0xFF
        if key == ord("q"):
            break
        elif key == ord(" ") and enable_freeze:  # Space key to toggle pause when enable_freeze is true
            is_paused = not is_paused
            logger.info("Stream " + ("paused" if is_paused else "resumed"))

    cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video Prototyping Client")
    parser.add_argument("--server", type=str, default="127.0.0.1", help="Server Ip")
    parser.add_argument(
        "--source",
        type=str,
        required=True,
        help="ImageFilePath or VideoFilePath or Webcam",
    )
    parser.add_argument("--max_size", type=int, default=800, help="Maximum size of the longer side")
    parser.add_argument(
        "--keep_size",
        dest="keep_size",
        action="store_true",
        help="Keep frames original size",
    )
    parser.add_argument(
        "--jpg_quality",
        type=int,
        default=50,
        help="JPG Quality (1, 100], the higher the better quality, the less compression",
    )
    parser.add_argument(
        "--lossless",
        dest="lossy",
        action="store_false",
        help="Send raw frames (pixelmap) to server",
    )
    parser.add_argument(
        "--autoplay",
        dest="autoplay",
        action="store_true",
        help="Autoplay on image sources",
    )
    parser.add_argument(
        "--enable_freeze",
        dest="enable_freeze",
        action="store_true",
        help="Pause when the predictor's freeze condition is satisfied",
    )
    parser.add_argument(
        "--write_to",
        type=str,
        default=None,
        help="Write visulized results to the specified folder",
    )
    parser.add_argument(
        "--display_file_name",
        dest="display_file_name",
        action="store_true",
        help="Display file name in image output",
    )
    parser.add_argument(
        "--handler",
        type=str,
        default=None,
        help="Handler to process the frame and visualize the result",
    )

    args = parser.parse_args()
    stream(args)
