# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build Commands

### C++ Module Compilation
```bash
# Build the Python extension module
mkdir -p build
cd build
cmake ..
make -j$(nproc)
```

### Testing
```bash
# Test the dual PSU web service endpoints
python test_dual_psu.py

# Test individual PSU control (requires hardware)
python single_psu_example.py

# Test multi-PSU functionality
python run_psu_multi.py
```

### Running Services
```bash
# Start dual PSU web service (production with hardware)
python dual_psu_service.py

# Start mock service (development/testing without hardware)
python mock_dual_psu_service.py

# Start single PSU service (legacy)
python run_psu_service.py
```

## Architecture Overview

This is a **multi-layer power supply control system** that bridges high-voltage laboratory equipment with modern software interfaces.

### Layer 1: Hardware Interface (C++)
- **USB Communication**: Direct communication with custom USB interface boards (VID: 0xA0A0, PID: 0x000C)
- **16-bit DAC Control**: Converts voltage/current commands to precise analog signals (0-10V)
- **ADC Reading**: Reads actual voltage/current measurements back from PSUs
- **Safety Systems**: Enforces voltage/current limits and handles errors

### Layer 2: Python Bindings (PyBind11)
- **Bridge**: Wraps C++ `HeinzingerVia16BitDAC` class as Python `HeinzingerPSU` class
- **Compilation**: Builds into `heinzinger_control.so` (the actual Python module)
- **Module Location**: `build/heinzinger_control.cpython-313-darwin.so`

### Layer 3: Python Control Layer
- **Multi-PSU Management**: `run_psu_multi.py` manages multiple PSU instances by device index
- **Resource Management**: Handles module loading, initialization, and cleanup
- **API Abstraction**: Provides clean Python interface for PSU operations

### Layer 4: User Interfaces
- **Web Services**: Flask-based REST APIs for remote control
- **LabVIEW Integration**: HTTP/JSON endpoints for instrument control
- **Direct Scripts**: Python automation and interactive control

## Key Components

### PSU Types and Specifications
- **Heinzinger PSU** (device_index=0): 30kV/2mA, no relay control
- **FUG PSU** (device_index=1): 50kV/0.5mA, has relay control

### Core Python Modules
- **`run_psu_multi.py`**: Modern multi-PSU control engine (recommended for new scripts)
- **`run_psu.py`**: Legacy single-PSU module with interactive CLI
- **`dual_psu_service.py`**: Production web service for both PSUs
- **`mock_dual_psu_service.py`**: Testing web service without hardware

### Web Service Endpoints
- **Heinzinger**: `/heinzinger/set_voltage`, `/heinzinger/set_current`, `/heinzinger/read`, `/heinzinger/relay`
- **FUG**: `/fug/set_voltage`, `/fug/set_current`, `/fug/read`, `/fug/relay`
- **System**: `/status` (both PSUs), `/` (service info)

## Critical Implementation Details

### Multi-PSU USB Interface Bug (RESOLVED)
The system previously had a critical bug where the second PSU would fail with "Unable to claim USB interface 1". This was resolved by fixing the `OpenDevice()` call in `Heinzinger.cpp` to properly specify USB interface 0 for all devices.

### Platform Differences (Mac vs Raspberry Pi)
- **Mac**: Both PSUs initialize in any order
- **Raspberry Pi**: Must initialize Device 1 (FUG) first, then Device 0 (Heinzinger)

### Safety and Error Handling
- Each PSU enforces specific voltage/current limits
- Hardware abstraction allows same Python API for different PSU hardware
- Graceful degradation - system continues working if one PSU fails

## Development Workflow

### For Direct PSU Control
Use `run_psu_multi.py` for scripting and automation:
```python
import run_psu_multi as psu
heinz = psu.get_psu_instance(device_index=0, max_v=30000, max_c=2.0)
heinz.set_voltage(5000)
```

### For LabVIEW Integration
1. Start `dual_psu_service.py` 
2. Send HTTP requests to PSU-specific endpoints
3. Use `mock_dual_psu_service.py` for development/testing

### For Testing
- Use `test_dual_psu.py` to validate web service endpoints
- Use `single_psu_example.py` for hardware testing
- Use mock service for development without hardware

## Common Issues

1. **Module not found**: Ensure C++ module is built in `build/` directory
2. **USB device not found**: Check physical connections and device enumeration
3. **Permission denied**: May need udev rules or elevated privileges for USB access
4. **Dual PSU initialization**: On Raspberry Pi, initialize FUG (device 1) before Heinzinger (device 0)

## Dependencies

- **Python**: Flask, requests (for web services and testing)
- **C++**: libusb-1.0, pybind11
- **Build Tools**: CMake, make