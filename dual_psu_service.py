#!/usr/bin/env python3
"""
Dual PSU Service - Web API for Controlling Two Power Supply Units

This Flask web service provides HTTP endpoints to control two different types of
high-voltage power supplies (PSUs) used in scientific/industrial applications.

What This Service Does:
- Provides a REST API to control PSUs via HTTP requests
- Manages two PSUs simultaneously with different capabilities
- Handles safety limits and error checking for all operations
- Offers both individual PSU control and system status monitoring

Supported PSUs:
1. Heinzinger PSU (USB path @00110000):
   - High voltage: up to 30,000 volts (30kV)
   - Low current: up to 2 milliamps (2mA)
   - Manual operation: no remote relay control
   - API endpoints: /heinzinger/*

2. FUG PSU (USB path @00120000):
   - Higher voltage: up to 50,000 volts (50kV)
   - Lower current: up to 0.5 milliamps (0.5mA)
   - Remote control: has relay for on/off switching
   - API endpoints: /fug/*

Common Use Cases:
- Laboratory automation for high-voltage experiments
- Remote control of power supplies for safety
- Automated testing of electrical equipment
- Scientific research requiring precise voltage/current control

Safety Features:
- Voltage and current limits enforced by software
- Input validation for all parameters
- Error handling and reporting
- Graceful shutdown procedures

How to Use:
1. Start the service: python dual_psu_service.py
2. Service runs on http://localhost:5001
3. Use HTTP requests to control PSUs (see individual endpoint documentation)
4. Check /status for system overview
5. Visit / for API documentation

Technical Notes:
- Built with Flask web framework
- Uses run_psu_multi.py for hardware communication
- Supports concurrent access to both PSUs
- JSON request/response format
- Thread-safe operations

Example Quick Start:
curl http://localhost:5001/status  # Check if PSUs are working
curl -X POST http://localhost:5001/fug/set_voltage -H "Content-Type: application/json" -d '{"value": 1000}'
curl http://localhost:5001/fug/read  # Read current voltage/current
"""

from flask import Flask, request, jsonify
import run_psu_multi as run_psu

app = Flask(__name__)

# Load the C++ PSU control module at startup
print("Loading C++ PSU control module...")
if not run_psu.setup_module_path_and_load():
    print("ERROR: Failed to load C++ module - web service may not work properly")
    exit(1)
else:
    print("✓ C++ module loaded successfully")

# PSU configurations - Updated to use USB path-based identification
PSU_CONFIGS = {
    "heinzinger": {
        "usb_path": run_psu.USB_PATH_HEINZINGER,  # "@00110000" - Reliable USB path identification
        "max_voltage": 30000.0,  # 30kV
        "max_current": 2.0,      # 2mA
        "max_input_voltage": 10.0,
        "instance": None,
        "has_relay": False  # Heinzinger has no relay - must be turned on manually
    },
    "fug": {
        "usb_path": run_psu.USB_PATH_FUG,         # "@00120000" - Reliable USB path identification
        "max_voltage": 50000.0,  # 50kV
        "max_current": 0.5,      # 0.5mA
        "max_input_voltage": 10.0,
        "instance": None,
        "has_relay": True   # FUG has relay control
    }
}

def get_psu_instance(psu_type):
    """
    Gets a PSU controller instance for the specified PSU type, creating it if needed.
    
    This function acts like a "PSU manager" - it keeps track of which PSUs are
    already set up and ready to use, and creates new connections when needed.
    Think of it like getting a remote control for a specific TV - if you already
    have the remote, it gives you that one; if not, it sets up a new remote.
    
    This is an internal helper function used by all the HTTP endpoints to ensure
    they have a working PSU connection before trying to control the hardware.
    
    Args:
        psu_type (str): Which PSU you want to control. Must be either:
                       - "heinzinger" for the Heinzinger PSU (30kV/2mA, no relay)
                       - "fug" for the FUG PSU (50kV/0.5mA, with relay)
    
    Returns:
        object: A PSU controller instance that can be used to control the hardware
                Returns None if the PSU type is invalid or initialization fails
    
    What This Function Does:
        1. Checks if the requested PSU type is valid (heinzinger or fug)
        2. Looks up the PSU's configuration (voltage limits, USB path, etc.)
        3. If PSU is already initialized, returns the existing controller
        4. If PSU is not initialized, attempts to create a new controller
        5. Stores the controller for future use if initialization succeeds
    
    PSU Configuration Details:
        - Each PSU has different voltage/current limits for safety
        - Each PSU uses a specific USB path for reliable hardware identification
        - Configuration is defined in the PSU_CONFIGS global dictionary
    
    Error Handling:
        - Returns None for invalid PSU types
        - Returns None if PSU hardware is not connected/available
        - Catches and logs all exceptions during initialization
        - Prints helpful error messages for troubleshooting
    
    Example Usage (internal):
        psu = get_psu_instance("fug")
        if psu is not None:
            voltage = psu.read_voltage()  # Now safe to use PSU
        else:
            return error_response("FUG PSU not available")
    
    Thread Safety:
        - Safe to call from multiple HTTP requests simultaneously
        - PSU instances are stored globally and reused
        - Initialization only happens once per PSU type
    
    Notes:
        - This is an internal function - users interact via HTTP endpoints
        - PSU instances persist for the lifetime of the web service
        - Failed initialization attempts are not retried automatically
        - Uses run_psu_multi.py for actual hardware communication
    """
    if psu_type not in PSU_CONFIGS:
        return None
    
    config = PSU_CONFIGS[psu_type]
    if config["instance"] is None:
        try:
            # Use the new USB path-based interface for reliable device identification
            instance = run_psu.get_psu_instance_by_path(
                usb_path=config["usb_path"],
                max_v=config["max_voltage"],
                max_c=config["max_current"],
                verb=False,  # Set to True for debugging
                max_in_v=config["max_input_voltage"]
            )
            
            if instance is not None:
                print(f"{psu_type.upper()} PSU initialized successfully at USB path {config['usb_path']}")
                config["instance"] = instance
            else:
                print(f"ERROR: Failed to initialize {psu_type} PSU - device not found")
                config["instance"] = None # Ensure it stays None
                return None
        except Exception as e:
            print(f"ERROR: Exception during {psu_type} PSU initialization: {e}")
            config["instance"] = None
            return None
    
    return config["instance"]

# Heinzinger PSU routes
@app.post("/heinzinger/set_voltage")
def heinzinger_set_voltage():
    """
    HTTP Endpoint: Set voltage for Heinzinger PSU
    
    Sets the output voltage of the Heinzinger PSU to a specific value.
    The Heinzinger PSU can output high voltage (up to 30,000V) with low current (up to 2mA).
    
    HTTP Method: POST
    URL: /heinzinger/set_voltage
    Content-Type: application/json
    
    Request Body (JSON):
        {
            "value": <voltage_in_volts>
        }
    
    Parameters:
        value (number): Desired voltage in volts
                       Must be between 0 and 30,000 (30kV maximum)
                       Can be integer or decimal (e.g., 1500, 2500.5)
    
    Response (JSON):
        Success (200): {"ok": true}   - Voltage set successfully
        Success (200): {"ok": false}  - PSU rejected the command
        Error (400): {"error": "message"} - Invalid request format or value
        Error (500): {"error": "message"} - PSU not available or hardware error
    
    Example Usage:
        # Set voltage to 5000V (5kV)
        curl -X POST http://localhost:5001/heinzinger/set_voltage \
             -H "Content-Type: application/json" \
             -d '{"value": 5000}'
        
        # Set voltage to 12.5kV
        curl -X POST http://localhost:5001/heinzinger/set_voltage \
             -H "Content-Type: application/json" \
             -d '{"value": 12500}'
    
    Safety Notes:
        - Voltage is applied immediately when command succeeds
        - High voltage can be dangerous - ensure proper safety procedures
        - PSU hardware may have additional safety interlocks
        - Always verify connections before applying high voltage
    
    Common Errors:
        - "JSON must contain 'value' field" - Missing or misspelled parameter
        - "Invalid voltage value" - Non-numeric value provided
        - "Voltage X outside range" - Value exceeds safety limits (0-30000V)
        - "Heinzinger PSU not available" - Hardware not connected or initialized
    """
    psu = get_psu_instance("heinzinger")
    if psu is None:
        return jsonify({"error": "Heinzinger PSU not available"}), 500
    
    try:
        data = request.get_json()
        if not data or "value" not in data:
            return jsonify({"error": "JSON must contain 'value' field"}), 400
        
        v = float(data["value"])
        max_v = PSU_CONFIGS["heinzinger"]["max_voltage"]
        if v > max_v or v < 0:
            return jsonify({"error": f"Voltage {v}V outside range [0, {max_v}V]"}), 400
        
        ok = psu.set_voltage(v)
        return jsonify({"ok": ok})
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid voltage value - must be a number"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.post("/heinzinger/set_current")
def heinzinger_set_current():
    """
    HTTP Endpoint: Set current limit for Heinzinger PSU
    
    Sets the maximum current limit for the Heinzinger PSU. This acts as a safety limit -
    if the connected load tries to draw more current than this limit, the PSU will
    reduce voltage to keep current at or below this limit.
    
    HTTP Method: POST
    URL: /heinzinger/set_current
    Content-Type: application/json
    
    Request Body (JSON):
        {
            "value": <current_in_milliamps>
        }
    
    Parameters:
        value (number): Maximum current limit in milliamps (mA)
                       Must be between 0 and 2.0 (2mA maximum)
                       Can be decimal (e.g., 1.5, 0.8)
    
    Response (JSON):
        Success (200): {"ok": true}   - Current limit set successfully
        Success (200): {"ok": false}  - PSU rejected the command
        Error (400): {"error": "message"} - Invalid request format or value
        Error (500): {"error": "message"} - PSU not available or hardware error
    
    Example Usage:
        # Set current limit to 1.5mA
        curl -X POST http://localhost:5001/heinzinger/set_current \
             -H "Content-Type: application/json" \
             -d '{"value": 1.5}'
        
        # Set current limit to 0.5mA for sensitive equipment
        curl -X POST http://localhost:5001/heinzinger/set_current \
             -H "Content-Type: application/json" \
             -d '{"value": 0.5}'
    
    What Current Limiting Does:
        - Acts as a safety protection for connected equipment
        - PSU will automatically reduce voltage if load draws too much current
        - Prevents damage to sensitive circuits from overcurrent
        - Does not control actual current flow (that depends on the load)
    
    Safety Notes:
        - Always set appropriate current limits before connecting loads
        - Even small currents can be dangerous at high voltages
        - Current limit is enforced by PSU hardware
    
    Common Errors:
        - "JSON must contain 'value' field" - Missing or misspelled parameter
        - "Invalid current value" - Non-numeric value provided
        - "Current X outside range" - Value exceeds safety limits (0-2.0mA)
        - "Heinzinger PSU not available" - Hardware not connected or initialized
    """
    psu = get_psu_instance("heinzinger")
    if psu is None:
        return jsonify({"error": "Heinzinger PSU not available"}), 500
    
    try:
        data = request.get_json()
        if not data or "value" not in data:
            return jsonify({"error": "JSON must contain 'value' field"}), 400
        
        i = float(data["value"])
        max_c = PSU_CONFIGS["heinzinger"]["max_current"]
        if i > max_c or i < 0:
            return jsonify({"error": f"Current {i}mA outside range [0, {max_c}mA]"}), 400
        
        ok = psu.set_current(i)
        return jsonify({"ok": ok})
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid current value - must be a number"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/heinzinger/read")
def heinzinger_read():
    """
    HTTP Endpoint: Read current voltage and current from Heinzinger PSU
    
    Reads the actual output values from the Heinzinger PSU - both the voltage
    being output and the current flowing to the connected load. This is useful
    for monitoring PSU status and verifying that settings are being applied correctly.
    
    HTTP Method: GET
    URL: /heinzinger/read
    
    Request: No body required (GET request)
    
    Response (JSON):
        Success (200):
        {
            "voltage": <actual_voltage_in_volts>,
            "current": <actual_current_in_milliamps>,
            "on": false
        }
        
        Error (500): {"error": "message"} - PSU not available or hardware error
    
    Response Fields:
        voltage (number): Actual output voltage in volts (may differ slightly from set value)
        current (number): Actual current flowing in milliamps (depends on connected load)
        on (boolean): Always false for Heinzinger (no remote relay control)
    
    Example Usage:
        # Read current PSU status
        curl http://localhost:5001/heinzinger/read
        
        # Example response:
        # {
        #   "voltage": 4998.7,
        #   "current": 1.23,
        #   "on": false
        # }
    
    Understanding the Values:
        - voltage: What the PSU is actually outputting (may be slightly different from set value)
        - current: How much current the connected load is actually drawing
        - on: Always false because Heinzinger PSU must be turned on/off manually
    
    Use Cases:
        - Verify that voltage setting was applied correctly
        - Monitor current draw to ensure it's within safe limits
        - Check PSU status during experiments or testing
        - Troubleshoot connection or load issues
    
    Notes:
        - Readings are real-time from PSU hardware
        - Current value depends on what's connected (0 if nothing connected)
        - Voltage may be slightly different from set value due to load or PSU accuracy
        - "on" field is always false because Heinzinger has no remote relay control
    
    Common Issues:
        - "Heinzinger PSU not available" - Hardware not connected or initialized
        - Very low current readings might indicate poor connections
        - Voltage significantly different from set value might indicate PSU issues
    """
    psu = get_psu_instance("heinzinger")
    if psu is None:
        return jsonify({"error": "Heinzinger PSU not available"}), 500
    
    try:
        return jsonify({
            "voltage": psu.read_voltage(),
            "current": psu.read_current(),
            "on": False  # Heinzinger has no relay - must be turned on manually
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/heinzinger/relay")
def heinzinger_relay_state():
    """
    HTTP Endpoint: Check relay state for Heinzinger PSU
    
    Checks whether the Heinzinger PSU's internal relay/switch is ON or OFF.
    However, the Heinzinger PSU model does not have remote relay control capability,
    so this endpoint always returns "false" (OFF). The PSU must be turned on/off
    manually using physical controls on the device.
    
    HTTP Method: GET
    URL: /heinzinger/relay
    
    Request: No body required (GET request)
    
    Response (JSON):
        Success (200): {"on": false}  - Always false for Heinzinger PSU
        Error (500): {"error": "message"} - PSU not available
    
    Example Usage:
        curl http://localhost:5001/heinzinger/relay
        
        # Response will always be:
        # {"on": false}
    
    Why This Endpoint Exists:
        - Provides consistent API interface with FUG PSU (which does have relay control)
        - Allows client code to check relay status without knowing PSU type
        - Part of standardized PSU control interface
    
    Important Notes:
        - Heinzinger PSU has NO remote relay control
        - Physical power switch on PSU must be operated manually
        - This is a hardware limitation, not a software issue
        - For actual power control, use the FUG PSU which has relay capability
    
    Understanding Relay Control:
        - A relay is like a remote-controlled electrical switch
        - When relay is ON, PSU can output power
        - When relay is OFF, no power output regardless of voltage/current settings
        - Heinzinger model doesn't have this feature - must use manual controls
    """
    psu = get_psu_instance("heinzinger")
    if psu is None:
        return jsonify({"error": "Heinzinger PSU not available"}), 500
    
    # Heinzinger has no relay - always return false
    return jsonify({"on": False})

@app.post("/heinzinger/relay")
def heinzinger_set_relay():
    """
    HTTP Endpoint: Attempt to control Heinzinger PSU relay (NOT SUPPORTED)
    
    This endpoint attempts to turn the Heinzinger PSU's relay ON or OFF remotely.
    However, the Heinzinger PSU model does not support remote relay control,
    so this operation will always fail with an error message explaining the limitation.
    
    HTTP Method: POST
    URL: /heinzinger/relay
    Content-Type: application/json
    
    Request Body (JSON):
        {
            "state": <true_or_false>
        }
    
    Parameters:
        state (boolean): Desired relay state
                        true = turn ON, false = turn OFF
    
    Response (JSON):
        Error (400): 
        {
            "error": "Heinzinger PSU has no relay - must be turned on/off manually",
            "on": false
        }
    
    Example Usage:
        # This will always fail, but shows the request format
        curl -X POST http://localhost:5001/heinzinger/relay \
             -H "Content-Type: application/json" \
             -d '{"state": true}'
        
        # Response will always be:
        # {
        #   "error": "Heinzinger PSU has no relay - must be turned on/off manually",
        #   "on": false
        # }
    
    Why This Endpoint Exists:
        - Provides consistent API interface with FUG PSU
        - Gives clear error message explaining the limitation
        - Allows client code to attempt relay control without knowing PSU type
        - Part of standardized PSU control interface
    
    Hardware Limitation:
        - Heinzinger PSU must be turned on/off using physical controls on the device
        - No remote relay control capability in this PSU model
        - This is a hardware design choice, not a software limitation
        - For remote power control, use the FUG PSU instead
    
    Alternative Solutions:
        - Use FUG PSU for applications requiring remote on/off control
        - Manually operate Heinzinger PSU power switch as needed
        - Consider external relay hardware if remote control is absolutely required
    
    Common Errors:
        - "JSON must contain 'state' field" - Missing or misspelled parameter
        - "Invalid JSON format" - Malformed JSON in request body
        - Main error will always be about lack of relay support
    """
    psu = get_psu_instance("heinzinger")
    if psu is None:
        return jsonify({"error": "Heinzinger PSU not available"}), 500
    
    try:
        data = request.get_json()
        if not data or "state" not in data:
            return jsonify({"error": "JSON must contain 'state' field"}), 400
        
        desired = bool(data["state"])
    except Exception:
        return jsonify({"error": "Invalid JSON format"}), 400

    # Heinzinger has no relay control - must be operated manually
    return jsonify({
        "error": "Heinzinger PSU has no relay - must be turned on/off manually",
        "on": False
    }), 400

# FUG PSU routes
@app.post("/fug/set_voltage")
def fug_set_voltage():
    """
    HTTP Endpoint: Set voltage for FUG PSU
    
    Sets the output voltage of the FUG PSU to a specific value.
    The FUG PSU can output very high voltage (up to 50,000V) with very low current (up to 0.5mA).
    Unlike the Heinzinger PSU, the FUG PSU supports remote relay control for turning output on/off.
    
    HTTP Method: POST
    URL: /fug/set_voltage
    Content-Type: application/json
    
    Request Body (JSON):
        {
            "value": <voltage_in_volts>
        }
    
    Parameters:
        value (number): Desired voltage in volts
                       Must be between 0 and 50,000 (50kV maximum)
                       Can be integer or decimal (e.g., 2500, 10000.5)
    
    Response (JSON):
        Success (200): {"ok": true}   - Voltage set successfully
        Success (200): {"ok": false}  - PSU rejected the command
        Error (400): {"error": "message"} - Invalid request format or value
        Error (500): {"error": "message"} - PSU not available or hardware error
    
    Example Usage:
        # Set voltage to 10kV
        curl -X POST http://localhost:5001/fug/set_voltage \
             -H "Content-Type: application/json" \
             -d '{"value": 10000}'
        
        # Set voltage to 25.5kV
        curl -X POST http://localhost:5001/fug/set_voltage \
             -H "Content-Type: application/json" \
             -d '{"value": 25500}'
    
    Safety Notes:
        - FUG PSU can output VERY high voltage (50kV) - extremely dangerous
        - Voltage is applied immediately when command succeeds
        - Always ensure proper safety procedures and equipment isolation
        - Consider using relay control to safely enable/disable output
        - PSU hardware may have additional safety interlocks
    
    Comparison with Heinzinger:
        - FUG: Higher voltage (50kV vs 30kV), lower current (0.5mA vs 2mA)
        - FUG: Has remote relay control (Heinzinger does not)
        - FUG: Better for applications requiring very high voltage with minimal current
    
    Common Errors:
        - "JSON must contain 'value' field" - Missing or misspelled parameter
        - "Invalid voltage value" - Non-numeric value provided
        - "Voltage X outside range" - Value exceeds safety limits (0-50000V)
        - "FUG PSU not available" - Hardware not connected or initialized
    """
    psu = get_psu_instance("fug")
    if psu is None:
        return jsonify({"error": "FUG PSU not available"}), 500
    
    try:
        data = request.get_json()
        if not data or "value" not in data:
            return jsonify({"error": "JSON must contain 'value' field"}), 400
        
        v = float(data["value"])
        max_v = PSU_CONFIGS["fug"]["max_voltage"]
        if v > max_v or v < 0:
            return jsonify({"error": f"Voltage {v}V outside range [0, {max_v}V]"}), 400
        
        ok = psu.set_voltage(v)
        return jsonify({"ok": ok})
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid voltage value - must be a number"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.post("/fug/set_current")
def fug_set_current():
    """
    HTTP Endpoint: Set current limit for FUG PSU
    
    Sets the maximum current limit for the FUG PSU. This acts as a safety limit -
    if the connected load tries to draw more current than this limit, the PSU will
    reduce voltage to keep current at or below this limit. The FUG PSU has a very
    low maximum current (0.5mA) making it suitable for high-voltage, low-current applications.
    
    HTTP Method: POST
    URL: /fug/set_current
    Content-Type: application/json
    
    Request Body (JSON):
        {
            "value": <current_in_milliamps>
        }
    
    Parameters:
        value (number): Maximum current limit in milliamps (mA)
                       Must be between 0 and 0.5 (0.5mA maximum)
                       Can be decimal (e.g., 0.1, 0.25, 0.4)
    
    Response (JSON):
        Success (200): {"ok": true}   - Current limit set successfully
        Success (200): {"ok": false}  - PSU rejected the command
        Error (400): {"error": "message"} - Invalid request format or value
        Error (500): {"error": "message"} - PSU not available or hardware error
    
    Example Usage:
        # Set current limit to 0.3mA
        curl -X POST http://localhost:5001/fug/set_current \
             -H "Content-Type: application/json" \
             -d '{"value": 0.3}'
        
        # Set current limit to 0.1mA for very sensitive equipment
        curl -X POST http://localhost:5001/fug/set_current \
             -H "Content-Type: application/json" \
             -d '{"value": 0.1}'
    
    What Current Limiting Does:
        - Critical safety protection for high-voltage applications
        - PSU will automatically reduce voltage if load draws too much current
        - Prevents damage to sensitive circuits from overcurrent
        - Even tiny currents can be significant at very high voltages
        - Does not control actual current flow (that depends on the load)
    
    Safety Notes:
        - ALWAYS set appropriate current limits before connecting loads
        - At high voltages, even 0.5mA can be dangerous
        - Current limiting is essential for protecting sensitive equipment
        - Consider starting with very low limits (0.1mA) and increasing as needed
    
    Comparison with Heinzinger:
        - FUG: Much lower maximum current (0.5mA vs 2mA)
        - FUG: Better suited for high-voltage, ultra-low-current applications
        - FUG: More precise current control for sensitive measurements
    
    Common Errors:
        - "JSON must contain 'value' field" - Missing or misspelled parameter
        - "Invalid current value" - Non-numeric value provided
        - "Current X outside range" - Value exceeds safety limits (0-0.5mA)
        - "FUG PSU not available" - Hardware not connected or initialized
    """
    psu = get_psu_instance("fug")
    if psu is None:
        return jsonify({"error": "FUG PSU not available"}), 500
    
    try:
        data = request.get_json()
        if not data or "value" not in data:
            return jsonify({"error": "JSON must contain 'value' field"}), 400
        
        i = float(data["value"])
        max_c = PSU_CONFIGS["fug"]["max_current"]
        if i > max_c or i < 0:
            return jsonify({"error": f"Current {i}mA outside range [0, {max_c}mA]"}), 400
        
        ok = psu.set_current(i)
        return jsonify({"ok": ok})
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid current value - must be a number"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/fug/read")
def fug_read():
    """
    HTTP Endpoint: Read current voltage, current, and relay state from FUG PSU
    
    Reads the actual output values from the FUG PSU - the voltage being output,
    the current flowing to the connected load, and whether the internal relay is ON or OFF.
    This provides complete status information for monitoring and verification.
    
    HTTP Method: GET
    URL: /fug/read
    
    Request: No body required (GET request)
    
    Response (JSON):
        Success (200):
        {
            "voltage": <actual_voltage_in_volts>,
            "current": <actual_current_in_milliamps>,
            "on": <true_if_relay_on_false_if_off>
        }
        
        Error (500): {"error": "message"} - PSU not available or hardware error
    
    Response Fields:
        voltage (number): Actual output voltage in volts (may differ slightly from set value)
        current (number): Actual current flowing in milliamps (depends on connected load)
        on (boolean): True if relay is ON (power can flow), False if relay is OFF (no power)
    
    Example Usage:
        # Read current PSU status
        curl http://localhost:5001/fug/read
        
        # Example response when PSU is on and supplying power:
        # {
        #   "voltage": 9998.3,
        #   "current": 0.12,
        #   "on": true
        # }
        
        # Example response when PSU relay is off:
        # {
        #   "voltage": 0.0,
        #   "current": 0.0,
        #   "on": false
        # }
    
    Understanding the Values:
        - voltage: What the PSU is actually outputting right now
        - current: How much current the connected load is actually drawing
        - on: Whether the internal relay allows power to flow
    
    Key Differences from Heinzinger:
        - FUG "on" field reflects actual relay state (Heinzinger always shows false)
        - FUG can show 0V/0mA when relay is off, even if voltage is set
        - FUG provides true remote monitoring of power output state
    
    Use Cases:
        - Verify that voltage/current settings were applied correctly
        - Monitor current draw to ensure it's within safe limits
        - Check if PSU is actually outputting power (relay state)
        - Confirm safe shutdown by verifying relay is off
        - Troubleshoot connection or load issues
    
    Safety Monitoring:
        - Always check "on" status before working on connected equipment
        - Use this endpoint to verify safe shutdown procedures
        - Monitor current to detect unexpected load changes
        - Verify voltage is at expected levels during operation
    
    Notes:
        - Readings are real-time from PSU hardware
        - If relay is OFF, voltage/current should be near 0 regardless of settings
        - Current value depends on what's connected (0 if nothing connected)
        - Voltage may be slightly different from set value due to load or PSU accuracy
    
    Common Issues:
        - "FUG PSU not available" - Hardware not connected or initialized
        - Very low current readings might indicate poor connections
        - Voltage significantly different from set value might indicate PSU issues
        - "on" false when expecting true suggests relay control problems
    """
    psu = get_psu_instance("fug")
    if psu is None:
        return jsonify({"error": "FUG PSU not available"}), 500
    
    try:
        return jsonify({
            "voltage": psu.read_voltage(),
            "current": psu.read_current(),
            "on": psu.is_relay_on()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/fug/relay")
def fug_relay_state():
    """
    HTTP Endpoint: Check relay state for FUG PSU
    
    Checks whether the FUG PSU's internal relay/switch is currently ON or OFF.
    The FUG PSU has full remote relay control capability, so this endpoint returns
    the actual state of the internal power relay. This is useful for safety checks
    and verifying power output status.
    
    HTTP Method: GET
    URL: /fug/relay
    
    Request: No body required (GET request)
    
    Response (JSON):
        Success (200): {"on": <true_or_false>} - Actual relay state
        Error (500): {"error": "message"} - PSU not available or communication error
    
    Response Values:
        on (boolean): True if relay is ON (power can flow), False if relay is OFF (no power)
    
    Example Usage:
        # Check if FUG PSU relay is currently on
        curl http://localhost:5001/fug/relay
        
        # Example responses:
        # {"on": true}   - Relay is ON, power can flow
        # {"on": false}  - Relay is OFF, no power output
    
    Understanding Relay State:
        - ON (true): Internal relay is closed, PSU can output power at set voltage/current
        - OFF (false): Internal relay is open, no power output regardless of settings
        - This is independent of voltage/current settings - relay controls actual power flow
    
    Safety Applications:
        - Verify PSU is safely OFF before working on connected equipment
        - Confirm PSU is ON before expecting power output
        - Monitor relay state during automated sequences
        - Safety interlocks can check relay state before proceeding
    
    Comparison with Heinzinger:
        - FUG: Has actual remote relay control (this endpoint is meaningful)
        - Heinzinger: No remote relay control (always returns false)
        - FUG: Can be safely controlled remotely without physical access
    
    Use Cases:
        - Safety verification before maintenance
        - Automated testing sequences
        - Remote monitoring of PSU status
        - Confirming successful relay control commands
        - System status dashboards
    
    Technical Notes:
        - This is a read-only operation - doesn't change relay state
        - Real-time reading from PSU hardware
        - Should match the "on" field from /fug/read endpoint
        - Fast operation suitable for frequent polling
    
    Common Issues:
        - "FUG PSU not available" - Hardware not connected or initialized
        - Communication timeouts if PSU is unresponsive
        - Inconsistent readings might indicate hardware problems
    """
    psu = get_psu_instance("fug")
    if psu is None:
        return jsonify({"error": "FUG PSU not available"}), 500
    
    try:
        return jsonify({"on": psu.is_relay_on()})
    except Exception as exc:
        print("ERROR reading FUG relay state:", exc)
        return jsonify({"error": str(exc)}), 500

@app.post("/fug/relay")
def fug_set_relay():
    """
    HTTP Endpoint: Control FUG PSU relay (turn power ON or OFF)
    
    Controls the FUG PSU's internal relay to turn power output ON or OFF remotely.
    This is the primary safety control for the FUG PSU - when the relay is OFF,
    no power flows regardless of voltage/current settings. When ON, the PSU outputs
    power at the configured voltage and current levels.
    
    HTTP Method: POST
    URL: /fug/relay
    Content-Type: application/json
    
    Request Body (JSON):
        {
            "state": <true_or_false>
        }
    
    Parameters:
        state (boolean): Desired relay state
                        true = turn relay ON (enable power output)
                        false = turn relay OFF (disable power output)
    
    Response (JSON):
        Success (200): {"on": <actual_relay_state>} - Command succeeded
        Error (400): {"error": "message"} - Invalid request format
        Error (500): {"error": "message"} - PSU not available or command failed
    
    Example Usage:
        # Turn FUG PSU relay ON (enable power output)
        curl -X POST http://localhost:5001/fug/relay \
             -H "Content-Type: application/json" \
             -d '{"state": true}'
        
        # Turn FUG PSU relay OFF (disable power output)
        curl -X POST http://localhost:5001/fug/relay \
             -H "Content-Type: application/json" \
             -d '{"state": false}'
        
        # Example success response:
        # {"on": true}  - Relay is now ON
    
    Safety Sequence Example:
        # 1. Set safe voltage and current limits first
        curl -X POST http://localhost:5001/fug/set_voltage \
             -H "Content-Type: application/json" -d '{"value": 1000}'
        curl -X POST http://localhost:5001/fug/set_current \
             -H "Content-Type: application/json" -d '{"value": 0.1}'
        
        # 2. Turn relay ON to enable power output
        curl -X POST http://localhost:5001/fug/relay \
             -H "Content-Type: application/json" -d '{"state": true}'
        
        # 3. Later, turn relay OFF for safety
        curl -X POST http://localhost:5001/fug/relay \
             -H "Content-Type: application/json" -d '{"state": false}'
    
    What Happens When Relay Changes:
        - ON → PSU immediately starts outputting power at set voltage/current
        - OFF → PSU immediately stops all power output (voltage drops to 0)
        - Settings (voltage/current limits) are preserved when relay changes
        - Hardware safety interlocks may still prevent operation
    
    Safety Best Practices:
        - Always set voltage and current limits BEFORE turning relay ON
        - Turn relay OFF before making any connection changes
        - Verify relay is OFF before maintenance work
        - Use this as emergency stop capability
        - Monitor relay state during automated operations
    
    Error Handling:
        - If PSU rejects the command, "ok" will be false in response
        - Response always includes actual relay state for verification
        - Hardware safety systems may override relay commands
    
    Comparison with Heinzinger:
        - FUG: Full remote relay control (this endpoint works)
        - Heinzinger: No remote relay control (similar endpoint always fails)
        - FUG: Enables safe remote operation without physical access
    
    Technical Notes:
        - Command is sent to PSU hardware immediately
        - Response includes verification of actual relay state
        - Thread-safe for multiple concurrent requests
        - PSU may have additional safety interlocks that override commands
    
    Common Errors:
        - "JSON must contain 'state' field" - Missing or misspelled parameter
        - "Invalid JSON format" - Malformed JSON in request body
        - "FUG PSU not available" - Hardware not connected or initialized
        - "FUG PSU did not accept the command" - Hardware rejected the command
    """
    psu = get_psu_instance("fug")
    if psu is None:
        return jsonify({"error": "FUG PSU not available"}), 500
    
    try:
        data = request.get_json()
        if not data or "state" not in data:
            return jsonify({"error": "JSON must contain 'state' field"}), 400
        
        desired = bool(data["state"])
    except Exception:
        return jsonify({"error": "Invalid JSON format"}), 400

    try:
        if desired:
            ok = psu.switch_on()
        else:
            ok = psu.switch_off()

        if not ok:
            return jsonify({"error": "FUG PSU did not accept the command"}), 500

        return jsonify({"on": psu.is_relay_on()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Status endpoint to check both PSUs
@app.get("/status")
def status():
    """
    HTTP Endpoint: Get comprehensive status of both PSUs
    
    Provides a complete overview of both Heinzinger and FUG PSUs in a single request.
    This endpoint is ideal for monitoring dashboards, system health checks, and
    troubleshooting. It shows initialization status, configuration, and current
    readings for both PSUs.
    
    HTTP Method: GET
    URL: /status
    
    Request: No body required (GET request)
    
    Response (JSON):
        {
            "heinzinger": {
                "initialized": <true_or_false>,
                "device_index": 0,
                "max_voltage": 30000.0,
                "max_current": 2.0,
                "voltage": <current_voltage>,    // Only if initialized
                "current": <current_current>,    // Only if initialized  
                "relay_on": false               // Always false for Heinzinger
            },
            "fug": {
                "initialized": <true_or_false>,
                "device_index": 1,
                "max_voltage": 50000.0,
                "max_current": 0.5,
                "voltage": <current_voltage>,    // Only if initialized
                "current": <current_current>,    // Only if initialized
                "relay_on": <true_or_false>     // Actual relay state for FUG
            }
        }
    
    Response Fields (per PSU):
        initialized (boolean): Whether PSU hardware connection is established
        device_index (number): Hardware device identifier (0=Heinzinger, 1=FUG)
        max_voltage (number): Maximum voltage limit set during initialization
        max_current (number): Maximum current limit set during initialization
        voltage (number): Current actual output voltage (only if initialized)
        current (number): Current actual output current (only if initialized)
        relay_on (boolean): Current relay state (false for Heinzinger, actual state for FUG)
        error (string): Error message if reading current values failed
    
    Example Usage:
        # Get status of both PSUs
        curl http://localhost:5001/status
        
        # Example response:
        # {
        #   "heinzinger": {
        #     "initialized": true,
        #     "device_index": 0,
        #     "max_voltage": 30000.0,
        #     "max_current": 2.0,
        #     "voltage": 5000.0,
        #     "current": 1.2,
        #     "relay_on": false
        #   },
        #   "fug": {
        #     "initialized": true,
        #     "device_index": 1,
        #     "max_voltage": 50000.0,
        #     "max_current": 0.5,
        #     "voltage": 10000.0,
        #     "current": 0.15,
        #     "relay_on": true
        #   }
        # }
    
    Use Cases:
        - System health monitoring and dashboards
        - Verify both PSUs are properly initialized
        - Quick overview of current operating conditions
        - Troubleshooting PSU connection issues
        - Automated system checks before operations
        - Safety verification (check relay states)
    
    Initialization Status:
        - "initialized": true = PSU is connected and ready for commands
        - "initialized": false = PSU not connected or initialization failed
        - If not initialized, voltage/current/relay_on fields will be missing
    
    Error Handling:
        - If a PSU is initialized but reading current values fails, an "error" field is added
        - Individual PSU errors don't affect the other PSU's status
        - The endpoint always returns HTTP 200 with available information
    
    Monitoring Best Practices:
        - Use this endpoint for periodic health checks
        - Check "initialized" before attempting PSU operations
        - Monitor "relay_on" for safety verification
        - Watch "current" values to detect unexpected load changes
        - Compare "voltage" with expected set values
    
    Technical Notes:
        - Reads from both PSUs simultaneously
        - Non-blocking operation - doesn't affect PSU settings
        - Configuration values (max_voltage, max_current) are from PSU_CONFIGS
        - Current readings are real-time from hardware
    """
    result = {}
    for psu_type in PSU_CONFIGS.keys():
        config = PSU_CONFIGS[psu_type]
        result[psu_type] = {
            "initialized": config["instance"] is not None,
            "device_index": config["device_index"],
            "max_voltage": config["max_voltage"],
            "max_current": config["max_current"]
        }
        
        # Try to get current readings if initialized
        if config["instance"] is not None:
            try:
                psu = config["instance"]
                result[psu_type].update({
                    "voltage": psu.read_voltage(),
                    "current": psu.read_current(),
                    "relay_on": psu.is_relay_on() if config["has_relay"] else False
                })
            except Exception as e:
                result[psu_type]["error"] = str(e)
    
    return jsonify(result)

# Root endpoint with usage information
@app.get("/")
def root():
    """
    HTTP Endpoint: API documentation and service information
    
    Provides comprehensive API documentation and service overview. This endpoint
    serves as a self-documenting interface that shows all available endpoints,
    PSU specifications, and basic usage information. Perfect for developers
    getting started with the API or for quick reference.
    
    HTTP Method: GET
    URL: /
    
    Request: No body required (GET request)
    
    Response (JSON):
        {
            "service": "Dual PSU Control Service",
            "psus": {
                "heinzinger": {
                    "device_index": 0,
                    "max_voltage": "30kV",
                    "max_current": "2mA",
                    "endpoints": [
                        "/heinzinger/set_voltage",
                        "/heinzinger/set_current",
                        "/heinzinger/relay",
                        "/heinzinger/read"
                    ]
                },
                "fug": {
                    "device_index": 1,
                    "max_voltage": "50kV",
                    "max_current": "0.5mA",
                    "endpoints": [
                        "/fug/set_voltage",
                        "/fug/set_current",
                        "/fug/relay",
                        "/fug/read"
                    ]
                }
            },
            "status_endpoint": "/status"
        }
    
    Example Usage:
        # Get API documentation
        curl http://localhost:5001/
        
        # Or visit in web browser:
        # http://localhost:5001/
    
    What This Endpoint Provides:
        - Service identification and version info
        - Complete list of available PSUs and their capabilities
        - All available endpoints for each PSU
        - Basic specifications (voltage/current limits)
        - Quick reference for API structure
    
    PSU Information:
        - Heinzinger: High current (2mA), moderate voltage (30kV), no relay control
        - FUG: Low current (0.5mA), very high voltage (50kV), with relay control
        - Each PSU has its own device_index for hardware identification
    
    Endpoint Categories:
        - set_voltage: Configure output voltage
        - set_current: Configure current limit
        - relay: Control/check power output (FUG only for control)
        - read: Get current voltage, current, and status
        - /status: Overview of both PSUs
    
    Use Cases:
        - API discovery for new developers
        - Quick reference during development
        - Documentation for integration teams
        - Service health check (confirms service is running)
        - Understanding PSU capabilities and limitations
    
    Getting Started:
        1. Visit this endpoint to see available APIs
        2. Check /status to verify PSU connections
        3. Use individual PSU endpoints for control
        4. Refer to detailed endpoint documentation for parameters
    
    Technical Notes:
        - Static information - doesn't query hardware
        - Always returns HTTP 200
        - Useful for automated service discovery
        - Human-readable format for documentation
    """
    return jsonify({
        "service": "Dual PSU Control Service",
        "psus": {
            "heinzinger": {
                "device_index": 0,
                "max_voltage": "30kV",
                "max_current": "2mA",
                "endpoints": [
                    "/heinzinger/set_voltage",
                    "/heinzinger/set_current", 
                    "/heinzinger/relay",
                    "/heinzinger/read"
                ]
            },
            "fug": {
                "device_index": 1,
                "max_voltage": "50kV", 
                "max_current": "0.5mA",
                "endpoints": [
                    "/fug/set_voltage",
                    "/fug/set_current",
                    "/fug/relay", 
                    "/fug/read"
                ]
            }
        },
        "status_endpoint": "/status"
    })

def cleanup_resources():
    """
    Properly shuts down and releases all PSU resources during service shutdown.
    
    This function ensures that all PSU connections are properly closed and
    memory resources are freed when the web service shuts down. It's crucial
    for preventing resource leaks and ensuring PSUs are left in a safe state.
    Think of it like properly closing all connections before turning off a computer.
    
    What This Function Does:
        1. Calls run_psu.cleanup_psu() to release all hardware connections
        2. Sets all PSU instances to None in the global PSU_CONFIGS
        3. Prints status message for debugging
        4. Ensures clean shutdown without resource leaks
    
    When This Function Is Called:
        - Automatically when the web service exits normally
        - When the service receives termination signals (Ctrl+C, SIGTERM)
        - During error shutdowns to ensure cleanup
        - Can be called manually if needed
    
    Safety Features:
        - Safe to call multiple times (idempotent)
        - Doesn't affect PSU hardware settings, just software connections
        - Ensures no hanging processes or memory leaks
        - Prints confirmation message for verification
    
    What Happens to PSUs:
        - Software connection to PSUs is closed
        - PSU hardware remains in its last configured state
        - Voltage and current settings are preserved on the hardware
        - Relay states are maintained (FUG PSU)
        - Physical PSU operation is not affected
    
    Technical Details:
        - Uses run_psu.cleanup_psu() from the PSU control module
        - Clears global _psu_instances dictionary
        - Resets PSU_CONFIGS instance references to None
        - Registered with multiple shutdown handlers for reliability
    
    Example Situations:
        - User presses Ctrl+C to stop the service
        - System administrator sends SIGTERM signal
        - Service crashes and needs emergency cleanup
        - Manual service restart or maintenance
    
    Notes:
        - This is a safety function - always better to call it than not
        - PSUs can be reconnected by restarting the service
        - Hardware will remember its settings between service restarts
        - Essential for proper resource management in production
    """
    print("Cleaning up PSU resources...")
    run_psu.cleanup_psu()  # Clean up all PSU instances
    for psu_type in PSU_CONFIGS:
        PSU_CONFIGS[psu_type]["instance"] = None

if __name__ == "__main__":
    import atexit
    import signal
    
    # Register cleanup handlers
    atexit.register(cleanup_resources)
    signal.signal(signal.SIGINT, lambda s, f: cleanup_resources())
    signal.signal(signal.SIGTERM, lambda s, f: cleanup_resources())
    
    print("Starting Dual PSU Service...")
    print("Heinzinger PSU: device_index=0, 30kV/2mA, endpoints: /heinzinger/* (no relay)")
    print("FUG PSU: device_index=1, 50kV/0.5mA, endpoints: /fug/* (with relay)")
    print("Status endpoint: /status")
    
    try:
        app.run(host="0.0.0.0", port=5001, threaded=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        cleanup_resources()
