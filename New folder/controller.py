"""Provides an interface for a game controller."""

import pygame

class Controller:
    """An interface for a configurable pygame controller."""

    def __init__(self):
        pygame.init()
        self.joystick = pygame.joystick.Joystick(0)
        self.deadzone = 0.15

    def get(self) -> dict:
        """Get current state of the controller.

        Returns:
            dict: The current state of the controller.

            Example:
            {
                "left_x": 0.0,
                "left_y": 0.0,
                "right_x": 0.0,
                "right_y": 0.0,
                "triggers": 0.0,
                "a": 0,
                "b": 0,
                "x": 0,
                "left_bumper": 0,
                "right_bumper": 0,
                "back": 0,
                "start": 0,
                "home": 0,
                "left_joystick_click": 0,
                "right_joystick_click": 0,
                "hat": (0, 0),
            }"""
        self.update()

        hat = self.joystick.get_hat(0)

        return {
            "left_x": self.axis(0),
            "left_y": self.axis(1),
            "right_x": self.axis(2),
            "right_y": self.axis(3),
            "triggers": combine_triggers(self.axis(4), self.axis(5)),
            "a": self.button(0),
            "b": self.button(1),
            "x": self.button(2),
            "left_bumper": self.button(3),
            "right_bumper": self.button(4),
            "back": self.button(5),
            "start": self.button(6),
            "home": self.button(7),
            "left_joystick_click": self.button(8),
            "right_joystick_click": self.button(9),
            "up": 1 if hat[1] == 1 else 0,
            "down": 1 if hat[1] == -1 else 0,
            "left": 1 if hat[0] == -1 else 0,
            "right": 1 if hat[0] == 1 else 0,
        }

    def axis(self, axis: int) -> float:
        """Get the value of a specific axis.
        
        Args:
            axis (int):
                The axis to get the value of.

        Returns:
            float: The value of the axis."""
        return apply_deadzone(self.joystick.get_axis(axis), self.deadzone)

    def button(self, button: int) -> bool:
        """Get the value of a specific button.
        
        Args:
            button (int):
                The button to get the value of.

        Returns:
            bool: The value of the button."""
        return 1 if self.joystick.get_button(button) else 0

    def update(self):
        """Update the controller state by clearing the event queue."""
        pygame.event.get()
        # Not sure why you bothered looping through the events, but left it here just in case.
        # for _ in pygame.event.get():
        #     pass

    def quit(self):
        """Quit the controller."""
        pygame.quit()

    def __del__(self):
        self.quit()


def apply_deadzone(value: float, deadzone: float = 0.15) -> float:
    """Apply a deadzone to the controller input.
    
    Args:
        value (float):
            The value to apply the deadzone to.
        deadzone (float, optional):
            The deadzone value.
            Defaults to 0.15.

    Returns:
        float: The value after applying the deadzone."""
    if abs(value) < deadzone:
        return 0
    return value


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
