import json
from logging import get_logger

import imagezmq

from utils.message import decode

logger = get_logger("server")


def serv():
    hub = imagezmq.ImageHub()

    while True:
        try:
            rpi_name, msg = hub.recv_jpg()
            _, frame = decode(msg.bytes)
            assert frame.size
        except Exception as err:
            logger.warning(f"Communication Error {err}!")

        # image processing
        res = "frame result"
        hub.send_reply(json.dumps(res).encode("utf-8"))


if __name__ == "__main__":
    serv()
