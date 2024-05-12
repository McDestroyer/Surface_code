"""Send a Raspberry Pi commands from joystick."""

import json
import socket
import time
from pi_connection import PiConnection
from controller import Controller
from controller_config import XBOX_CONFIG
from thruster_pwm import lateral_thruster_calc
from serial_manager import SerialManager

class Main:
    """Exists so I can use self vars"""

    def __init__(self) -> None:
        self.joy = Controller(XBOX_CONFIG)
        self.ser = SerialManager()
        self.pi = PiConnection()

    def main(self):
        """Main"""
        while True:
            self.joy.update()

            controls = self.joy.get()

            left_x = controls["left_x"]
            left_y = controls["left_y"]
            right_x = controls["right_x"]
            right_y = -controls["right_y"]
            triggers = controls["triggers"]
            buttons = [controls["a"], controls["b"],
                       controls["x"], controls["y"]]

            thrust = lateral_thruster_calc(left_x, left_y, right_x)

            data = thrust.get_pwm(triggers, right_y)
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

            if buttons[0]:
                self.ser.send("1")
                # print("a", end="")
            else:
                self.ser.send("0")

            if buttons[1]:
                pass
                # print("b", end="")
            if buttons[2]:
                pass
                # print("x", end="")
            if buttons[3]:
                pass
                # print("y", end="")
            # print()

            self.pi.send(json.dumps(data).encode())

            # print("Left X:", left_x, "Left Y:", left_y, "Right X:", right_x,
            #       "Right Y:", right_y, "Triggers:", triggers)
            print(data, "\n", self.pi.recv())

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
