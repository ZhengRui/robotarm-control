import time
from typing import Any, Dict, List, Optional, Tuple

from pymycobot import MyCobot280, MyCobot280Socket
from pymycobot.genre import Coord

from ....handlers import BaseHandler
from ....utils.logger import get_logger

logger = get_logger("armcontrol")


class ArmControlHandler(BaseHandler):
    def __init__(
        self,
        remote_addr: Optional[str] = None,
        remote_port: Optional[int] = 9000,
        port: str = "/dev/ttyUSB0",
        baudrate: int = 1000000,
        task: str = "pick_and_place",
        grasp_offset: Tuple[float, float] = (-0.02, -0.005),
        init_angles: List[int] = [43, 0, 0, -80, -6, -6],
        coord_config: Dict[str, Any] = {
            "pre_grasp_z": 180,
            "grasp_z": 130,
            "post_grasp_z": 250,
            "place": {
                "red": [75, 230, 130, -175, 0, -45],
                "green": [10, 230, 130, -175, 0, -45],
                "blue": [-70, 230, 130, -175, 0, -45],
                "yellow": [140, 230, 130, -175, 0, -45],
            },
            "stack": {"first": [135, -155, 130, -175, 0, -45], "delta_z": 30},
        },
        gripper_config: Dict[str, int] = {
            "open": 100,
            "close": 20,
        },
    ) -> None:
        self.task = task
        self.grasp_offset = grasp_offset
        self.mc = MyCobot280Socket(remote_addr, remote_port) if remote_addr else MyCobot280(port, baudrate)
        self.init_angles = init_angles
        self.coord_config = coord_config
        self.gripper_config = gripper_config
        self._reset()

    def _reset(self) -> None:
        self.mc.send_angles(self.init_angles, 30)
        time.sleep(0.5)

    def _move_to_coord(
        self,
        x: float,
        y: float,
        z: float,
        rx: float = -175,
        ry: float = 0,
        rz: float = -45,
        speed: int = 40,
        delay: float = 1,
    ) -> None:
        coords = [x, y, z, rx, ry, rz]
        self.mc.send_coords(coords, speed, 0)
        time.sleep(delay)

    def _move_to_z(self, z: float, speed: int = 40, delay: float = 1) -> None:
        self.mc.send_coord(Coord.Z.value, z, speed)
        time.sleep(delay)

    def _set_gripper_value(self, value: int, speed: int = 40, delay: float = 1) -> None:
        self.mc.set_gripper_value(value, speed)
        time.sleep(delay)

    def process(
        self,
        objects: List[Dict[str, Any]],
        speed: int = 40,
        delay: float = 1,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        done: List[Dict[str, Any]] = []
        failed: List[Dict[str, Any]] = []

        for obj in objects:
            label = obj["label"]
            cx, cy = obj["center"]

            if cx > 0.275:
                logger.info(f"{label} at {cx:.3f}, {cy:.3f} unreachable")
                failed.append(obj)
                continue

            logger.info(f"Moving to {label} at {cx:.3f}, {cy:.3f}")
            cx += self.grasp_offset[0]
            cy += self.grasp_offset[1]

            cx *= 1000
            cy *= 1000

            self._move_to_coord(cx, cy, self.coord_config["pre_grasp_z"], speed=speed, delay=delay)

            self._set_gripper_value(self.gripper_config["open"], speed=speed, delay=delay)

            self._move_to_coord(cx, cy, self.coord_config["grasp_z"], speed=speed, delay=delay)

            self._set_gripper_value(self.gripper_config["close"], speed=speed, delay=delay)

            self._move_to_coord(cx, cy, self.coord_config["post_grasp_z"], speed=speed, delay=delay)

            if self.task == "pick_and_place":
                coords = self.coord_config["place"][label]
            elif self.task == "pick_and_stack":
                coords = self.coord_config["stack"]["first"].copy()
                coords[2] += self.coord_config["stack"]["delta_z"] * len(done)

            x, y, z, rx, ry, rz = coords

            self._move_to_coord(x, y, self.coord_config["pre_grasp_z"], speed=speed, delay=delay)

            self._move_to_coord(x, y, z, rx, ry, rz, speed=speed, delay=delay)

            self._set_gripper_value(self.gripper_config["open"], speed=speed, delay=delay)

            self._move_to_coord(x, y, z + 50, rx, ry, rz, speed=speed, delay=delay)

            self._reset()

            done.append(obj)

        return {"done": done, "failed": failed}
