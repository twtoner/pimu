# pimu
Stream data from an IMU through a Raspberry Pi. 

This package treats the Pi as a server and any other machine on the network as a client.

## Client installation and usage
Clients can treat this repo as an installable pip package and use in their code.
```
pip install git+https://github.com/https://github.com/twtoner/pimu
```

Then, the `ImuReader` class can be used in the following way:

```python
from pimu.client import ImuReader

imu = ImuReader(ip="10.12.194.1") # port=5555 used by default

while True:
    print(imu.last_data)
```
Note that it is important to use the IP of the lowest-latency interface to the server. For example, it may be accessible over both WiFi and local LAN/USB. Check `ifconfig` on the server and choose the latter when possible.

Here, the data is encoded using the following data structure
```python
class ImuData:
    recv_ts: float=0.0
    sensor_ts: float=0.0
    ax: float=0.0
    ay: float=0.0
    az: float=0.0
    gx: float=0.0
    gy: float=0.0
    gz: float=0.0
```

The `sensor_ts` is the timestamp in the sensor's local time at the time of sending, while `recv_ts` is the timestamp in the client's local time at the time of receiving. See more information in the Hardware Setup section.

## Server installation and usage
Clone the repo locally
```
gh repo clone twtoner/pimu
```
To install,
```
./server_install.sh
```
Then, to run
```
./server_run.sh
```
Sensor data will be published to the terminal at 1 Hz:
```
msg_ts=1764829339.64116
accel=(-0.24885355039999998, -0.13758729949999998, 9.919446088299999)
gyro=(0.010537425358915765, -0.00839939702522271, 0.0013744467859455344)

msg_ts=1764829341.727843
accel=(-0.251246373, -0.12442677519999999, 9.9469635482)
gyro=(0.00992656012071775, -0.008704829644321718, 0.0016798794050445422)

msg_ts=1764829343.8144
accel=(-0.24885355039999998, -0.1387837108, 9.9433743143)
gyro=(0.01038470904936626, -0.010995574287564275, 0.0013744467859455344)
```

## Hardware setup
It is strongly recommended to use a wired connection directly between the server and client. For example, put the Raspberry Pi in [USB gadget mode](https://github.com/raspberrypi/rpi-usb-gadget) and connect directly to the client's USB-C port for power and data; this enables <1 ms ping times. If you choose a wired connection, machine time differences are likely larger than communication latency, so it is recommended to use `recv_ts` for timestamps.

If you use a wireless setup but the data is not used in closed loop, then it's important to ensure both the client and server are closely synchronized in time. This can be done by setting up a chrony server on either machine. An alternative is to adjust the server's local time to account for the difference. This repo contains a script to help with this:
```
gh repo clone twtoner/pimu
```
Then run 
```
./client_synctime --ip <server-ip>
```
This will estimate the interface latency and then publish an adjusted time to the client:
```
$ ./client_synctime.sh <server-username>@<server-ip>
Measuring SSH RTT to <server-username>@<server-ip> ...
  RTT sample 1: 0.352582932 s
  RTT sample 2: 0.294234037 s
  RTT sample 3: 0.330222130 s
  RTT sample 4: 0.325948954 s
  RTT sample 5: 0.347456932 s
  RTT sample 6: 0.317037106 s
  RTT sample 7: 0.342265844 s
Best RTT: 0.294234037 s
Local time:   1764832663.873984098 s
Target epoch: 1764832664.021101236 s
Setting client time on <server-username>@<server-ip> ...
Checking offset ...
T1 (server before): 1764832664.304933071
T2 (server after):  1764832664.667839050
Midpoint (server):  1764832664.486386061
Client time:        1764832664.404209852
Estimated offset (client - server_mid): -0.082176 s
```
Note that the remaining offset is still far larger than 1ms.

If the sensor data is not needed in closed loop, then use the timestamp with the least expected delay. If network delay > clock offset, use `sensor_ts`; if network delay < clock offset, use `recv_ts`.

## Plotting
On the client, clone the repo locally and run
```
python3 tools/plot.py --ip <server-ip>
```
![alt text](figures/image.png)
