"""Send a Raspberry Pi commands from joystick."""

import json
import socket
import time
from pi_connection import PiConnection
from controller import Controller
from thruster_pwm import FrameThrusters
from serial_manager import SerialManager

class Main:
    """Exists so I can use self vars"""

    def __init__(self) -> None:
        self.joy = Controller()
        self.ser = SerialManager()
        self.pi = PiConnection()
        self.thrusters = FrameThrusters()

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

        self.ctrl_invert_mask = 1

    def main(self):
        """Main"""
        while True:
            # Update controller.
            self.joy.update()
            controls = self.joy.get()

            # Handle controller input.
            self.handle_input(controls)
            self.thrusters.thrust_calc(
                controls["left_x"] * self.ctrl_invert_mask,
                controls["left_y"] * self.ctrl_invert_mask,
                controls["triggers"],
                controls["right_y"] * self.ctrl_invert_mask,
                controls["right_x"]
            )

            # Assemble data to send to Pi.
            data = self.thrusters.get_pwm()
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
            # Run auto code.
            pass
        if controls["x"]:
            if not self.instantaneous_controls["x"]:
                self.ctrl_invert_mask *= -1
                if self.ctrl_invert_mask == 1:
                    print("Controls are normal.")
                else:
                    print("Controls are inverted.")
        if controls["y"]:
            pass

        # Thruster mask hot modification.
        mod_inc = .05
        modded_thrusters = False

        # If left bumper is pressed, decrease thruster mask values.
        if controls["left_bumper"] and not self.instantaneous_controls["left_bumper"]:
            modded_thrusters = True
            # Front motors: fr, fl, fv
            if controls["up"]:
                if controls["right"]:
                    self.thrusters.fr.set_power(self.thrusters.fr.get_power() - mod_inc)
                elif controls["left"]:
                    self.thrusters.fl.set_power(self.thrusters.fl.get_power() - mod_inc)
                else:
                    self.thrusters.fv.set_power(self.thrusters.fv.get_power() - mod_inc)
            # Rear motors: rr, rl, rv
            elif controls["down"]:
                if controls["right"]:
                    self.thrusters.rr.set_power(self.thrusters.rr.get_power() - mod_inc)
                elif controls["left"]:
                    self.thrusters.rl.set_power(self.thrusters.rl.get_power() - mod_inc)
                else:
                    self.thrusters.rv.set_power(self.thrusters.rv.get_power() - mod_inc)
            # Overall multiplier
            else:
                self.thrusters.overall_multiplier = max(
                    self.thrusters.overall_multiplier - mod_inc,
                    0
                )

        # If right bumper is pressed, increase thruster mask values.
        elif controls["right_bumper"] and not self.instantaneous_controls["right_bumper"]:
            modded_thrusters = True
            # Front motors: fr, fl, fv
            if controls["up"]:
                if controls["right"]:
                    self.thrusters.fr.set_power(self.thrusters.fr.get_power() + mod_inc)
                elif controls["left"]:
                    self.thrusters.fl.set_power(self.thrusters.fl.get_power() + mod_inc)
                else:
                    self.thrusters.fv.set_power(self.thrusters.fv.get_power() + mod_inc)
            # Rear motors: rr, rl, rv
            elif controls["down"]:
                if controls["right"]:
                    self.thrusters.rr.set_power(self.thrusters.rr.get_power() + mod_inc)
                elif controls["left"]:
                    self.thrusters.rl.set_power(self.thrusters.rl.get_power() + mod_inc)
                else:
                    self.thrusters.rv.set_power(self.thrusters.rv.get_power() + mod_inc)
            # Overall multiplier
            else:
                self.thrusters.overall_multiplier = min(
                    self.thrusters.overall_multiplier + mod_inc,
                    1
                )

        # If back is pressed, reverse thruster polarity.
        elif controls["back"] and not self.instantaneous_controls["back"]:
            modded_thrusters = True
            # Front motors: fr, fl, fv
            if controls["up"]:
                if controls["right"]:
                    self.thrusters.fr.reverse_polarity()
                elif controls["left"]:
                    self.thrusters.fl.reverse_polarity()
                else:
                    self.thrusters.fv.reverse_polarity()
            # Rear motors: rr, rl, rv
            elif controls["down"]:
                if controls["right"]:
                    self.thrusters.rr.reverse_polarity()
                elif controls["left"]:
                    self.thrusters.rl.reverse_polarity()
                else:
                    self.thrusters.rv.reverse_polarity()

        # If start is pressed, save thruster/frame settings.
        if controls["start"] and not self.instantaneous_controls["start"]:
            modded_thrusters = True
            self.thrusters.save_settings()

        # Print thruster mask to show changes.
        if modded_thrusters:
            print(
                "FR:", self.thrusters.fr.get_multiplier(), "\n",
                "FL:", self.thrusters.fl.get_multiplier(), "\n",
                "RR:", self.thrusters.rr.get_multiplier(), "\n",
                "RL:", self.thrusters.rl.get_multiplier(), "\n",
                "FV:", self.thrusters.fv.get_multiplier(), "\n",
                "RV:", self.thrusters.rv.get_multiplier(), "\n",
                "Overall:", self.thrusters.overall_multiplier, "\n",
            )

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
