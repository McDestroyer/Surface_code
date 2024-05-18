"""Module providing a basic wrapper for ROV thrusters and PWM calculations."""
import os

thruster_mask_dict = {
    "fr": -1,  # fr
    "fl": 1,  # fl
    "rr": -1,  # rr
    "rl": -1,  # rl
    "fv": .75,  # fv
    "rv": .75,  # rv
    "power_multiplier": .6
}

class Thruster:
    """Basic wrapper for a servo-based thruster."""

    def __init__(self, reverse_polarity: bool = False, power_multiplier: float = 1.0,
                 pulse_range: tuple[int, int] | None = None) -> None:
        """Initialize a new thruster

        Args:
            reverse_polarity (bool, optional):
                Whether the thruster is in reverse polarity.
                Defaults to False.
            power_multiplier (float, optional):
                Multiplier for the thruster power. Must be between 0.0 and 1.0.
                Defaults to 1.0.
            pulse_range (tuple[int, int], optional):
                The range of PWM values the thruster can accept.
                Defaults to (1100, 1900).
        """
        self.power = 0
        self.polarity_mask = -1 if reverse_polarity else 1
        self.multiplier = min(max(power_multiplier, 0), 1)
        self.pulse_range = pulse_range if pulse_range else (1100, 1900)

    def get_pwm(self) -> int:
        """Get a PWM value for the thruster at its current power.
        
        Returns:
            int: The PWM value for the thruster."""
        power = self.power * self.polarity_mask * self.multiplier
        return int(self.pulse_range[0] + 0.5 * (self.pulse_range[1] - self.pulse_range[0]) * (power))  # NOTE: There was a +1 to the power here? If broken, add back

    def reverse_polarity(self) -> bool:
        """Toggle the polarity of the thruster.
        
        Returns:
            bool: Whether the polarity is now reversed.
        """
        self.polarity_mask *= -1
        return True if self.polarity_mask == -1 else False

    def set_power(self, power: float) -> None:
        """Set the power of the thruster.
        
        Args:
            power (float):
                The power of the thruster. Must be between -1.0 and 1.0.
        """
        self.power = min(max(power, 0), 1)

    def get_power(self) -> float:
        """Get the power of the thruster.
        
        Returns:
            float: The power of the thruster.
        """
        return self.power

    def set_multiplier(self, power_multiplier: float) -> None:
        """Set the power multiplier of the thruster.
        
        Args:
            power_multiplier (float):
                The power multiplier of the thruster. Must be between 0.0 and 1.0.
        """
        self.multiplier = min(max(power_multiplier, 0), 1)

    def get_multiplier(self) -> float:
        """Get the power multiplier of the thruster.
        
        Returns:
            float: The power multiplier of the thruster multiplied by the polarity mask
                (This means it would be negative if the motor is reversed).
        """
        return self.multiplier * self.polarity_mask

    def __repr__(self) -> str:
        return f"Thruster(power={self.power})"

class FrameThrusters:
    """Wrapper for a ROV frame's thrusters."""

    def __init__(self, folder_name: str = "default_thruster_profile") -> None:
        """Initialize a new set of thruster values.
        
        Args:
            file_name (str, optional):
                The path to the folder containing the thruster settings starting
                inside the configs folder.
                Defaults to "default_thruster_profile".
        """
        # Generate the path to the file.
        current_path = os.path.dirname(__file__)
        self.folder_path = os.path.join(current_path, "configs", folder_name)

        # Load settings from a file if a file name is provided.
        settings = get_settings(self.folder_path)

        # Initialize thrusters.
        self.fr = Thruster(settings["fr"][0], settings["fr"][1])
        self.fl = Thruster(settings["fl"][0], settings["fl"][1])
        self.rr = Thruster(settings["rr"][0], settings["rr"][1])
        self.rl = Thruster(settings["rl"][0], settings["rl"][1])
        self.fv = Thruster(settings["fv"][0], settings["fv"][1])
        self.rv = Thruster(settings["rv"][0], settings["rv"][1])

        self.overall_multiplier = settings["multiplier"]

    def get_pwm(self) -> dict[str, int]:
        """Get a PWM value for each thruster at its current power."""
        return {
            "fr": self.fr.get_pwm(),
            "fl": self.fl.get_pwm(),
            "rr": self.rr.get_pwm(),
            "rl": self.rl.get_pwm(),
            "fv": self.fv.get_pwm(),
            "rv": self.rv.get_pwm(),
        }

    def thrust_calc(self, x: float, y: float, z: float, pitch: float, yaw: float) -> None:
        """Calculate thruster values for a given set of inputs.

        Args:
            x (float):
                Sideways movement speed (between -1.0 and 1.0).
            y (float):
                Forward movement speed (between -1.0 and 1.0).
            z (float):
                Vertical movement speed (between -1.0 and 1.0).
            pitch (float):
                Pitch speed (between -1.0 and 1.0).
            yaw (float):
                Yaw speed (between -1.0 and 1.0).
        """
        lateral_thrusters = lateral_thruster_calc(x, y, yaw)
        vertical_thrusters = vertical_pwm_calc(z, pitch)

        self.fr.set_power(lateral_thrusters["fr"] * self.overall_multiplier)
        self.fl.set_power(lateral_thrusters["fl"] * self.overall_multiplier)
        self.rr.set_power(lateral_thrusters["rr"] * self.overall_multiplier)
        self.rl.set_power(lateral_thrusters["rl"] * self.overall_multiplier)
        self.fv.set_power(vertical_thrusters["fv"] * self.overall_multiplier)
        self.rv.set_power(vertical_thrusters["rv"] * self.overall_multiplier)


    def save_settings(self, folder_name: str = "") -> None:
        """Save the current thruster and frame settings to either the
        specified folder or the currently saved one. Creates one if necessary.
        
        Args:
            folder_name (str, optional):
                The name of the folder to save the settings to.
                Defaults to the currently saved folder.
        """
        if not folder_name:
            pass
        else:
            # Generate the path to the folder.
            current_path = os.path.dirname(__file__)
            self.folder_path = os.path.join(current_path, "configs", folder_name)

        # Verify that the folder exists/is valid.
        if not os.path.exists(os.path.dirname(self.folder_path)):
            os.makedirs(os.path.dirname(self.folder_path))

        # Generate the paths to the first settings files.
        path = os.path.join(self.folder_path, "thruster_profile.fngr")

        # Save the settings to the file.
        for _ in range(2):
            with open(path, "w", encoding="UTF-8") as file:
                file.write(f"fr:{self.fr.polarity_mask}:{self.fr.multiplier}\n")
                file.write(f"fl:{self.fl.polarity_mask}:{self.fl.multiplier}\n")
                file.write(f"rr:{self.rr.polarity_mask}:{self.rr.multiplier}\n")
                file.write(f"rl:{self.rl.polarity_mask}:{self.rl.multiplier}\n")
                file.write(f"fv:{self.fv.polarity_mask}:{self.fv.multiplier}\n")
                file.write(f"rv:{self.rv.polarity_mask}:{self.rv.multiplier}\n")

            # Generate the paths to the second settings file for the second loop.
            path = os.path.join(self.folder_path, "frame_profile.fngr")

        print("Settings saved to:", self.folder_path)


def get_settings(path: str) -> dict[str, list[bool, float] | float]:
    """Get settings from a file.

    Args:
        path (str):
            The path to the folder.

    Returns:
        dict[str, list[bool, float]]: A dictionary of settings.
    """
    # Verify that the file exists/is valid.
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

    # Generate the paths to the specific settings files.
    thruster_path = os.path.join(path, "thruster_profile.fngr")
    frame_path = os.path.join(path, "frame_profile.fngr")

    default_thruster_settings = {
        "fr": [False, 1.0],
        "fl": [False, 1.0],
        "rr": [False, 1.0],
        "rl": [False, 1.0],
        "fv": [False, 1.0],
        "rv": [False, 1.0],
    }

    default_frame_settings = {
        "multiplier": 1.0,
    }

    # Get thruster settings:

    # Read the file and return the settings, or create a new file if it doesn't exist.
    try:
        with open(thruster_path, "r", encoding="UTF-8") as file:
            file_lines = file.readlines()[:]
        if len(file_lines) < 6:
            print("File is of insufficient length. Replacing file contents...")
            raise FileNotFoundError
    except FileNotFoundError:
        print("File not found or empty. Creating new file...")
        with open(thruster_path, "w", encoding="UTF-8") as file:
            for key, value in default_thruster_settings.items():
                file.write(f"{key}:{value[0]}:{value[1]}\n")

    with open(thruster_path, "r", encoding="UTF-8") as file:
        file_lines = file.readlines()[:]

    # Parse the settings into a dictionary and return.
    settings_dict = {}
    for line in file_lines:
        line = line.split(":")
        settings_dict[line[0]] = [is_bool(line[1]), float(line[2])]

    # Get frame settings:

    # Read the file and return the settings, or create a new file if it doesn't exist.
    try:
        with open(frame_path, "r", encoding="UTF-8") as file:
            file_lines = file.readlines()[:]
        if len(file_lines) < 1:
            print("File is of insufficient length. Replacing file contents...")
            raise FileNotFoundError
    except FileNotFoundError:
        print("File not found. Creating new file...")
        with open(frame_path, "w", encoding="UTF-8") as file:
            for key, value in default_frame_settings.items():
                file.write(f"{key}:{value}\n")

    with open(frame_path, "r", encoding="UTF-8") as file:
        file_lines = file.readlines()[:]

    # Parse the settings into the dictionary and return.
    for line in file_lines:
        line = line.split(":")
        settings_dict[line[0]] = float(line[1])

    return settings_dict


def is_bool(string: str) -> bool | None:
    """Check if a string is a boolean.
    Mostly just for fun bc it'll always be the words true or false.

    Args:
        string (str):
            The string to check.

    Returns:
        bool: Whether the string is a boolean.
    """
    positive_answers = (['ok', 'okay', 'yes', 'y', 'sure', '1', 'true', 'affirmative',
                         'alright', 't', 'yeah', 'yup', 'ye', 'yea'])
    negative_answers = (['no', 'nope', 'negative', 'nein', '0',
                         'n', 'false', 'nah', 'nay', 'negatory'])

    if string.lower() in positive_answers:
        return True
    elif string.lower() in negative_answers:
        return False
    else:
        return None


def lateral_thruster_calc(x: float, y: float, r: float) -> tuple[str, float]:
    """Calculate lateral thruster values for a given set of inputs.

    Args:
        x (float):
            Sideways movement speed (between -1.0 and 1.0).
        y (float):
            Forward movement speed (between -1.0 and 1.0).
        r (float):
            Rotation speed (between -1.0 and 1.0).

    Returns:
        dict[str, float]: A dictionary of thruster values for each lateral thruster.
    """

    # Assume that positive values are all going forward.
    # We can reason what what should happen if we only have a single non-zero input:

    # [x, y, r] -> [ur, ul, lr, ll]
    # [1, 0, 0] -> [-1, +1, +1, -1]
    # [0, 1, 0] -> [+1, +1, +1, +1]
    # [0, 0, 1] -> [+1, +1, -1, -1]

    # We can calculate thruster values as a linear combination of the input values
    # by repeating this pattern with each output scaled by the actual value of each input.

    x_contrib = [x,  -x,  -x, x]
    y_contrib = [ y,  y,  y,  y]
    r_contrib = [ r,  -r, r, -r]

    # However, we want thruster values to be in the range [-1.0, 1.0], so we need to
    # normalize based on the maximum possible value this can have: 3

    # Jason: I modified the following lines a bit to make it scale based on joystick input
    # to avoid low power throughput.
    # fr = (x_contrib[0] + y_contrib[0] + r_contrib[0]) / 3.0
    # fl = (x_contrib[1] + y_contrib[1] + r_contrib[1]) / 3.0
    # rr = (x_contrib[2] + y_contrib[2] + r_contrib[2]) / 3.0
    # rl = (x_contrib[3] + y_contrib[3] + r_contrib[3]) / 3.0
    fr = x_contrib[0] + y_contrib[0] + r_contrib[0]
    fl = x_contrib[1] + y_contrib[1] + r_contrib[1]
    rr = x_contrib[2] + y_contrib[2] + r_contrib[2]
    rl = x_contrib[3] + y_contrib[3] + r_contrib[3]
    normalization_factor = max(abs(fr), abs(fl), abs(rr), abs(rl), 1)
    fr /= normalization_factor
    fl /= normalization_factor
    rr /= normalization_factor
    rl /= normalization_factor

    return {"fr": fr, "fl": fl, "rr": rr, "rl": rl}


def vertical_pwm_calc(z: float, pitch: float) -> dict[str, float]:
    """Calculate vertical thruster values for a given set of inputs.

    Args:
        z (float):
            Vertical movement speed (between -1.0 and 1.0).
        pitch (float):
            Pitch speed (between -1.0 and 1.0).

    Returns:
        dict[str, int]: A dictionary of PWM values for the vertical thrusters.
    """
    fv = z - pitch
    rv = z + pitch

    # However, we want thruster values to be in the range [-1.0, 1.0],
    # so we need to normalize based on the maximum possible value this can have: 1
    normalization_divisor = max(abs(fv), abs(rv), 1)

    fv /= normalization_divisor
    rv /= normalization_divisor

    return {"fv": fv, "rv": rv}
