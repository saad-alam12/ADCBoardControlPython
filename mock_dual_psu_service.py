#!/usr/bin/env python3
"""
Mock Dual PSU Service - Test the API structure without hardware
- Heinzinger: 30kV/2mA on device_index=0, endpoints: /heinzinger/*
- FUG: 50kV/0.5mA on device_index=1, endpoints: /fug/*
"""

from flask import Flask, request, jsonify

app = Flask(__name__)

# PSU configurations
PSU_CONFIGS = {
    "heinzinger": {
        "device_index": 0,
        "max_voltage": 30000.0,  # 30kV
        "max_current": 2.0,      # 2mA
        "max_input_voltage": 10.0,
        "voltage": 0.0,
        "current": 0.0,
        "relay_on": False
    },
    "fug": {
        "device_index": 1,
        "max_voltage": 50000.0,  # 50kV
        "max_current": 0.5,      # 0.5mA
        "max_input_voltage": 10.0,
        "voltage": 0.0,
        "current": 0.0,
        "relay_on": False
    }
}

# Mock PSU functions
def validate_psu_type(psu_type):
    return psu_type in PSU_CONFIGS

def validate_voltage(psu_type, voltage):
    max_v = PSU_CONFIGS[psu_type]["max_voltage"]
    return 0 <= voltage <= max_v

def validate_current(psu_type, current):
    max_c = PSU_CONFIGS[psu_type]["max_current"]
    return 0 <= current <= max_c

# Heinzinger PSU routes
@app.post("/heinzinger/set_voltage")
def heinzinger_set_voltage():
    try:
        v = float(request.json["value"])
        if not validate_voltage("heinzinger", v):
            max_v = PSU_CONFIGS["heinzinger"]["max_voltage"]
            return jsonify({"error": f"Voltage {v}V outside range [0, {max_v}V]"}), 400
        
        PSU_CONFIGS["heinzinger"]["voltage"] = v
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.post("/heinzinger/set_current")
def heinzinger_set_current():
    try:
        i = float(request.json["value"])
        if not validate_current("heinzinger", i):
            max_c = PSU_CONFIGS["heinzinger"]["max_current"]
            return jsonify({"error": f"Current {i}mA outside range [0, {max_c}mA]"}), 400
        
        PSU_CONFIGS["heinzinger"]["current"] = i
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/heinzinger/read")
def heinzinger_read():
    return jsonify({
        "voltage": PSU_CONFIGS["heinzinger"]["voltage"],
        "current": PSU_CONFIGS["heinzinger"]["current"],
        "on": PSU_CONFIGS["heinzinger"]["relay_on"]
    })

@app.get("/heinzinger/relay")
def heinzinger_relay_state():
    return jsonify({"on": PSU_CONFIGS["heinzinger"]["relay_on"]})

@app.post("/heinzinger/relay")
def heinzinger_set_relay():
    try:
        data = request.get_json(force=True)
        desired = bool(data["state"])
        PSU_CONFIGS["heinzinger"]["relay_on"] = desired
        return jsonify({"on": PSU_CONFIGS["heinzinger"]["relay_on"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# FUG PSU routes
@app.post("/fug/set_voltage")
def fug_set_voltage():
    try:
        v = float(request.json["value"])
        if not validate_voltage("fug", v):
            max_v = PSU_CONFIGS["fug"]["max_voltage"]
            return jsonify({"error": f"Voltage {v}V outside range [0, {max_v}V]"}), 400
        
        PSU_CONFIGS["fug"]["voltage"] = v
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.post("/fug/set_current")
def fug_set_current():
    try:
        i = float(request.json["value"])
        if not validate_current("fug", i):
            max_c = PSU_CONFIGS["fug"]["max_current"]
            return jsonify({"error": f"Current {i}mA outside range [0, {max_c}mA]"}), 400
        
        PSU_CONFIGS["fug"]["current"] = i
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/fug/read")
def fug_read():
    return jsonify({
        "voltage": PSU_CONFIGS["fug"]["voltage"],
        "current": PSU_CONFIGS["fug"]["current"],
        "on": PSU_CONFIGS["fug"]["relay_on"]
    })

@app.get("/fug/relay")
def fug_relay_state():
    return jsonify({"on": PSU_CONFIGS["fug"]["relay_on"]})

@app.post("/fug/relay")
def fug_set_relay():
    try:
        data = request.get_json(force=True)
        desired = bool(data["state"])
        PSU_CONFIGS["fug"]["relay_on"] = desired
        return jsonify({"on": PSU_CONFIGS["fug"]["relay_on"]})
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
            "initialized": True,  # Mock PSUs are always "initialized"
            "device_index": config["device_index"],
            "max_voltage": config["max_voltage"],
            "max_current": config["max_current"],
            "voltage": config["voltage"],
            "current": config["current"],
            "relay_on": config["relay_on"]
        }
    
    return jsonify(result)

# Root endpoint with usage information
@app.get("/")
def root():
    return jsonify({
        "service": "Mock Dual PSU Control Service",
        "note": "This is a mock service for testing API structure without hardware",
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

if __name__ == "__main__":
    print("Starting Mock Dual PSU Service...")
    print("This is a mock service for testing without hardware")
    print("Heinzinger PSU: device_index=0, 30kV/2mA, endpoints: /heinzinger/*")
    print("FUG PSU: device_index=1, 50kV/0.5mA, endpoints: /fug/*")
    print("Status endpoint: /status")
    app.run(host="0.0.0.0", port=5001, threaded=True)
