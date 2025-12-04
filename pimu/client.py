
import zmq
import struct
from pimu.utils import PACKET_FORMAT, RATE, unpack_data, get_current_dt, PORT
from dataclasses import dataclass
from threading import Thread

@dataclass
class ImuData:
    recv_ts: float=0.0
    sensor_ts: float=0.0
    ax: float=0.0
    ay: float=0.0
    az: float=0.0
    gx: float=0.0
    gy: float=0.0
    gz: float=0.0

class ImuReader:
    def __init__(self, ip: str, port: int=PORT):
        # ZMQ setup
        ctx = zmq.Context()
        self.sock = ctx.socket(zmq.SUB)
        self.sock.setsockopt(zmq.LINGER, 0)
        self.sock.setsockopt(zmq.RCVHWM, int(RATE))
        self.sock.setsockopt_string(zmq.SUBSCRIBE, "")  # sub to all topics
        self.sock.connect(f"tcp://{ip}:{port}")
        
        # Prepare to unpack messages
        self.packet_size = struct.calcsize(PACKET_FORMAT)
        self.last_data = ImuData()

        # Create listener thread
        self.thread = Thread(target=self._spin, daemon=True)
        self.thread.start()

    def _spin(self):
        while True:
            data = self.sock.recv()

            # Skip malformed packet
            if len(data) != self.packet_size:
                continue

            # Unpack data
            try:
                self.last_data = ImuData(
                    get_current_dt().timestamp(),
                    *unpack_data(data)
                )
            except Exception as e:
                print(f"Error parsing IMU data: {e}")
                pass
