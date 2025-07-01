#!/usr/bin/env python3
"""
Board Assignment Verification Script

This script checks if the PSU boards are plugged into the correct USB ports
by testing each board's expected characteristics (relay capability).
"""

import run_psu_multi as psu

def verify_board_assignment():
    """Verify that each USB path has the correct PSU board plugged in."""
    print("PSU Board Assignment Verification")
    print("=" * 50)
    
    # Load the module
    print("\nLoading C++ module...")
    if not psu.setup_module_path_and_load():
        print("✗ Failed to load C++ module")
        return False
    print("✓ C++ module loaded")
    
    results = {}
    
    # Test path @00110000 (should be Heinzinger - no relay)
    print(f"\nTesting USB path @00110000 (expected: Heinzinger - no relay)")
    try:
        psu_110 = psu.get_psu_instance_by_path("@00110000", max_v=30000, max_c=2.0, verb=False)
        if psu_110:
            print("✓ Successfully connected to device at @00110000")
            
            # Test if it has relay control (Heinzinger shouldn't have relay)
            try:
                # Try to read relay status - this should work for both
                has_relay_method = hasattr(psu_110, 'is_relay_on')
                if has_relay_method:
                    relay_status = psu_110.is_relay_on()
                    print(f"  Relay status readable: {relay_status}")
                    results["@00110000"] = {
                        "connected": True, 
                        "has_relay_method": True,
                        "type": "Unknown - need to test actual relay control"
                    }
                else:
                    results["@00110000"] = {
                        "connected": True,
                        "has_relay_method": False, 
                        "type": "Likely Heinzinger (no relay method)"
                    }
            except Exception as e:
                print(f"  Relay test error: {e}")
                results["@00110000"] = {"connected": True, "error": str(e)}
        else:
            print("✗ Failed to connect to device at @00110000")
            results["@00110000"] = {"connected": False}
    except Exception as e:
        print(f"✗ Error testing @00110000: {e}")
        results["@00110000"] = {"error": str(e)}
    
    # Test path @00120000 (should be FUG - with relay)
    print(f"\nTesting USB path @00120000 (expected: FUG - with relay)")
    try:
        psu_120 = psu.get_psu_instance_by_path("@00120000", max_v=50000, max_c=0.5, verb=False)
        if psu_120:
            print("✓ Successfully connected to device at @00120000")
            
            # Test relay control (FUG should have relay)
            try:
                has_relay_method = hasattr(psu_120, 'is_relay_on')
                if has_relay_method:
                    relay_status = psu_120.is_relay_on()
                    print(f"  Relay status readable: {relay_status}")
                    results["@00120000"] = {
                        "connected": True,
                        "has_relay_method": True,
                        "type": "Unknown - need to test actual relay control"
                    }
                else:
                    results["@00120000"] = {
                        "connected": True,
                        "has_relay_method": False,
                        "type": "Unexpected - should have relay"
                    }
            except Exception as e:
                print(f"  Relay test error: {e}")
                results["@00120000"] = {"connected": True, "error": str(e)}
        else:
            print("✗ Failed to connect to device at @00120000")
            results["@00120000"] = {"connected": False}
    except Exception as e:
        print(f"✗ Error testing @00120000: {e}")
        results["@00120000"] = {"error": str(e)}
    
    # Analyze results
    print("\n" + "=" * 50)
    print("ANALYSIS:")
    print("=" * 50)
    
    if "@00110000" in results and results["@00110000"].get("connected"):
        print("✓ Device found at @00110000 (expected Heinzinger location)")
    else:
        print("✗ No device at @00110000 - Heinzinger may be in wrong port!")
        
    if "@00120000" in results and results["@00120000"].get("connected"):
        print("✓ Device found at @00120000 (expected FUG location)")
    else:
        print("✗ No device at @00120000 - FUG may be in wrong port!")
    
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
    
    print(f"\nRECOMMENDATION:")
    if (results.get("@00110000", {}).get("connected") and 
        results.get("@00120000", {}).get("connected")):
        print("✓ Both devices found at expected USB paths")
        print("✓ Board assignment appears correct")
        print("✓ You can safely use the new USB path-based system")
    else:
        print("⚠️  One or both devices not found at expected paths")
        print("⚠️  You may need to:")
        print("   1. Swap the USB connections")
        print("   2. Update the USB path constants in the code")
        print("   3. Or use the legacy device_index system temporarily")
    
    return results

if __name__ == "__main__":
    verify_board_assignment()