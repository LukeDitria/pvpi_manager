import logging
import os
from typing import Protocol

import serial
import zmq
import zmq.asyncio

_logger = logging.getLogger(__name__)


class BaseTransportInterface(Protocol):
    def write(self, message: bytes) -> bytes: ...

    def close(self) -> None: ...


# TODO keyboard interrupt
# TODO service stop
# TODO serial not found or similar


class SerialInterface(BaseTransportInterface):
    def __init__(self, port: str = "/dev/ttyAMA0", baud_rate: int = 115_200, timeout_sec: float = 5):
        self.port = port
        self.baud_rate = baud_rate
        self.timeout_sec = timeout_sec

        self._serial = serial.Serial(
            self.port, self.baud_rate, timeout=self.timeout_sec, write_timeout=self.timeout_sec
        )
        _logger.info("Successfully opened serial port %s at %i baud.", self.port, self.baud_rate)

    def close(self):
        if self._serial and self._serial.is_open:
            self._serial.close()

    def write(self, message: bytes) -> bytes:
        try:
            self._serial.write(message)
            _logger.debug("Written to serial: %s", message)

            response = self._serial.readline()
            _logger.debug("Received from serial: %s", response)
            return response
        except serial.SerialException as err:
            raise err  # TODO
        except Exception:
            raise


class ZmqSerialProxyInterface(BaseTransportInterface):
    def __init__(self, addr: str = "tcp://127.0.0.1:5555"):
        self.addr = addr

        _logger.info("Connecting to socket at %s", addr)
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.DEALER)
        self.client_id = f"client_{os.getpid()}".encode()
        self.socket.setsockopt(zmq.IDENTITY, self.client_id)
        self.socket.connect(self.addr)

    def close(self):
        _logger.info("Closing socket...")
        self.socket.close()
        self.context.term()

    def write(self, message: bytes) -> bytes:
        self.socket.send_multipart([message])
        response = b"".join(self.socket.recv_multipart())
        return response  # TODO error handling here?
