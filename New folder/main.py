"""Send a Raspberry Pi commands from joystick."""

import json
import socket
import time
from pi_connection import PiConnection
from controller import Controller
from thruster_pwm import lateral_thruster_calc, thruster_mask_dict
from serial_manager import SerialManager

class Main:
    """Exists so I can use self vars"""

    def __init__(self) -> None:
        self.joy = Controller()
        self.ser = SerialManager()
        self.pi = PiConnection()

        self.instantaneous_controls = {
            "a": 0,
            "b": 0,
            "x": 0,
            "y": 0,
            "left_bumper": 0,
            "right_bumper": 0,
            "back": 0,
            "start": 0,
            "home": 0,
            "left_joystick_click": 0,
            "right_joystick_click": 0,
            "up": 0,
            "down": 0,
            "left": 0,
            "right": 0,
        }

        self.button_toggles = {
            "a": False,
            "b": False,
            "x": False,
            "y": False,
            "left_bumper": False,
            "right_bumper": False,
            "back": False,
            "start": False,
            "home": False,
            "left_joystick_click": False,
            "right_joystick_click": False,
            "up": False,
            "down": False,
            "left": False,
            "right": False,
        }

    def main(self):
        """Main"""
        while True:
            # Update controller.
            self.joy.update()
            controls = self.joy.get()

            # Handle controller input.
            self.handle_input(controls)
            thrust = lateral_thruster_calc(controls["left_x"], controls["left_y"], controls["right_x"])

            # Assemble data to send to Pi.
            data = thrust.get_pwm(controls["triggers"], -controls["right_y"])
            # For testing purposes only output manual thruster values.
            # data = {
            #     "fr": 1900,  # 5.0-5.1? Amps
            #     "fl": 1900,  # 5.0 Amps
            #     "rr": 1900,  # 5.3 Amps
            #     "rl": 1900,  # 5.2 Amps
            #     "fv": 1500,  #  Amps
            #     "rv": 1500,  #  Amps
            # }
            data["msg"] = []
            data["restart"] = False

            # Send data to Pi.
            self.pi.send(json.dumps(data).encode())

            # Print data.
            # print("Left X:", controls["left_x"], "Left Y:", controls["left_y"], "Right X:", controls["right_x"],
            #       "Right Y:", controls["right_y"], "controls["triggers"]:", controls["triggers"])
            # print(self.pi.recv(), "LX:", round(controls["left_x"], 5), "LY:", round(controls["left_y"], 5), "RX:", round(controls["right_x"], 5), "RY:", round(controls["right_y"], 5))

    def handle_input(self, controls: dict) -> None:
        """Handle input from the controller."""

        if controls["a"]:
            if not self.instantaneous_controls["a"]:
                # Fire on press
                pass
        elif self.instantaneous_controls["a"]:
            # Fire on release
            pass

        if controls["b"]:
            pass
        if controls["x"]:
            pass
        if controls["y"]:
            pass

        # Thruster mask hot modification.
        mod_inc = .05

        # If left bumper is pressed, decrease thruster mask values.
        if controls["left_bumper"] and not self.instantaneous_controls["left_bumper"]:
            if controls["up"]:
                if controls["right"]:
                    thruster_mask_dict["fr"] = max(
                        thruster_mask_dict["fr"] - mod_inc, -1)
                elif controls["left"]:
                    thruster_mask_dict["fl"] = max(
                        thruster_mask_dict["fl"] - mod_inc, -1)
                else:
                    thruster_mask_dict["fv"] = max(
                        thruster_mask_dict["fv"] - mod_inc, -1)
            elif controls["down"]:
                if controls["right"]:
                    thruster_mask_dict["rr"] = max(
                        thruster_mask_dict["rr"] - mod_inc, -1)
                elif controls["left"]:
                    thruster_mask_dict["rl"] = max(
                        thruster_mask_dict["rl"] - mod_inc, -1)
                else:
                    thruster_mask_dict["rv"] = max(
                        thruster_mask_dict["rv"] - mod_inc, -1)
            else:
                thruster_mask_dict["power_multiplier"] = max(
                    power_multiplier - mod_inc, 0)

        # If right bumper is pressed, increase thruster mask values.
        elif controls["right_bumper"] and not self.instantaneous_controls["right_bumper"]:
            if controls["up"]:
                if controls["right"]:
                    thruster_mask_dict["fr"] = min(
                        thruster_mask_dict["fr"] + mod_inc, 1)
                elif controls["left"]:
                    thruster_mask_dict["fl"] = min(
                        thruster_mask_dict["fl"] + mod_inc, 1)
                else:
                    thruster_mask_dict["fv"] = min(
                        thruster_mask_dict["fv"] + mod_inc, 1)
            elif controls["down"]:
                if controls["right"]:
                    thruster_mask_dict["rr"] = min(
                        thruster_mask_dict["rr"] + mod_inc, 1)
                elif controls["left"]:
                    thruster_mask_dict["rl"] = min(
                        thruster_mask_dict["rl"] + mod_inc, 1)
                else:
                    thruster_mask_dict["rv"] = min(
                        thruster_mask_dict["rv"] + mod_inc, 1)
            else:
                thruster_mask_dict["power_multiplier"] = min(power_multiplier + mod_inc, 1)

        # Print thruster mask to show changes.
        if ((controls["left_bumper"] and not self.instantaneous_controls["left_bumper"]) or
            (controls["right_bumper"] and not self.instantaneous_controls["right_bumper"])):
            print(thruster_mask_dict)

        # Update instantaneous controls (NOTE: Must be performed after all uses).
        for key in self.instantaneous_controls:
            self.instantaneous_controls[key] = controls[key]

    def __del__(self):
        self.ser.close()
        self.pi.close()

if __name__ == "__main__":
    while True:
        main_system = None
        try:
            main_system = Main()
            main_system.main()
        except socket.timeout:
            print("Socket timed out. Trying again...")
        except KeyboardInterrupt:
            print("Keyboard interrupted. Shutting down...")
            data = {
                "fr": 1500,
                "fl": 1500,
                "rr": 1500,
                "rl": 1500,
                "fv": 1500,
                "rv": 1500,
                "msg": [],
                "restart": True,
            }
            main_system.pi.send(json.dumps(data).encode())
            print(main_system.pi.recv())
            time.sleep(.5)
            main_system.pi.close()
            break
        except ConnectionResetError:
            print("Connection reset. Restarting...")
            main_system.pi.close()
