import serial
from time import sleep

class SerialManager:
    def __init__(self) -> None:
        self.do_ser = True

        for port in range(19,30):
            try:
                print("Trying port:", 'COM'+str(port))

                self.ser = serial.Serial('COM'+str(port), 115200, timeout=.02)

                # self.ser.timeout = 3
                # if self.ser.writable():
                #     print("Writable")
                #     self.ser.writelines(["0".encode()])

                print("Connected to:", 'COM'+str(port))
                self.do_ser = True
                return
            except serial.serialutil.SerialException:
                continue

        print("Could not connect to serial device.")
        self.do_ser = False

    def send(self, message: str) -> None:
        """Send a message."""
        if not self.do_ser:
            return
        print("Sending:", message)
        self.ser.write(message.encode())
        print("Sent:", message)

    def recv(self) -> str:
        """Receive a message."""
        if not self.do_ser:
            return "No serial connection."
        return self.ser.readline().decode().strip()

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

        print(ser.recv())
        sleep(1)

        ser.send("0")

        print(ser.recv())
        sleep(1)
    # print(ser.recv())
    ser.close()
