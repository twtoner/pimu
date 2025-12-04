from datetime import datetime, timezone
import struct

# struct 7 doubles: timestamp + 3 accel + 3 gyro
PACKET_FORMAT =  "<7d"
# Data rate
RATE = 500
# Publishing port
PORT = 5555

def get_imu_parser() -> callable:
    """
    Set up IMU interface and return a function that returns IMU data 
    in a tuple of the following format (accel, gyro), where
    - accel = (ax, ay, az) in m/s/s
    - gyro = (wx, wy, wz) in deg/s

    Notes:
    - Sensor driver set to 416 Hz parsing
    """
    from adafruit_lsm6ds.lsm6dsox import LSM6DSOX
    from adafruit_lsm6ds import Rate
    import board

    i2c = board.I2C()
    sensor = LSM6DSOX(i2c)
    sensor.accelerometer_data_rate = Rate.RATE_416_HZ
    sensor.gyro_data_rate = Rate.RATE_416_HZ
    return lambda: (sensor.acceleration, sensor.gyro)

def get_current_dt() -> datetime:
    return datetime.now(tz=timezone.utc)

def ts_to_dt(timestamp: float):
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)

def pack_data(msg_ts: float, accel: float, gyro: float) -> bytes:
    """
    Given a message timestamp, accel 3-tuple, and gyro 3-tuple,
    return a bytes representation following the `PACKET_FORMAT` structure.
    """
    return struct.pack(
        PACKET_FORMAT,
        msg_ts,
        accel[0], accel[1], accel[2],
        gyro[0], gyro[1], gyro[2]
    )

def unpack_data(data: bytes) -> tuple[float, float, float, float, float, float, float]:
    """
    Unpack data into the format:
    (ts, ax, ay, az, gx, gy, gz)
    """
    return struct.unpack(PACKET_FORMAT, data)
