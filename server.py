import json

import imagezmq

from utils.factory import decode
from utils.logger import get_logger

logger = get_logger("server")


def serv():
    hub = imagezmq.ImageHub()

    try:
        while True:
            try:
                rpi_name, msg = hub.recv_jpg()
                i_frame, frame = decode(msg.bytes)
                assert frame.size
            except Exception as err:
                logger.warning(f"Communication Error {err}!")
                continue  # Continue listening even if one message fails

            # if i_frame % 100 == 0:
            #     logger.info(f"{rpi_name} {i_frame}th frame: {frame.shape}")

            # image processing
            res = "frame result"
            hub.send_reply(json.dumps(res).encode("utf-8"))
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, shutting down server.")
    finally:
        hub.close()


if __name__ == "__main__":
    serv()
