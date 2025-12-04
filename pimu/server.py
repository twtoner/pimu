import argparse
from datetime import datetime, timezone
import signal
import time
import zmq
from pimu.utils import get_imu_parser, pack_data, RATE, PORT

# Get global sensor parser handle
imu_parser = get_imu_parser()

# Initialize stop signal
_STOP = False

def _signal_handler(signum, frame):
    global _STOP
    _STOP = True


def run_server(port: int, rate: float=RATE) -> int:
    global _STOP
    # Set up signal handlers for systemd-friendly shutdown
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    # ZMQ setup
    ctx = zmq.Context()
    sock = ctx.socket(zmq.PUB)
    sock.setsockopt(zmq.LINGER, 0)
    sock.setsockopt(zmq.SNDHWM, int(rate))
    sock.bind(f"tcp://*:{port}")

    # Run loop
    dt = 1.0 / rate
    next_t = time.perf_counter()
    counter = 0
    try:
        while not _STOP:
            # Wait to publish at pub rate #
            now = time.perf_counter()
            if now < next_t:
                time.sleep(next_t - now)
            next_t += dt

            # Read data #
            msg_ts = datetime.now(tz=timezone.utc).timestamp()
            accel, gyro = imu_parser()

            # Package data #
            data = pack_data(msg_ts, accel, gyro)

            # Non-blocking send: drops if HWM reached
            sock.send(data, flags=zmq.NOBLOCK)

            # Print status every second
            if counter % rate < 1e-9:
                print(f"{msg_ts=}")
                print(f"{accel=}")
                print(f"{gyro=}")
                print("")
                counter %= 0xFFFFFFFF # limit to 32 bits so it doesn't grow infinitely
            counter += 1
            
    finally:
        sock.close()

    return 0


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="IMU Publisher Server")
    parser.add_argument(
        "--port",
        type=int,
        default=PORT,
        help=f"Port to send on. Default: {PORT}",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    return run_server(args.port)


if __name__ == "__main__":
    raise SystemExit(main())
