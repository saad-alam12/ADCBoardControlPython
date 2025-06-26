# ADC Board Control Python - Complete System Overview

Your codebase is a **multi-layer power supply control system** that bridges high-voltage laboratory equipment with modern software interfaces. Here's how it all works together:

## 🏗️ **System Architecture (4 Layers)**

### **Layer 1: Hardware Interface (C++)**
**Files:** `Heinzinger.cpp`, `headers/AnalogPSU.h`, `headers/FGUSBBulk.h`

- **USB Communication**: Talks directly to custom USB interface boards (VID: 0xA0A0, PID: 0x000C)
- **16-bit DAC Control**: Converts voltage/current commands to precise analog signals (0-10V)
- **ADC Reading**: Reads actual voltage/current measurements back from PSUs
- **Safety Systems**: Enforces voltage/current limits and handles errors

### **Layer 2: Python Bindings (PyBind11)**
**Files:** `bindings.cpp`, `CMakeLists.txt`

- **Bridge**: Wraps C++ `HeinzingerVia16BitDAC` class as Python `HeinzingerPSU` class
- **Compilation**: Builds into `heinzinger_control.so` (the actual Python module)
- **Type Conversion**: Handles data exchange between C++ and Python seamlessly

### **Layer 3: Python Control Layer**
**Files:** `run_psu_multi.py`, `run_psu.py`

- **Multi-PSU Management**: `run_psu_multi.py` manages multiple PSU instances by device index
- **Resource Management**: Handles module loading, initialization, and cleanup
- **API Abstraction**: Provides clean Python interface for PSU operations

### **Layer 4: User Interfaces**
**Files:** `dual_psu_service.py`, `mock_dual_psu_service.py`, example scripts

- **Web Services**: Flask-based REST APIs for remote control
- **LabVIEW Integration**: HTTP/JSON endpoints for instrument control
- **Direct Scripts**: Python automation and interactive control

## 🔌 **Physical Connection Flow**

```
[Heinzinger 30kV PSU] ←→ [USB Interface Board #1] ←→ [USB] ←→ [Computer]
[FUG 50kV PSU]        ←→ [USB Interface Board #2] ←→ [USB] ←→ [Computer]
                                                              ↓
                                                    [Your Control Software]
```

## 🔄 **Data Flow Examples**

### **Direct Python Control:**
```
Your Script → run_psu_multi.py → heinzinger_control.so → USB Hardware → PSU
```

### **LabVIEW Integration:**
```
LabVIEW → HTTP/JSON → dual_psu_service.py → run_psu_multi.py → Hardware
```

## 🎯 **Key Components Explained**

### **Multi-PSU Support (`run_psu_multi.py:19-117`)**
- **Device Index System**: Each PSU gets a unique `device_index` (0, 1, 2...)
- **Instance Management**: `_psu_instances` dictionary stores multiple PSU objects
- **Automatic Initialization**: `get_psu_instance()` creates PSUs on-demand with specific specs

### **Web Service Architecture (`dual_psu_service.py:13-31`)**
- **Separate Endpoints**: `/heinzinger/*` and `/fug/*` for different PSU types
- **Individual Limits**: Each PSU enforces its own voltage/current specifications
- **Relay Differences**: Heinzinger has no relay control, FUG has full relay control

### **Safety & Error Handling**
- **Range Validation**: Each PSU enforces specific voltage/current limits
- **Hardware Abstraction**: Same Python API works with different PSU hardware
- **Graceful Degradation**: System continues working even if one PSU fails

## 🚀 **Usage Patterns**

### **For Research/Automation:**
Use `run_psu_multi.py` directly in your Python scripts

### **For LabVIEW Integration:**
Run `dual_psu_service.py` and send HTTP requests to control PSUs remotely

### **For Development/Testing:**
Use `mock_dual_psu_service.py` to test without hardware

The system is designed to be **flexible, safe, and scalable** - you can control one PSU or multiple PSUs, use it directly from Python or remotely via web APIs, and easily add support for additional PSU types.