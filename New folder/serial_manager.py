import serial
from time import sleep

class SerialManager:
    def __init__(self) -> None:
        self.do_ser = True

        for port in range(30):
            try:
                self.ser = serial.Serial('/dev/ttyACM'+str(port), 9600)
                print("connected to:", '/dev/ttyACM'+str(port))
                return
            except serial.serialutil.SerialException:
                continue

        print("Could not connect to serial device.")
        self.do_ser = False

    def send(self, message: str) -> None:
        """Send a message."""
        if not self.do_ser:
            return
        self.ser.write(message.encode())

    def recv(self) -> str:
        """Receive a message."""
        if not self.do_ser:
            return
        return self.ser.readline().decode()

    def close(self) -> None:
        """Close the connection."""
        if not self.do_ser:
            return
        self.ser.close()

    def __del__(self) -> None:
        if not self.do_ser:
            return
        self.ser.close()

if __name__ == "__main__":
    ser = SerialManager()
    for i in range(10):
        ser.send("1")
        print("sent 1")
        sleep(1)
        ser.send("0")
        print("sent 0")
        sleep(1)
    # print(ser.recv())
    ser.close()
