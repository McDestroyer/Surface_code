"""Module providing a basic wrapper for ROV thrusters and PWM calculations."""
import math

thruster_mask = [
    -1,
    1,
    -1,
    -1,
    .75,
    .75,
]

power_multiplier = .6

class Thruster:
    """Basic wrapper for a servo-based thruster."""

    def __init__(self, power: float = 0.0):
        """Initialize a new thruster

        Args:
            power (int, optional): Motor power. Defaults to 0.0.
        """
        self.power = power
        self.reverse_polarity = False

    def toggle_polarity(self):
        """Toggle the polarity of the thruster."""
        self.reverse_polarity = not self.reverse_polarity

    def get_pwm(self, min_pulse: int = 1100, max_pulse: int = 1900) -> int:
        """Get a PWM value for the thruster at its current power."""
        power = -self.power if self.reverse_polarity else self.power
        return int(min_pulse + 0.5 * (max_pulse - min_pulse) * (power + 1))

    def __repr__(self) -> str:
        return f"Thruster(power={self.power})"

class FrameThrusters:
    """Wrapper for a ROV frame's thrusters."""

    def __init__(self, fr: Thruster, fl: Thruster, rr: Thruster, rl: Thruster):
        """Initialize a new set of thruster values.

        Args:
            fr (Thruster): Upper right thruster.
            fl (Thruster): Upper left thruster.
            rr (Thruster): Lower right thruster.
            rl (Thruster): Lower left thruster.
        """
        self.fr = fr
        self.fl = fl
        self.rr = rr
        self.rl = rl

    def get_pwm(self, z, pitch, min_pulse: int = 1100, max_pulse: int = 1900) -> dict[str, int]:
        """Get a PWM value for each thruster at its current power."""
        return {
            "fr": self.fr.get_pwm(min_pulse, max_pulse),
            "fl": self.fl.get_pwm(min_pulse, max_pulse),
            "rr": self.rr.get_pwm(min_pulse, max_pulse),
            "rl": self.rl.get_pwm(min_pulse, max_pulse),
            "fv": vertical_pwm_calc(z, pitch)[0],
            "rv": vertical_pwm_calc(z, pitch)[1],
        }

def lateral_thruster_calc(x: float, y: float, r: float) -> FrameThrusters:
    """Calculate lateral thruster values for a given set of inputs.

    Args:
        x (float): Sideways movement speed (between -1.0 and 1.0).
        y (float): Forward movement speed (between -1.0 and 1.0).
        r (float): Rotation speed (between -1.0 and 1.0).

    Returns:
       FrameThrusters: A collection of Thrusters at the correct power levels."""

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

    fr *= thruster_mask[0] * power_multiplier #* 1 if y <= 0 else .8
    fl *= thruster_mask[1] * power_multiplier #* 1 if y >= 0 else .8
    rr *= thruster_mask[2] * power_multiplier #* 1 if y <= 0 else .8
    rl *= thruster_mask[3] * power_multiplier #* 1 if y >= 0 else .8

    return FrameThrusters(Thruster(fr), Thruster(fl), Thruster(rr), Thruster(rl))

def map_to_circle(x: float, y: float) -> tuple[float, float]:
    """Map rectangular controller inputs to a circle."""
    return (x*math.sqrt(1 - y**2/2.0), y*math.sqrt(1 - x**2/2.0))

INV_SQRT2 = 0.7071067811865476
def lateral_thruster_calc_circular(x: float, y: float, r: float):
    """Calculate lateral thruster values for a given set of inputs after mapping them to a circle.

    Args:
        x (float): Sideways movement speed (between -1.0 and 1.0).
        y (float): Forward movement speed (between -1.0 and 1.0).
        r (float): Rotation speed (between -1.0 and 1.0).

    Returns:
       FrameThrusters: A collection of Thrusters at the correct power levels."""
    # some bullshit
    x, y = map_to_circle(x, y)
    r *= INV_SQRT2
    thrusters = lateral_thruster_calc(x, y, r)
    mag_adjust = abs(math.sqrt(x**2 + y**2) / max((thrusters.fr.power,
                                               thrusters.fl.power,
                                               thrusters.rr.power,
                                               thrusters.rl.power)))

    thrusters.fr.power *= mag_adjust
    thrusters.fl.power *= mag_adjust
    thrusters.rr.power *= mag_adjust
    thrusters.rl.power *= mag_adjust
    return thrusters

def vertical_pwm_calc(z: float, pitch: float) -> tuple[int, int]:
    """Calculate vertical thruster values for a given set of inputs.

    Args:
        z (float):
            Vertical movement speed (between -1.0 and 1.0).
        pitch (float):
            Pitch speed (between -1.0 and 1.0).

    Returns:
        tuple[int, int]: A tuple of PWM values for the vertical thrusters.
    """
    fv = z + pitch
    rv = z - pitch

    # However, we want thruster values to be in the range [-1.0, 1.0], so we need to normalize based on the maximum
    # possible value this can have: 1
    normalization_divisor = max(abs(fv), abs(rv), 1)

    fv /= normalization_divisor
    rv /= normalization_divisor

    fv *= thruster_mask[4]
    rv *= thruster_mask[5] 

    # Finally, we need to convert these values to PWM values.
    fv = int(1500 + 400 * fv)
    rv = int(1500 + 400 * rv)

    return fv, rv
