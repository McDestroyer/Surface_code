"""Provides an interface for a game controller."""

import time
import pygame
from pygame.locals import *


def map_ranges(x, from_range, to_range):
    """Interpolates a value from one range to another.

    Args:
        x (float): the value to interpolate
        from_range (tuple[int, int]): (min, max) for input range
        to_range (tuple[int, int]): (min, max) for output range

    Returns:
        float: the interpolated value
    """
    delta_y = to_range[1] - to_range[0]
    delta_x = from_range[1] - from_range[0]
    slope = delta_y / delta_x
    return slope * (x - from_range[0]) + to_range[0]


def squeeze(x, _min, _max, deadband=0.1):
    """Make sure a value is within a certain range and above a certain threshhold.

    Args:
        x (float): the value to squeeze
        _min (float): the minimum value
        _max (float): the maximum value
        deadband (float): the deadband

    Returns:
        float: the squeezed value
    """
    x = min(max(x, _min), _max)
    if abs(x) > deadband:
        return x
    return 0


class RawController:
    """An unfiltered interface for a pygame controller"""

    def __init__(self):
        pygame.init()

        self.joystick = pygame.joystick.Joystick(0)

    def update(self):
        for event in pygame.event.get():
            pass

    def get_left(self):
        return self.joystick.get_axis(0), self.joystick.get_axis(1)

    def get_right(self):
        return self.joystick.get_axis(2), self.joystick.get_axis(3)

    def quit(self):
        pygame.quit()


class Controller:
    """An interface for a configurable pygame controller."""

    def __init__(self, config=None):
        self.cont = RawController()

        self.left_x_center = 0.0
        self.left_y_center = 0.0

        self.right_x_center = 0.0
        self.right_y_center = 0.0

        self.left_x_range = [-1.0, 1.0]
        self.left_y_range = [-1.0, 1.0]

        self.right_x_range = [-1.0, 1.0]
        self.right_y_range = [-1.0, 1.0]

        if config is not None:
            self.load_config(config)

    def dump_config(self):
        """Dumps the configuration of the controller.

        Returns:
            dict[str, float]: configuration relationships
        """
        return {
            "left_x_center": self.left_x_center,
            "left_y_center": self.left_y_center,
            "right_x_center": self.right_x_center,
            "right_y_center": self.right_y_center,
            "left_x_range": self.left_x_range,
            "left_y_range": self.left_y_range,
            "right_x_range": self.right_x_range,
            "right_y_range": self.right_y_range,
        }

    def load_config(self, config):
        """Load configuration from a dictionary.

        Args:
            config (dict[str, float]): config relationships
        """
        self.left_x_center = config["left_x_center"]
        self.left_y_center = config["left_y_center"]

        self.right_x_center = config["right_x_center"]
        self.right_y_center = config["right_y_center"]

        self.left_x_range = config["left_x_range"]
        self.left_y_range = config["left_y_range"]

        self.right_x_range = config["right_x_range"]
        self.right_y_range = config["right_y_range"]

    def update(self):
        """Tick controller readings."""
        self.cont.update()

    def config(self):
        """Run a configuration utility."""
        print("Press forward on both sticks...")
        while not (
            self.cont.get_left()[0]
            and self.cont.get_left()[1]
            and self.cont.get_right()[0]
            and self.cont.get_left()[1]
        ):
            self.update()

        time.sleep(2.0)
        print("Release both sticks.")
        time.sleep(1.0)

        self.left_x_center = 0
        self.left_y_center = 0

        self.right_x_center = 0
        self.right_y_center = 0

        for _ in range(20):
            self.update()
            self.left_x_center += self.cont.get_left()[0]
            self.left_y_center += self.cont.get_left()[1]

            self.right_x_center += self.cont.get_right()[0]
            self.right_y_center += self.cont.get_right()[1]
            time.sleep(0.1)

        self.left_x_center /= 20
        self.left_y_center /= 20

        self.right_x_center /= 20
        self.right_y_center /= 20

        print("Center set.")
        print("Left X: {:.10f}".format(self.left_x_center))
        print("Left Y: {:.10f}".format(self.left_y_center))
        print("Right X: {:.10f}".format(self.right_x_center))
        print("Right Y: {:.10f}".format(self.right_y_center))

        self.left_x_range = [float("inf"), -float("inf")]
        self.left_y_range = [float("inf"), -float("inf")]

        self.right_x_range = [float("inf"), -float("inf")]
        self.right_y_range = [float("inf"), -float("inf")]

        print("Sweep both around in full circles for 10 seconds.")

        start = time.time()

        while time.time() - start < 10:
            self.update()
            left = self.cont.get_left()
            right = self.cont.get_right()

            left_x = left[0] - self.left_x_center
            left_y = left[1] - self.left_y_center

            right_x = right[0] - self.right_x_center
            right_y = right[1] - self.right_y_center

            if left_x > self.left_x_range[1]:
                self.left_x_range[1] = left_x
            if left_x < self.left_x_range[0]:
                self.left_x_range[0] = left_x

            if left_y > self.left_y_range[1]:
                self.left_y_range[1] = left_y
            if left_y < self.left_x_range[0]:
                self.left_y_range[0] = left_y

            if right_x > self.right_x_range[1]:
                self.right_x_range[1] = right_x
            if right_x < self.left_x_range[0]:
                self.right_x_range[0] = right_x

            if right_y > self.right_y_range[1]:
                self.right_y_range[1] = right_y
            if right_y < self.right_y_range[0]:
                self.right_y_range[0] = right_y

            time.sleep(0.02)

        print("New ranges:")
        print("Left x:", self.left_x_range)
        print("Right x:", self.right_x_range)
        print("Left x:", self.left_x_range)
        print("Right x:", self.right_x_range)

    def get(self):
        """Get current state of the controller."""
        left = self.cont.get_left()
        right = self.cont.get_right()

        left_x = left[0] - self.left_x_center
        left_y = left[1] - self.left_y_center

        right_x = right[0] - self.right_x_center
        right_y = right[1] - self.right_y_center

        left_x = map_ranges(left_x, self.left_x_range, (-1.0, 1.0))
        left_y = map_ranges(left_y, self.left_y_range, (-1.0, 1.0))

        right_x = map_ranges(right_x, self.right_x_range, (-1.0, 1.0))
        right_y = map_ranges(right_y, self.right_y_range, (-1.0, 1.0))
        
        deadzone = .15

        return {
            "left_x": squeeze(left_x, -1.0, 1.0, deadzone),
            "left_y": squeeze(left_y, -1.0, 1.0, deadzone),
            "right_x": squeeze(right_x, -1.0, 1.0, deadzone),
            "right_y": squeeze(right_y, -1.0, 1.0, deadzone),
            "triggers": combine_triggers(self.cont.joystick.get_axis(4), self.cont.joystick.get_axis(5)),
            "a": self.cont.joystick.get_button(0),
            "b": self.cont.joystick.get_button(1),
            "x": self.cont.joystick.get_button(2),
            "y": self.cont.joystick.get_button(3),
        }


def combine_triggers(trigger_1: float, trigger_2: float) -> float:
    """Combines the values of the two triggers into a single value.

    Args:
        trigger_1 (float):
            The value of the first trigger.
        trigger_2 (float):
            The value of the second trigger.

    Returns:
        float: The combined value of the triggers.
    """
    trigger_1 = (trigger_1 + 1) / 2
    trigger_2 = (trigger_2 + 1) / 2

    return trigger_2 - trigger_1
