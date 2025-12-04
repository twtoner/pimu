#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 user@client-host"
    echo "Example: $0 pi@device.local"
    exit 1
fi

CLIENT="$1"
SAMPLES=7

now() {
    python3 - <<'PY'
import time
print(f"{time.time():.9f}")
PY
}

echo "Measuring SSH RTT to $CLIENT ..."
best_rtt=""

for i in $(seq 1 "$SAMPLES"); do
    t1=$(now)
    ssh -o BatchMode=yes -o ConnectTimeout=2 "$CLIENT" "true" >/dev/null 2>&1 || {
        echo "SSH to $CLIENT failed."
        exit 1
    }
    t2=$(now)

    rtt=$(python3 - "$t1" "$t2" <<'PY'
import sys
t1 = float(sys.argv[1])
t2 = float(sys.argv[2])
print(f"{t2 - t1:.9f}")
PY
)
    echo "  RTT sample $i: $rtt s"

    if [ -z "$best_rtt" ] || python3 - "$rtt" "$best_rtt" <<'PY'
import sys
cur = float(sys.argv[1])
best = float(sys.argv[2]) if sys.argv[2] != "" else float("inf")
raise SystemExit(0 if cur < best else 1)
PY
    then
        best_rtt="$rtt"
    fi
done

echo "Best RTT: $best_rtt s"

one_way=$(python3 - "$best_rtt" <<'PY'
import sys
rtt = float(sys.argv[1])
print(f"{rtt / 2.0:.9f}")
PY
)

local_now=$(now)
target_epoch=$(python3 - "$local_now" "$one_way" <<'PY'
import sys
now = float(sys.argv[1])
delay = float(sys.argv[2])
print(f"{now + delay:.9f}")
PY
)

echo "Local time:   $local_now s"
echo "Target epoch: $target_epoch s"
echo "Setting client time on $CLIENT ..."

ssh "$CLIENT" "sudo date -u -s '@$target_epoch' >/dev/null"

echo "Checking offset ..."
T1=$(now)
CLIENT_EPOCH=$(ssh "$CLIENT" python3 - <<'PY'
import time
print(f"{time.time():.9f}")
PY
)
T2=$(now)

python3 - "$T1" "$T2" "$CLIENT_EPOCH" <<'PY'
import sys
T1 = float(sys.argv[1])
T2 = float(sys.argv[2])
C  = float(sys.argv[3])

mid = (T1 + T2) / 2.0
offset = C - mid  # client - server(mid)

print(f"T1 (server before): {T1:.9f}")
print(f"T2 (server after):  {T2:.9f}")
print(f"Midpoint (server):  {mid:.9f}")
print(f"Client time:        {C:.9f}")
print(f"Estimated offset (client - server_mid): {offset:+.6f} s")
PY
