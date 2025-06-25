This project is designed to control one or more Heinzinger power supplies (PSUs) from a computer. Here's a breakdown of how it works:

**Core Functionality (C++)**

*   **Low-Level USB Communication:** The `FGUSBBulk.h` and related files handle the direct communication with a custom USB interface board. This board acts as a bridge between the computer and the analog control signals of the PSU.
*   **Analog PSU Interface:** `AnalogPSU.h` defines a class (`FGAnalogPSUInterface`) that translates high-level commands (like "set voltage") into the specific data packets that the USB interface board understands.
*   **Heinzinger PSU Control:** `Heinzinger.h` and `Heinzinger.cpp` create a `HeinzingerVia16BitDAC` class. This is the main C++ interface for a single PSU. It uses the `FGAnalogPSUInterface` to perform actions like setting voltage/current, switching the output on/off, and reading back measured values. It understands the specifics of the Heinzinger PSU, such as its maximum voltage and current.

**Python Integration**

*   **Python Bindings:** `bindings.cpp` is the key to using the C++ code from Python. It uses a library called `pybind11` to "wrap" the `HeinzingerVia16BitDAC` class, making it available as a Python class called `HeinzingerPSU`. This means you can create and use `HeinzingerPSU` objects directly in your Python scripts as if they were native Python objects.
*   **Build System:** `CMakeLists.txt` and `Makefile` are used to compile the C++ code and the Python bindings into a single shared library file (e.g., `heinzinger_control.cpython-313-darwin.so`). This file is what Python imports to get access to the C++ functionality.

**Python Scripts (How you use it)**

The Python scripts provide different ways to interact with the PSUs:

*   **Direct Control:**
    *   `run_psu.py`: An older script for controlling a single PSU. It has an interactive command-line interface to set voltage, current, etc.
    *   `run_psu_multi.py`: An updated version that can manage multiple PSUs connected to the same computer (each on a different USB device index). It's the foundation for the other scripts.
    *   `single_psu_example.py` and `simple_psu_script.py`: These are clear examples of how to write your own Python scripts to control a PSU for an experiment.

*   **Web-Based Control (Services):** These scripts run a web server (using the Flask framework) to allow controlling the PSUs over a network. This is useful for remote operation or integration with other systems.
    *   `run_psu_service.py`: A simple web service for controlling a single PSU.
    *   `dual_psu_service.py`: A more advanced service that can control two different PSUs (a Heinzinger and a FUG model) simultaneously, each with its own set of web endpoints (e.g., `/heinzinger/set_voltage`, `/fug/set_voltage`).
    *   `dummypsu_service.py`: A "fake" PSU service for testing the web interface without needing the actual hardware connected.
    *   `test_dual_psu.py`: A script to test the `dual_psu_service.py` to make sure all its web endpoints are working correctly.

**In simple terms:**

You have C++ code that knows how to "talk" to the power supply through a special USB adapter. This C++ code is wrapped up so that Python can use it. Then, you have a collection of Python scripts that let you either control the power supply directly from the command line or through a web browser, making it very flexible for different experimental setups. The system is even designed to handle multiple power supplies at once.
