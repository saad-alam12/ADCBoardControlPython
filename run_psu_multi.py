import sys
import os
import time
import subprocess
import sysconfig

# --- Configuration ---
# Path to the directory where your .so module was built
MODULE_BUILD_DIR = os.path.join(os.path.dirname(__file__), 'build')

# The expected name of your compiled module.
MODULE_FILENAME = (
     'heinzinger_control' + sysconfig.get_config_var('EXT_SUFFIX')
)
PYTHON_MODULE_NAME = 'heinzinger_control' 
CPP_CLASS_NAME_IN_PYTHON = 'HeinzingerPSU'

# --- Global variables for PSU instances ---
_psu_instances = {}  # Dictionary to store multiple PSU instances by device_index
_module_loaded = False

def setup_module_path_and_load():
    """Adds the build directory to Python's path and tries to load the module."""
    global _module_loaded

    if _module_loaded:
        return True

    if not os.path.isdir(MODULE_BUILD_DIR):
        print(f"ERROR: Build directory not found at {MODULE_BUILD_DIR}")
        _module_loaded = False
        return False

    sys.path.insert(0, MODULE_BUILD_DIR)
    print(f"Added '{MODULE_BUILD_DIR}' to sys.path.")

    so_file_path = os.path.join(MODULE_BUILD_DIR, MODULE_FILENAME)
    if not os.path.exists(so_file_path):
        print(f"ERROR: Module file not found at {so_file_path}")
        print("Please ensure you've built the module correctly and it's in the build directory.")
        _module_loaded = False
        return False
    else:
        print(f"Module file found at {so_file_path}")

    # Try to import the module
    try:
        module = __import__(PYTHON_MODULE_NAME)
        globals()[PYTHON_MODULE_NAME] = module 
        print(f"Successfully imported '{PYTHON_MODULE_NAME}' module.")
        _module_loaded = True
        return True
    except ImportError as e:
        print(f"ERROR: Failed to import '{PYTHON_MODULE_NAME}' module.")
        print(f"Import error details: {e}")
        _module_loaded = False
        return False
    except Exception as e:
        print(f"An unexpected error occurred during import: {e}")
        _module_loaded = False
        return False

def initialize_psu(device_index=0, max_v=30000.0, max_c=25, verb=False, max_in_v=10.0):
    """Initializes connection to a PSU with specific device index."""
    global _psu_instances
    
    if not _module_loaded:
        print("ERROR: Python module not loaded. Cannot initialize PSU.")
        return False
    
    # Check if PSU for this device index is already initialized
    if device_index in _psu_instances:
        print(f"PSU on device {device_index} already initialized.")
        return True
    
    try:
        # Access the module and class correctly
        psu_module = globals().get(PYTHON_MODULE_NAME)
        if not psu_module:
            print(f"ERROR: Module '{PYTHON_MODULE_NAME}' not found in globals after import.")
            return False
            
        PSUClass = getattr(psu_module, CPP_CLASS_NAME_IN_PYTHON)
        psu_instance = PSUClass(
            device_index=device_index, 
            max_voltage=max_v, 
            max_current=max_c, 
            verbose=verb, 
            max_input_voltage=max_in_v
        )
        
        # Store the instance
        _psu_instances[device_index] = psu_instance
        print(f"PSU C++ object instance created successfully for device {device_index}.")
        
        # Small delay after initialization
        time.sleep(0.1)
        return True
        
    except AttributeError as e:
        print(f"ERROR: Class '{CPP_CLASS_NAME_IN_PYTHON}' not found in module '{PYTHON_MODULE_NAME}'.")
        print(f"Pybind11 binding error or mismatch? Details: {e}")
        return False
    except Exception as e:
        print(f"ERROR during PSU initialization for device {device_index}: {e}")
        return False

def get_psu_instance(device_index=0, max_v=30000.0, max_c=25, verb=False, max_in_v=10.0):
    """
    Get PSU instance for specific device index, initializing if necessary.
    """
    if device_index not in _psu_instances:
        setup_module_path_and_load()
        if not initialize_psu(device_index=device_index, max_v=max_v, max_c=max_c, verb=verb, max_in_v=max_in_v):
            return None
    
    return _psu_instances.get(device_index)

def set_psu_voltage(device_index, voltage):
    """Sets PSU voltage for specific device. Returns True on success, False on error."""
    psu_instance = _psu_instances.get(device_index)
    if psu_instance is None:
        print(f"ERROR: PSU on device {device_index} not initialized.")
        return False
    try:
        print(f"Python: Calling C++ set_voltage({voltage}) for device {device_index}")
        success = psu_instance.set_voltage(float(voltage))
        print(f"Python: C++ set_voltage returned: {success}")
        return success
    except Exception as e:
        print(f"ERROR setting voltage for device {device_index}: {e}")
        return False

def read_psu_voltage(device_index):
    """Reads PSU voltage for specific device."""
    psu_instance = _psu_instances.get(device_index)
    if psu_instance is None:
        print(f"ERROR: PSU on device {device_index} not initialized.")
        raise RuntimeError(f"PSU on device {device_index} not initialized")
    try:
        voltage = psu_instance.read_voltage()
        return voltage
    except Exception as e:
        print(f"ERROR reading voltage for device {device_index}: {e}")
        raise

def set_psu_current(device_index, current):
    """Sets PSU current limit for specific device."""
    psu_instance = _psu_instances.get(device_index)
    if psu_instance is None:
        print(f"ERROR: PSU on device {device_index} not initialized.")
        return False
    try:
        success = psu_instance.set_current(float(current))
        return success
    except Exception as e:
        print(f"ERROR setting current for device {device_index}: {e}")
        return False

def read_psu_current(device_index):
    """Reads PSU current for specific device."""
    psu_instance = _psu_instances.get(device_index)
    if psu_instance is None:
        print(f"ERROR: PSU on device {device_index} not initialized.")
        raise RuntimeError(f"PSU on device {device_index} not initialized")
    try:
        current = psu_instance.read_current()
        return current
    except Exception as e:
        print(f"ERROR reading current for device {device_index}: {e}")
        raise

def switch_psu_on(device_index):
    """Turns the PSU output ON for specific device."""
    psu_instance = _psu_instances.get(device_index)
    if psu_instance is None:
        print(f"ERROR: PSU on device {device_index} not initialized.")
        return False
    try:
        success = psu_instance.switch_on()
        return success
    except Exception as e:
        print(f"ERROR turning PSU on for device {device_index}: {e}")
        return False

def switch_psu_off(device_index):
    """Turns the PSU output OFF for specific device."""
    psu_instance = _psu_instances.get(device_index)
    if psu_instance is None:
        print(f"ERROR: PSU on device {device_index} not initialized.")
        return False
    try:
        success = psu_instance.switch_off()
        return success
    except Exception as e:
        print(f"ERROR turning PSU off for device {device_index}: {e}")
        return False

def is_relay_on(device_index):
    """Check if relay is on for specific device."""
    psu_instance = _psu_instances.get(device_index)
    if psu_instance is None:
        print(f"ERROR: PSU on device {device_index} not initialized.")
        return False
    try:
        return psu_instance.is_relay_on()
    except Exception as e:
        print(f"ERROR checking relay state for device {device_index}: {e}")
        return False

def cleanup_psu(device_index=None):
    """Cleans up PSU resources. If device_index is None, cleans up all."""
    global _psu_instances
    if device_index is None:
        # Clean up all instances
        for idx in list(_psu_instances.keys()):
            cleanup_psu(idx)
    else:
        if device_index in _psu_instances:
            print(f"Cleaning up PSU instance for device {device_index}")
            del _psu_instances[device_index]
        else:
            print(f"PSU instance for device {device_index} already None or not initialized.")
    return True

# Legacy compatibility functions for single PSU operation (device_index=0)
_psu_instance = None  # For backward compatibility

def get_psu_instance_legacy(device_index=0, verb=False):
    """Legacy function for backward compatibility with existing code."""
    global _psu_instance
    _psu_instance = get_psu_instance(device_index=device_index, verb=verb)
    return _psu_instance

# Main execution block (for testing)
if __name__ == '__main__':
    setup_module_path_and_load()

    if not _module_loaded:
        print("\nExiting script as module could not be loaded.")
        sys.exit(1)

    print("\nTesting dual PSU initialization...")
    
    # Test initializing two PSUs
    print("\nInitializing Heinzinger PSU (device 0)...")
    if initialize_psu(device_index=0, max_v=30000.0, max_c=2.0, verb=True):
        print("Heinzinger PSU initialized successfully.")
    else:
        print("Failed to initialize Heinzinger PSU.")
    
    print("\nInitializing FUG PSU (device 1)...")
    if initialize_psu(device_index=1, max_v=50000.0, max_c=0.5, verb=True):
        print("FUG PSU initialized successfully.")
    else:
        print("Failed to initialize FUG PSU.")
    
    print(f"\nTotal PSU instances: {len(_psu_instances)}")
    print(f"Device indices: {list(_psu_instances.keys())}")
    
    # Cleanup
    cleanup_psu()
    print("Test completed.")
