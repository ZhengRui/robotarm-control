import time
from typing import Any, Dict, List, Tuple

from pymycobot import MyCobot280
from pymycobot.genre import Coord

from ..utils.logger import get_logger

logger = get_logger("armcontrol")


class ArmControlHandler:
    def __init__(self, name: str = "yahboom", **kwargs: Any) -> None:
        if name == "yahboom":
            self.handler = YahboomArmControlHandler(**kwargs)

    def process(self, objects: List[Dict[str, Any]], debug: bool = False, **kwargs: Any) -> Dict[str, Any]:
        return self.handler.process(objects, debug=debug, **kwargs)


class YahboomArmControlHandler:
    def __init__(
        self,
        task: str = "pick_and_place",
        grasp_offset: Tuple[float, float] = (0.005, 0),
        init_angles: List[int] = [39, 0, 0, -71, -8, -8],
        coord_config: Dict[str, Any] = {
            "pre_grasp_z": 170,
            "grasp_z": 115,
            "post_grasp_z": 170,
            "place": {
                "red": [75, 230, 115, -175, 0, -45],
                "green": [10, 230, 115, -175, 0, -45],
                "blue": [-70, 230, 115, -175, 0, -45],
                "yellow": [140, 230, 115, -175, 0, -45],
            },
            "stack": {"first": [135, -155, 115, -175, 0, -45], "delta_z": 30},
        },
        gripper_config: Dict[str, int] = {
            "open": 100,
            "close": 20,
        },
    ) -> None:
        self.task = task
        self.grasp_offset = grasp_offset
        self.mc = MyCobot280(port="/dev/ttyUSB0", baudrate=1000000)
        self.init_angles = init_angles
        self.coord_config = coord_config
        self.gripper_config = gripper_config
        self._reset()

    def _reset(self) -> None:
        self.mc.send_angles(self.init_angles, 40)
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
                logger.info(f"{label} at {cx:.2f}, {cy:.2f} unreachable")
                failed.append(obj)
                continue

            logger.info(f"Moving to {label} at {cx:.2f}, {cy:.2f}")
            cx += self.grasp_offset[0]
            cy += self.grasp_offset[1]

            self._move_to_coord(cx, cy, self.coord_config["pre_grasp_z"], speed=speed, delay=delay)

            self._move_to_z(self.coord_config["grasp_z"], speed=speed, delay=delay)

            self._set_gripper_value(self.gripper_config["close"], speed=speed, delay=delay)

            self._move_to_z(self.coord_config["post_grasp_z"], speed=speed, delay=delay)

            if self.task == "pick_and_place":
                coords = self.coord_config["place"][label]
            elif self.task == "pick_and_stack":
                coords = self.coord_config["stack"]["first"]
                coords[2] += self.coord_config["stack"]["delta_z"] * (len(done) - 1)

            x, y, z, rx, ry, rz = coords

            self._move_to_coord(x, y, z, rx, ry, rz, speed=speed, delay=delay)

            self._set_gripper_value(self.gripper_config["open"], speed=speed, delay=delay)

            self._move_to_coord(x, y, z + 30, rx, ry, rz, speed=speed, delay=delay)

            self._reset()

            done.append(label)

        return {"done": done, "failed": failed}
