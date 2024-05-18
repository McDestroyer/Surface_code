import socket
from time import sleep


class PiConnection:
    """Interface for communicating with a Raspberry Pi."""

    def __init__(self):

        self.TCP_IP = "169.254.6.161"
        self.TCP_PORT = 5005
        self.port_mod = 0
        self.BUFFER_SIZE = 1024
        self.TIMEOUT = 5

        while True:
            try:
                if self.port_mod >= 10:
                    self.port_mod = 0
                print("Trying port:", self.TCP_PORT + self.port_mod)
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.settimeout(self.TIMEOUT)
                self.s.connect((self.TCP_IP, self.TCP_PORT + self.port_mod))
                print("Connected to port:", self.TCP_PORT + self.port_mod)
                sleep(2.5)
                break
            except socket.timeout as e:
                print(e)
                self.port_mod += 1
            except ConnectionRefusedError as e:
                print(e)
                self.port_mod += 1

    def send(self, message):
        """Send a message."""
        self.s.send(message)

    def recv(self):
        """Receive a message."""
        return self.s.recv(self.BUFFER_SIZE)

    def close(self):
        """Close the connection."""
        self.s.close()

    def __del__(self):
        self.s.close()
