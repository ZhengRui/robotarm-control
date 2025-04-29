import os
import re
import shutil
import sys
from typing import Generator, List, Tuple, Union

import cv2
import numpy as np

from .logger import get_logger

VIDEO_SUFFIX: Tuple[str, ...] = (".mp4", ".avi")
IMAGE_SUFFIX: Tuple[str, ...] = (".jpg", ".jpeg", ".png")

logger = get_logger("factory")


def sorted_alphanumeric(data: List[str]) -> List[str]:
    def convert(text: str) -> Union[int, str]:
        return int(text) if text.isdigit() else text.lower()

    def alphanum_key(key: str) -> List[Union[int, str]]:
        return [convert(c) for c in re.split("([0-9]+)", key)]

    return sorted(data, key=alphanum_key)


class DataFactory:
    def __init__(self, source: str):
        try:
            if source.startswith(("http://", "https://")):
                if source.endswith(IMAGE_SUFFIX):
                    import requests

                    resp = requests.get(source, stream=True, timeout=5)
                    resp.raise_for_status()

                    tmp_source = "/tmp/segrec/source.jpg"
                    with open(tmp_source, "wb") as of:
                        try:
                            shutil.copyfileobj(resp.raw, of)
                            self.source: Union[List[str], cv2.VideoCapture] = [tmp_source]
                            self.type: str = "image"
                        except Exception:
                            if os.path.exists(tmp_source):
                                os.remove(tmp_source)
                            raise Exception(f"not able to download image from {source}")

                else:
                    # extract url using youtube_dl
                    # ref:
                    # 1. https://stackoverflow.com/questions/50876292/
                    #    opencv-capture-online-video-for-further-processing-without-downloading-the-file/
                    #    50881927#50881927
                    # 2. https://github.com/ytdl-org/youtube-dl/blob/master/docs/module_guide.rst

                    import youtube_dl

                    ydl_opts = {}  # type: ignore
                    ydl = youtube_dl.YoutubeDL(ydl_opts)
                    info_dict = ydl.extract_info(source, download=False)

                    # find the url the corresponds to best video resolution
                    formats = info_dict.get("formats")

                    if formats is None:
                        raise Exception(f"youtube-dl not able to extract info of {source}")

                    urls: List[Tuple[int, str, int, str]] = []
                    for fmt in formats:
                        height, width, ext, url = (
                            fmt.get("height"),
                            fmt.get("width"),
                            fmt.get("ext"),
                            fmt.get("url"),
                        )
                        if height and width and ext and url:
                            urls.append((height, ext, width, url))
                    urls = sorted(urls, key=lambda x: (x[0], x[1]), reverse=True)

                    self.type = "video"

                    init_succeed = False
                    for height, ext, width, stream_url in urls:
                        self.source = cv2.VideoCapture(stream_url)
                        if self.source.isOpened():
                            init_succeed = True
                            logger.info(f"find usable stream: {height}x{width} {ext}")
                            break

                    if not init_succeed:
                        raise Exception(f"opencv not able to load any stream source of {source}")

            elif source.lower().startswith("webcam"):
                cam_id = source.split(":")[1] if ":" in source else 0
                self.type = "video"
                self.source = cv2.VideoCapture(int(cam_id))

            else:
                assert os.path.exists(source), "Source does not exists!"

                if os.path.isfile(source):
                    if source.lower().endswith(VIDEO_SUFFIX):
                        self.type = "video"
                        self.source = cv2.VideoCapture(source)
                    elif source.lower().endswith(IMAGE_SUFFIX):
                        self.type = "image"
                        self.source = [source]
                    else:
                        raise Exception("Invalid source!")

                if os.path.isdir(source):
                    fs = [os.path.join(source, f) for f in os.listdir(source) if f.lower().endswith(IMAGE_SUFFIX)]
                    if len(fs):
                        self.type = "image"
                        self.source = sorted_alphanumeric(fs)
                    else:
                        raise Exception("Invalid source!")

        except Exception as err:
            logger.error(err)
            sys.exit(1)

    def pipeline(
        self, keep_size: bool = True, max_size: int = 800, lossy: bool = True, jpg_quality: int = 50
    ) -> Generator[bytes, None, None]:
        if self.type == "image":
            for i_frame, img_path in enumerate(self.source):  # type: ignore
                try:
                    im = cv2.imread(img_path, cv2.IMREAD_COLOR)
                    assert im.size

                    if not keep_size:
                        h, w = im.shape[:2]
                        s = min(max_size / w, max_size / h)
                        im = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)

                    msg = encode(im, i_frame=i_frame, lossy=lossy, jpg_quality=jpg_quality)

                    yield msg

                except Exception as err:
                    logger.error(f"Reading Error {img_path} {err}, skipped!")

        elif self.type == "video":
            i_frame = 0
            while True:
                try:
                    ret, im = self.source.read()  # type: ignore
                    if ret:
                        assert im.size

                        if not keep_size:
                            h, w = im.shape[:2]
                            s = min(max_size / w, max_size / h)
                            im = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)

                        msg = encode(im, i_frame=i_frame, lossy=lossy, jpg_quality=jpg_quality)
                        i_frame += 1

                        yield msg
                    else:
                        break

                except Exception as err:
                    logger.error(f"Reading Error {i_frame} {err}, skipped!")


def encode(im: np.ndarray, i_frame: int = 0, lossy: bool = True, jpg_quality: int = 50) -> bytes:
    assert im.size and im.dtype == np.uint8
    h, w = im.shape[:2]

    if lossy:
        _, im = cv2.imencode(
            ".jpg",
            im,
            [int(cv2.IMWRITE_JPEG_QUALITY), jpg_quality],
        )

    msg = f"{i_frame:010d}{h:010d}{w:010d}{lossy:010d}".encode() + im.tobytes()
    return msg


def decode(msg: bytes) -> Tuple[int, np.ndarray]:
    i_frame, h, w, encoded, im_buf = int(msg[:10]), int(msg[10:20]), int(msg[20:30]), bool(int(msg[30:40])), msg[40:]

    if encoded:
        im = cv2.imdecode(np.frombuffer(im_buf, dtype="uint8"), cv2.IMREAD_COLOR)
        assert im.shape[:2] == (h, w)
    else:
        im = np.frombuffer(im_buf, dtype="uint8").reshape(h, w, -1)

    return i_frame, im
