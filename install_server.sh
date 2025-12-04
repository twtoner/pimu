# Create virtual environment with Raspberry Pi packages
python3 -m venv --system-site-packages .venv

# Activate environment
source .venv/bin/activate

# Install
pip install -e .

# Install server-only requirements
pip install adafruit-circuitpython-lsm6ds
pip install adafruit-circuitpython-lis3mdl
