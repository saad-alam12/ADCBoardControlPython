#!/usr/bin/env python3
"""
Simple PSU Script Example
Basic script to set voltage, current, and turn PSU on/off
"""

import time
import run_psu_multi as psu

def control_psu():
    """Simple PSU control function"""
    
    # Configuration
    DEVICE_INDEX = 0        # Change to 1 for second PSU
    MAX_VOLTAGE = 30000.0   # 30kV for Heinzinger, 50kV for FUG  
    MAX_CURRENT = 2.0       # 2mA for Heinzinger, 0.5mA for FUG
    
    # Initialize PSU
    print("Initializing PSU...")
    psu_instance = psu.get_psu_instance(
        device_index=DEVICE_INDEX,
        max_v=MAX_VOLTAGE,
        max_c=MAX_CURRENT,
        verb=False  # Quiet mode
    )
    
    if psu_instance is None:
        print("ERROR: Failed to initialize PSU")
        return False
    
    try:
        # Your PSU operations here
        print("Setting up PSU...")
        
        # Set voltage to 5kV
        if not psu_instance.set_voltage(0):
            print("Failed to set voltage")
            return False
        print("Voltage set to 5kV")
        
        # Set current limit to 1mA
        if not psu_instance.set_current(1.0):
            print("Failed to set current")
            return False
        print("Current limit set to 1mA")
        
        # Turn PSU on
        if not psu_instance.switch_on():
            print("Failed to turn PSU on")
            return False
        print("PSU turned ON")
        
        # Wait and read values
        time.sleep(2)
        voltage = psu_instance.read_voltage()
        current = psu_instance.read_current()
        print(f"Measured: {voltage:.1f}V, {current:.3f}mA")
        
        # Do your experiment here...
        print("Running for 5 seconds...")
        time.sleep(5)
        
        # Turn PSU off
        psu_instance.switch_off()
        print("PSU turned OFF")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False
        
    finally:
        # Cleanup
        psu.cleanup_psu(DEVICE_INDEX)

if __name__ == "__main__":
    print("Simple PSU Control Script")
    print("=" * 30)
    
    success = control_psu()
    
    if success:
        print("Script completed successfully")
    else:
        print("Script failed")
