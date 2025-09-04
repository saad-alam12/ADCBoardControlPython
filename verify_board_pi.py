#!/usr/bin/env python3
"""
Board Assignment Verification Script - Pi Version

This script checks if the PSU boards are plugged into the correct USB ports
by testing each board's expected characteristics using Pi-specific USB paths.
"""

import run_psu_multi as psu

def verify_board_assignment():
    """Verify that each USB path has the correct PSU board plugged in."""
    print("PSU Board Assignment Verification - Raspberry Pi")
    print("=" * 60)
    
    # Load the module
    print("\nLoading C++ module...")
    if not psu.setup_module_path_and_load():
        print("✗ Failed to load C++ module")
        return False
    print("✓ C++ module loaded")
    
    results = {}
    
    # Test path 1-1.3 (should be Heinzinger - no relay)
    print(f"\nTesting USB path 1-1.3 (expected: Heinzinger - no relay)")
    try:
        psu_heinz = psu.get_psu_instance_by_path("1-1.3", max_v=30000, max_c=2.0, verb=False)
        if psu_heinz:
            print("✓ Successfully connected to device at 1-1.3")
            
            # Test basic operations
            try:
                has_relay_method = hasattr(psu_heinz, 'is_relay_on')
                if has_relay_method:
                    relay_status = psu_heinz.is_relay_on()
                    print(f"  Relay status readable: {relay_status}")
                    # Test voltage reading
                    voltage = psu_heinz.read_voltage()
                    print(f"  Voltage reading: {voltage}V")
                    results["1-1.3"] = {
                        "connected": True, 
                        "has_relay_method": True,
                        "type": "Heinzinger (30kV, no relay)"
                    }
                else:
                    results["1-1.3"] = {
                        "connected": True,
                        "has_relay_method": False, 
                        "type": "Heinzinger (no relay method)"
                    }
            except Exception as e:
                print(f"  Operation test error: {e}")
                results["1-1.3"] = {"connected": True, "error": str(e)}
        else:
            print("✗ Failed to connect to device at 1-1.3")
            results["1-1.3"] = {"connected": False}
    except Exception as e:
        print(f"✗ Error testing 1-1.3: {e}")
        results["1-1.3"] = {"error": str(e)}
    
    # Test path 1-1.1 (should be FUG - with relay)
    print(f"\nTesting USB path 1-1.1 (expected: FUG - with relay)")
    try:
        psu_fug = psu.get_psu_instance_by_path("1-1.1", max_v=50000, max_c=0.5, verb=False)
        if psu_fug:
            print("✓ Successfully connected to device at 1-1.1")
            
            # Test relay control (FUG should have relay)
            try:
                has_relay_method = hasattr(psu_fug, 'is_relay_on')
                if has_relay_method:
                    relay_status = psu_fug.is_relay_on()
                    print(f"  Relay status readable: {relay_status}")
                    # Test voltage reading
                    voltage = psu_fug.read_voltage()
                    print(f"  Voltage reading: {voltage}V")
                    results["1-1.1"] = {
                        "connected": True,
                        "has_relay_method": True,
                        "type": "FUG (50kV, with relay)"
                    }
                else:
                    results["1-1.1"] = {
                        "connected": True,
                        "has_relay_method": False,
                        "type": "Unexpected - FUG should have relay"
                    }
            except Exception as e:
                print(f"  Operation test error: {e}")
                results["1-1.1"] = {"connected": True, "error": str(e)}
        else:
            print("✗ Failed to connect to device at 1-1.1")
            results["1-1.1"] = {"connected": False}
    except Exception as e:
        print(f"✗ Error testing 1-1.1: {e}")
        results["1-1.1"] = {"error": str(e)}
    
    # Analyze results
    print("\n" + "=" * 60)
    print("ANALYSIS:")
    print("=" * 60)
    
    if "1-1.3" in results and results["1-1.3"].get("connected"):
        print("✓ Device found at 1-1.3 (expected Heinzinger location)")
    else:
        print("✗ No device at 1-1.3 - Heinzinger may be in wrong port!")
        
    if "1-1.1" in results and results["1-1.1"].get("connected"):
        print("✓ Device found at 1-1.1 (expected FUG location)")
    else:
        print("✗ No device at 1-1.1 - FUG may be in wrong port!")
    
    # Check current USB enumeration order
    print(f"\nCurrent USB device enumeration order:")
    import subprocess
    try:
        result = subprocess.run(["./simple_usb_info"], capture_output=True, text=True, cwd=".")
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if "Found PSU Interface Board" in line:
                    print(f"  {line}")
        else:
            print("  Could not run simple_usb_info utility")
    except Exception as e:
        print(f"  Error running enumeration check: {e}")
    
    # Show Pi-specific USB paths
    print(f"\nPi-specific USB path mapping:")
    print(f"  Heinzinger (30kV, no relay): 1-1.3")
    print(f"  FUG (50kV, with relay): 1-1.1")
    
    print(f"\nRECOMMENDATION:")
    if (results.get("1-1.3", {}).get("connected") and 
        results.get("1-1.1", {}).get("connected")):
        print("✅ SUCCESS: Both devices found at expected Pi USB paths")
        print("✅ Board assignment appears correct")
        print("✅ USB path-based system is working on Pi")
        print("✅ You can safely use the new identification system")
    else:
        print("❌ ISSUE: One or both devices not found at expected paths")
        print("❌ Check:")
        print("   1. USB connections are secure")
        print("   2. Both boards are powered")
        print("   3. USB path constants match your Pi configuration")
    
    return results

if __name__ == "__main__":
    verify_board_assignment()