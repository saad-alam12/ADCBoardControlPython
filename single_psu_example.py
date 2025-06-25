#!/usr/bin/env python3
"""
Single PSU Direct Control Example
Shows how to control one PSU directly from Python using the new multi-PSU module
"""

import time
import run_psu_multi as psu

def main():
    print("Single PSU Direct Control Example")
    print("=" * 40)
    
    # Configuration for your PSU
    DEVICE_INDEX = 0        # 0 for first PSU, 1 for second PSU  
    MAX_VOLTAGE = 30000.0   # 30kV for Heinzinger, 50kV for FUG
    MAX_CURRENT = 2.0       # 2mA for Heinzinger, 0.5mA for FUG
    
    print(f"Initializing PSU on device {DEVICE_INDEX}...")
    
    # Get PSU instance (automatically initializes if needed)
    psu_instance = psu.get_psu_instance(
        device_index=DEVICE_INDEX,
        max_v=MAX_VOLTAGE,
        max_c=MAX_CURRENT,
        verb=True,  # Set to False to reduce output
        max_in_v=10.0
    )
    
    if psu_instance is None:
        print("ERROR: Failed to initialize PSU. Check hardware connections.")
        return
    
    print("PSU initialized successfully!")
    
    try:
        # Example operations
        print("\n--- PSU Operations ---")
        
        # Read initial state
        print("Reading initial state...")
        voltage = psu_instance.read_voltage()
        current = psu_instance.read_current()
        relay_on = psu_instance.is_relay_on()
        print(f"Initial: {voltage:.1f}V, {current:.3f}mA, Relay: {'ON' if relay_on else 'OFF'}")
        
        # Set voltage to 1000V
        print("\nSetting voltage to 1000V...")
        if psu_instance.set_voltage(1000.0):
            print("Voltage set successfully")
        else:
            print("Failed to set voltage")
        
        # Set current limit to 1mA
        print("Setting current limit to 1mA...")
        if psu_instance.set_current(1.0):
            print("Current limit set successfully")
        else:
            print("Failed to set current limit")
        
        # Turn PSU on
        print("Turning PSU ON...")
        if psu_instance.switch_on():
            print("PSU turned ON successfully")
        else:
            print("Failed to turn PSU ON")
        
        # Wait and read values
        time.sleep(1)
        voltage = psu_instance.read_voltage()
        current = psu_instance.read_current()
        relay_on = psu_instance.is_relay_on()
        print(f"After setup: {voltage:.1f}V, {current:.3f}mA, Relay: {'ON' if relay_on else 'OFF'}")
        
        # Interactive control
        print("\n--- Interactive Control ---")
        print("Commands: setv <volts>, setc <mA>, on, off, read, quit")
        
        while True:
            try:
                cmd = input("\nEnter command: ").strip().lower()
                
                if cmd == 'quit':
                    break
                elif cmd.startswith('setv '):
                    v = float(cmd.split()[1])
                    if psu_instance.set_voltage(v):
                        print(f"Set voltage to {v}V")
                    else:
                        print(f"Failed to set voltage to {v}V")
                        
                elif cmd.startswith('setc '):
                    c = float(cmd.split()[1])
                    if psu_instance.set_current(c):
                        print(f"Set current limit to {c}mA")
                    else:
                        print(f"Failed to set current limit to {c}mA")
                        
                elif cmd == 'on':
                    if psu_instance.switch_on():
                        print("PSU turned ON")
                    else:
                        print("Failed to turn PSU ON")
                        
                elif cmd == 'off':
                    if psu_instance.switch_off():
                        print("PSU turned OFF")
                    else:
                        print("Failed to turn PSU OFF")
                        
                elif cmd == 'read':
                    v = psu_instance.read_voltage()
                    c = psu_instance.read_current()
                    relay = psu_instance.is_relay_on()
                    print(f"Read: {v:.1f}V, {c:.3f}mA, Relay: {'ON' if relay else 'OFF'}")
                    
                else:
                    print("Unknown command. Use: setv <volts>, setc <mA>, on, off, read, quit")
                    
            except (ValueError, IndexError):
                print("Invalid command format")
            except KeyboardInterrupt:
                print("\nCtrl+C pressed")
                break
                
    except Exception as e:
        print(f"Error during operation: {e}")
        
    finally:
        # Clean shutdown
        print("\nShutting down...")
        psu_instance.switch_off()
        psu.cleanup_psu(DEVICE_INDEX)
        print("PSU control finished.")

if __name__ == "__main__":
    main()
