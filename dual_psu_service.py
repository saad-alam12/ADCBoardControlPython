#!/usr/bin/env python3
"""
Dual PSU Service - Control two PSUs simultaneously
- Heinzinger: 30kV/2mA on device_index=0, endpoints: /heinzinger/*
- FUG: 50kV/0.5mA on device_index=1, endpoints: /fug/*
"""

from flask import Flask, request, jsonify
import run_psu_multi as run_psu

app = Flask(__name__)

# PSU configurations
PSU_CONFIGS = {
    "heinzinger": {
        "device_index": 0,
        "max_voltage": 30000.0,  # 30kV
        "max_current": 2.0,      # 2mA
        "max_input_voltage": 10.0,
        "instance": None,
        "has_relay": False  # Heinzinger has no relay - must be turned on manually
    },
    "fug": {
        "device_index": 1,
        "max_voltage": 50000.0,  # 50kV
        "max_current": 0.5,      # 0.5mA
        "max_input_voltage": 10.0,
        "instance": None,
        "has_relay": True   # FUG has relay control
    }
}

def get_psu_instance(psu_type):
    """Get or create PSU instance for the specified type"""
    if psu_type not in PSU_CONFIGS:
        return None
    
    config = PSU_CONFIGS[psu_type]
    if config["instance"] is None:
        try:
            # Use the multi-PSU interface to get/create the instance
            instance = run_psu.get_psu_instance(
                device_index=config["device_index"],
                max_v=config["max_voltage"],
                max_c=config["max_current"],
                verb=False,  # Set to True for debugging
                max_in_v=config["max_input_voltage"]
            )
            
            if instance is not None:
                print(f"{psu_type.upper()} PSU initialized successfully on device {config['device_index']}")
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
    psu = get_psu_instance("heinzinger")
    if psu is None:
        return jsonify({"error": "Heinzinger PSU not available"}), 500
    
    # Heinzinger has no relay - always return false
    return jsonify({"on": False})

@app.post("/heinzinger/relay")
def heinzinger_set_relay():
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
    """Get status of both PSUs"""
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
    """Clean up PSU resources on shutdown"""
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
