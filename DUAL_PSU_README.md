# Complete PSU Control System

This system provides comprehensive control of high-voltage power supplies through multiple interfaces: direct Python scripting, web services, and LabVIEW integration. It supports both single and dual PSU operation.

## 🔌 Physical Setup Overview

### What You Need:
1. **High-voltage power supplies** (Heinzinger 30kV/2mA and/or FUG 50kV/0.5mA)
2. **Custom USB interface boards** ("Analog PSU Interface" boards, VID: 0xA0A0, PID: 0x000C)
3. **Raspberry Pi 4** (or any computer with USB ports)
4. **USB cables** to connect interface boards to computer

### How It's Connected:
```
[Heinzinger PSU] ←→ [USB Interface Board #1] ←→ [USB Cable] ←→ [Raspberry Pi USB Port]
[FUG PSU]        ←→ [USB Interface Board #2] ←→ [USB Cable] ←→ [Raspberry Pi USB Port]
                                                              ↓
                                                      [Your Control Software]
```

### What the Interface Boards Do:
- Convert USB commands to analog control signals (0-10V)
- Read voltage/current measurements back from PSUs
- Control output relay (on/off switch) for each PSU
- Each board appears as a separate USB device with the same VID/PID but different device indices

## 🏗️ Software Architecture

### Layer 1: Hardware Interface (C++)
- **Low-level USB communication** with interface boards
- **16-bit DAC control** for precise voltage/current setting
- **ADC reading** for voltage/current measurement
- **Safety checks** and error handling

### Layer 2: Python Bindings (PyBind11)
- **Bridge between C++ and Python** using PyBind11
- **Compiled module**: `heinzinger_control.so` (built from C++ code)
- **Python classes**: Expose C++ functionality as Python objects

### Layer 3: Python Control Modules
- **Direct PSU control** for scripting and automation
- **Multi-PSU management** for handling multiple devices
- **Web service layer** for remote HTTP/JSON control

### Layer 4: User Interfaces
- **Direct Python scripts** for custom automation
- **REST API service** for LabVIEW and web interfaces
- **Mock services** for testing without hardware

## 📁 Complete File Guide

This section explains every single file in the system, what it does, when to use it, and how it works with other files.

### 🔧 Core Hardware Interface Files

#### `bindings.cpp` - The Bridge Between C++ and Python
**What it does:**
- Creates Python bindings for the C++ PSU control classes
- Uses PyBind11 to expose C++ functions to Python
- Defines the `HeinzingerPSU` class that Python can import

**Technical details:**
- Compiles into `heinzinger_control.so` (the actual Python module)
- Maps C++ methods like `set_voltage()` to Python callable functions
- Handles data type conversion between C++ and Python

**When it's used:** Automatically when you import the compiled module in Python

**You don't need to modify this** unless you want to add new C++ functions to Python

---

#### `Heinzinger.cpp` + Headers in `headers/` folder - The Low-Level Control
**What it does:**
- Contains the actual C++ code that talks to USB interface boards
- Handles USB communication, DAC/ADC operations, and safety checks
- Implements the `HeinzingerVia16BitDAC` class used by Python

**Technical details:**
- Uses libusb for USB communication
- Converts voltage/current values to DAC register values
- Reads ADC values and converts them back to voltage/current
- Handles USB packet checksums and error codes

**When it's used:** Automatically when Python calls PSU functions

**You don't need to modify this** unless you're changing hardware protocols

---

### 🐍 Python Control Modules

#### `run_psu_multi.py` - The Modern Multi-PSU Engine
**What it does:**
- **Core module** for controlling one or multiple PSUs
- Manages multiple PSU instances with different device indices
- Handles module loading, initialization, and cleanup
- **Recommended for all new scripts**

**Key functions:**
```python
# Get a PSU instance (creates if needed)
psu = get_psu_instance(device_index=0, max_v=30000, max_c=2.0)

# Control functions
psu.set_voltage(1000.0)      # Set voltage
psu.set_current(1.0)         # Set current limit  
psu.switch_on()              # Turn output on
volts = psu.read_voltage()    # Read actual voltage
amps = psu.read_current()     # Read actual current
relay_on = psu.is_relay_on()  # Check if output is on
```

**When to use:**
- Writing new Python scripts to control PSUs
- Need to control multiple PSUs (device_index=0, 1, etc.)
- Want the most flexible and modern interface

**Example usage:**
```python
import run_psu_multi as psu

# Control Heinzinger (device 0)
heinz = psu.get_psu_instance(device_index=0, max_v=30000, max_c=2.0)
heinz.set_voltage(5000)

# Control FUG (device 1)  
fug = psu.get_psu_instance(device_index=1, max_v=50000, max_c=0.5)
fug.set_voltage(10000)
```

---

#### `run_psu.py` - The Original Single-PSU Module
**What it does:**
- **Legacy module** originally designed for one PSU
- Now updated to support multiple PSUs but maintains backward compatibility
- Has built-in interactive command-line interface
- **Still perfectly usable** for single PSU control

**Key features:**
- Interactive mode: run `python3 run_psu.py` for command-line control
- Commands: `setv 1000`, `setc 1.5`, `on`, `off`, `read`, `quit`
- Legacy functions for existing scripts

**When to use:**
- Quick interactive testing of a single PSU
- You have existing scripts that import `run_psu`
- You want a simple command-line interface

**Example usage:**
```bash
# Interactive mode
python3 run_psu.py
# Then type: setv 1000, on, read, off, quit

# Or import in scripts (legacy style)
import run_psu
run_psu.setup_module_path_and_load()
run_psu.initialize_psu()
run_psu.set_psu_voltage(1000)
```

---

### 🌐 Web Service Files

#### `dual_psu_service.py` - The Real Hardware Web Service
**What it does:**
- **Main web service** for controlling both PSUs via HTTP/JSON
- Used by LabVIEW, web interfaces, or any HTTP client
- Provides REST API endpoints for both Heinzinger and FUG PSUs
- **Requires actual hardware** to work properly

**API endpoints it provides:**
```
Heinzinger PSU (device_index=0):
  POST /heinzinger/set_voltage {"value": 1000}
  POST /heinzinger/set_current {"value": 1.5} 
  GET  /heinzinger/read
  GET  /heinzinger/relay
  POST /heinzinger/relay {"state": true}

FUG PSU (device_index=1):
  POST /fug/set_voltage {"value": 2000}
  POST /fug/set_current {"value": 0.3}
  GET  /fug/read 
  GET  /fug/relay
  POST /fug/relay {"state": true}

Both PSUs:
  GET  /status  (shows both PSUs)
  GET  /       (service info)
```

**When to use:**
- **Production use** with real PSU hardware
- LabVIEW integration (LabVIEW sends HTTP requests to these endpoints)
- Remote control from other computers
- Web-based control interfaces

**How to start:**
```bash
python3 dual_psu_service.py
# Service runs on http://0.0.0.0:5001
```

**Example HTTP requests:**
```bash
# Set Heinzinger to 5kV
curl -X POST http://pi_ip:5001/heinzinger/set_voltage \
     -H "Content-Type: application/json" \
     -d '{"value": 5000}'

# Read FUG status
curl http://pi_ip:5001/fug/read
```

---

#### `mock_dual_psu_service.py` - The Testing Web Service
**What it does:**
- **Simulated web service** that mimics the real service without hardware
- Same API endpoints as the real service
- **Perfect for testing** LabVIEW code, HTTP requests, JSON parsing
- Stores PSU states in memory (voltage, current, relay status)

**Key advantages:**
- Works without any hardware connected
- Same API as real service - perfect for development
- Instant responses (no USB communication delays)
- Safe to experiment with (can't damage anything)

**When to use:**
- **Development and testing** of LabVIEW programs
- Learning the API without hardware
- Testing HTTP client code
- Debugging JSON request/response formats

**How to start:**
```bash
python3 mock_dual_psu_service.py
# Service runs on http://0.0.0.0:5001
```

**What it simulates:**
- Voltage/current limits (rejects values outside PSU specs)
- State persistence (remembers settings between requests)
- All HTTP endpoints and JSON formats
- Error responses for invalid requests

---

#### `run_psu_service.py` - The Original Single-PSU Web Service  
**What it does:**
- **Legacy web service** for controlling just one PSU
- Uses the original `run_psu.py` module
- Simpler than dual service - good for single PSU setups

**When to use:**
- You only have one PSU
- You want to keep using existing LabVIEW code designed for single PSU
- Simpler setup for basic applications

---

### 📝 Example and Testing Scripts

#### `single_psu_example.py` - Interactive Single PSU Control
**What it does:**
- **Complete example** of controlling one PSU directly from Python
- Shows proper initialization, error handling, and cleanup
- Has both programmatic control and interactive command-line mode
- **Great learning resource** for understanding PSU control

**What you'll learn:**
- How to initialize a PSU with specific parameters
- How to set voltage/current and turn PSU on/off
- How to read measurements and check relay status
- Proper error handling and cleanup procedures

**When to use:**
- Learning how PSU control works
- Starting point for your own custom scripts
- Interactive testing of a single PSU
- Understanding the Python PSU API

**How to run:**
```bash
python3 single_psu_example.py
# Follow the prompts for interactive control
```

**What it teaches:**
```python
# Device selection (0=first PSU, 1=second PSU)
DEVICE_INDEX = 0

# PSU specifications
MAX_VOLTAGE = 30000.0  # 30kV for Heinzinger
MAX_CURRENT = 2.0      # 2mA for Heinzinger

# Initialize PSU
psu_instance = psu.get_psu_instance(
    device_index=DEVICE_INDEX,
    max_v=MAX_VOLTAGE, 
    max_c=MAX_CURRENT
)

# Safe operation pattern
try:
    psu_instance.set_voltage(1000.0)
    psu_instance.switch_on()
    # ... do your experiment
finally:
    psu_instance.switch_off()  # Always turn off
    psu.cleanup_psu(DEVICE_INDEX)  # Always cleanup
```

---

#### `simple_psu_script.py` - Automation Template
**What it does:**
- **Minimal script template** for automated PSU control
- No interactive mode - pure automation
- **Perfect starting point** for custom automation scripts
- Shows the essential PSU control pattern

**When to use:**
- Creating automated test sequences
- Building custom experiments
- Learning the basic PSU control flow
- Template for your own scripts

**What it demonstrates:**
```python
# Basic automation pattern:
1. Initialize PSU
2. Set voltage and current
3. Turn on
4. Do experiment (your code here)
5. Turn off
6. Cleanup
```

**How to modify for your needs:**
1. Change `DEVICE_INDEX` (0 or 1)
2. Set your PSU specifications
3. Replace the "Do your experiment here" section
4. Add your measurements, delays, voltage ramps, etc.

---

#### `test_dual_psu.py` - Web Service API Tester
**What it does:**
- **Comprehensive test** of all web service endpoints
- Tests both Heinzinger and FUG endpoints
- Validates error handling and edge cases
- **Requires `requests` library** (`pip install requests`)

**When to use:**
- Testing if the web service is working correctly
- Validating API endpoints before using with LabVIEW
- Learning the HTTP/JSON API format
- Debugging web service issues

**What it tests:**
- All voltage/current setting endpoints
- All read endpoints
- Relay control (on/off)
- Status endpoint
- Error conditions (voltage/current limits)
- Invalid requests

**How to run:**
```bash
# Start web service first
python3 dual_psu_service.py  # or mock_dual_psu_service.py

# Then run tests
python3 test_dual_psu.py
```

---

### 📚 Documentation Files

#### `DUAL_PSU_README.md` - This Complete Guide
**What it is:**
- **Master documentation** explaining the entire system
- Step-by-step setup instructions
- Complete API reference
- Troubleshooting guide
- Examples for every use case

**When to read:**
- First time setting up the system
- Understanding how all pieces fit together
- Looking up API endpoints
- Troubleshooting problems
- Planning your integration

---

## 🔄 How the Files Work Together

### Scenario 1: Direct Python Control (Research/Automation)
```
Your Script → run_psu_multi.py → heinzinger_control.so → USB Hardware
                    ↑                    ↑                    ↑
              Python Module        Compiled C++        Physical PSU
```

**Example workflow:**
1. Your script imports `run_psu_multi`
2. `run_psu_multi` loads the compiled C++ module
3. C++ module talks to USB interface boards
4. Interface boards control the actual PSUs

**Use files:** `your_script.py` + `run_psu_multi.py` + `heinzinger_control.so`

### Scenario 2: LabVIEW Integration (Remote Control)
```
LabVIEW → HTTP/JSON → dual_psu_service.py → run_psu_multi.py → heinzinger_control.so → USB Hardware
   ↑           ↑              ↑                    ↑                    ↑                    ↑
Your VI    Network      Web Service         Python Module        Compiled C++        Physical PSU
```

**Example workflow:**
1. LabVIEW sends HTTP POST to `/heinzinger/set_voltage`
2. `dual_psu_service.py` receives the request
3. Web service calls `run_psu_multi.py` functions
4. Python module uses C++ code to control hardware

**Use files:** Your LabVIEW VI + `dual_psu_service.py` + `run_psu_multi.py` + `heinzinger_control.so`

### Scenario 3: Development Without Hardware
```
LabVIEW → HTTP/JSON → mock_dual_psu_service.py → (Simulated PSU states in memory)
   ↑           ↑              ↑                            ↑
Your VI    Network      Mock Service              No real hardware needed
```

**Example workflow:**
1. LabVIEW sends same HTTP requests as production
2. `mock_dual_psu_service.py` simulates PSU responses
3. Perfect for testing your LabVIEW code

**Use files:** Your LabVIEW VI + `mock_dual_psu_service.py`

### Scenario 4: Quick Interactive Testing
```
Terminal → run_psu.py → heinzinger_control.so → USB Hardware
    ↑           ↑              ↑                    ↑
User input  Legacy module  Compiled C++        Physical PSU
```

**Example workflow:**
1. Run `python3 run_psu.py`
2. Type commands like `setv 1000`, `on`, `read`
3. Direct control of one PSU

**Use files:** `run_psu.py` + `heinzinger_control.so`

## Installation and Setup

### 1. Build the C++ Module
```bash
cd /path/to/ADCBoardControlPython
mkdir -p build
cd build
cmake ..
make -j$(nproc)
```

### 2. Install Python Dependencies
```bash
pip install flask requests
```

### 3. Connect Hardware
- Connect Heinzinger PSU to USB interface board #1
- Connect FUG PSU to USB interface board #2
- Connect both USB interface boards to Raspberry Pi
- Ensure both boards enumerate as separate USB devices

## Usage

### Starting the Service
```bash
python dual_psu_service.py
```

The service will start on `http://0.0.0.0:5000` and automatically initialize both PSUs when first accessed.

### API Endpoints

#### Service Information
- `GET /` - Service information and available endpoints
- `GET /status` - Status of both PSUs including current readings

#### Heinzinger PSU (30kV/2mA, device_index=0)
- `POST /heinzinger/set_voltage` - Set voltage (JSON: `{"value": 1000.0}`)
- `POST /heinzinger/set_current` - Set current limit (JSON: `{"value": 1.5}`)
- `GET /heinzinger/read` - Read voltage, current, and relay state
- `GET /heinzinger/relay` - Get relay state (JSON: `{"on": true/false}`)
- `POST /heinzinger/relay` - Set relay state (JSON: `{"state": true/false}`)

#### FUG PSU (50kV/0.5mA, device_index=1)
- `POST /fug/set_voltage` - Set voltage (JSON: `{"value": 2000.0}`)
- `POST /fug/set_current` - Set current limit (JSON: `{"value": 0.3}`)
- `GET /fug/read` - Read voltage, current, and relay state
- `GET /fug/relay` - Get relay state (JSON: `{"on": true/false}`)
- `POST /fug/relay` - Set relay state (JSON: `{"state": true/false}`)

### LabVIEW Integration

To use with LabVIEW, configure your HTTP requests to use different base URLs:

**Heinzinger PSU:**
- Base URL: `http://raspberry_pi_ip:5000/heinzinger`
- Examples:
  - Set voltage: `POST /heinzinger/set_voltage` with `{"value": 1000.0}`
  - Read values: `GET /heinzinger/read`
  - Turn on: `POST /heinzinger/relay` with `{"state": true}`

**FUG PSU:**
- Base URL: `http://raspberry_pi_ip:5000/fug`
- Examples:
  - Set voltage: `POST /fug/set_voltage` with `{"value": 2000.0}`
  - Read values: `GET /fug/read`
  - Turn on: `POST /fug/relay` with `{"state": true}`

## Testing

### Without Hardware
```bash
# Start the service (will show initialization errors but endpoints will work)
python dual_psu_service.py

# In another terminal, run the test script
python test_dual_psu.py
```

### With Hardware
1. Ensure both USB interface boards are connected
2. Start the service: `python dual_psu_service.py`
3. Check status: `curl http://localhost:5000/status`
4. Test individual PSUs:
   ```bash
   # Heinzinger
   curl -X POST http://localhost:5000/heinzinger/set_voltage -d '{"value": 1000}' -H "Content-Type: application/json"
   curl http://localhost:5000/heinzinger/read
   
   # FUG
   curl -X POST http://localhost:5000/fug/set_voltage -d '{"value": 2000}' -H "Content-Type: application/json"
   curl http://localhost:5000/fug/read
   ```

## Safety Features

- **Range Validation**: Each PSU enforces its specific voltage/current limits
- **Independent Control**: PSUs operate completely independently
- **Error Handling**: Comprehensive error reporting for communication failures
- **Graceful Degradation**: Service continues to work even if one PSU fails

## Configuration

### PSU Specifications
Edit `dual_psu_service.py` to modify PSU configurations:

```python
PSU_CONFIGS = {
    "heinzinger": {
        "device_index": 0,
        "max_voltage": 30000.0,  # 30kV
        "max_current": 2.0,      # 2mA
        "max_input_voltage": 10.0,
    },
    "fug": {
        "device_index": 1,
        "max_voltage": 50000.0,  # 50kV
        "max_current": 0.5,      # 0.5mA
        "max_input_voltage": 10.0,
    }
}
```

### Debug Mode
Set `verb=True` in the `get_psu_instance()` calls for detailed C++ logging.

## Troubleshooting

### USB Device Detection
```bash
# Check if USB devices are detected
lsusb | grep "a0a0:000c"

# Should show two devices if both boards are connected
```

### Service Logs
The service prints initialization status and errors. Check console output for:
- "PSU initialized successfully" messages
- USB connection errors
- Module loading issues

### Common Issues
1. **"Module not found"**: Ensure the C++ module is built in the `build/` directory
2. **"USB device not found"**: Check physical connections and device enumeration
3. **"Permission denied"**: May need udev rules or elevated privileges for USB access
4. **Port conflicts**: Ensure port 5000 is available or change in the service

### ⚠️ **Known Issue - "Unable to claim USB interface 1" (FIXED)**
**Error:** `Error: Unable to claim USB interface 1. Libusb error: Entity not found. [-5]`

**Root Cause:** This was a critical bug in the C++ USB interface claiming logic where `device_index` was incorrectly passed as the USB interface number instead of the device skip count.

**Status:** ✅ **FIXED** in the current codebase. If you encounter this error, ensure you have the latest `Heinzinger.cpp` with the corrected `OpenDevice()` call.

**Technical Details:** The fix changed `OpenDevice(VID, PID, device_index)` to `OpenDevice(VID, PID, 0, device_index)` to properly specify USB interface 0 for all devices.

### 💻 **Platform Differences - Mac vs Raspberry Pi**

**Issue Discovered:** The dual PSU system works differently on Mac vs Raspberry Pi due to USB subsystem differences.

**Mac Behavior:**
- ✅ Both PSUs initialize in any order
- ✅ More permissive USB resource sharing
- ✅ Better USB driver isolation
- ✅ Handles multiple libusb contexts gracefully

**Raspberry Pi Behavior:**
- ❌ Device 1 fails if initialized after Device 0
- ❌ Stricter USB resource management
- ❌ USB contexts don't release properly between devices
- ✅ Works if Device 1 (FUG) initialized FIRST

**Root Cause:** Pi's USB subsystem doesn't fully release libusb resources when the first device cleanup occurs, causing "Resource busy" errors for the second device.

**Universal Solution:** Initialize devices in this order on both platforms:
1. **Device 1 (FUG) FIRST** - needs clean USB state
2. **Device 0 (Heinzinger) SECOND** - more tolerant of used USB state

**Status:** ✅ **WORKING** on both Mac and Pi with unified initialization order.

## Migration from Single PSU

If you're migrating from the original single PSU system:

1. **LabVIEW Changes**: Update base URLs from `http://pi:5000/` to `http://pi:5000/heinzinger/` or `http://pi:5000/fug/`
2. **JSON Format**: No changes needed - same JSON structure for all endpoints
3. **Backward Compatibility**: The original `run_psu_service.py` can still run independently for single PSU operation

## 🐛 **CRITICAL BUG FIX - Dual PSU USB Issue RESOLVED**

**Problem:** Second device failed with `Error: Unable to claim USB interface 1. Libusb error: Entity not found. [-5]`

**Root Cause:** In `Heinzinger.cpp` line 42-43, `device_index` was incorrectly passed as the USB interface number instead of device skip count.

**Fix:** Changed `OpenDevice(0xA0A0, 0x000C, device_index)` to `OpenDevice(0xA0A0, 0x000C, 0, device_index)`

**Status:** ✅ **SOLVED** - Both PSUs now initialize and control simultaneously.

---

## Next Steps

1. ✅ **COMPLETED:** Dual PSU USB initialization bug fixed
2. ✅ **WORKING:** Test the system on your Mac with both interface boards
3. ✅ **COMPLETED:** Copy working files to your Raspberry Pi  
4. ✅ **WORKING:** Test with actual hardware - both PSUs initialize successfully
5. Update your LabVIEW program to use the new endpoints:
   - Heinzinger: `http://pi_ip:5001/heinzinger/*`
   - FUG: `http://pi_ip:5001/fug/*`
6. Enjoy simultaneous control of both PSUs! 🎉

**System Status:** ✅ **FULLY OPERATIONAL** on both Mac and Raspberry Pi
