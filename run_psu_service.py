#!/usr/bin/env python3 
from flask import Flask, request, jsonify
import run_psu                    #(imports heinzinger as well)

psu = run_psu.get_psu_instance(device_index=0, verb=0)
app = Flask(__name__)

@app.post("/set_voltage")
def set_voltage():
    v = float(request.json["value"])
    ok = psu.set_voltage(v)
    return jsonify({"ok": ok})

@app.post("/set_current")
def set_current():
    i = float(request.json["value"])
    ok = psu.set_current(i)
    return jsonify({"ok": ok})

@app.get("/read")
def read():
    return jsonify({
        "voltage": psu.read_voltage(),
        "current": psu.read_current(),
        "on": False 
    })

@app.get("/relay")
def relay_state():
    """Return JSON: {"on": true|false} depending on PSU output state."""
    try:
        return jsonify({"on": psu.is_relay_on()})
    except Exception as exc:
        print("ERROR reading relay state:", exc)
        return jsonify({"error": str(exc)}), 500


@app.post("/relay")
def set_relay():
    """
    Toggle the output relay.

    Body JSON: {"state": true|false}
    Returns   : {"on": true|false}
    """
    try:
        data = request.get_json(force=True)
        desired = bool(data["state"])
    except Exception:
        return jsonify({"error": "JSON must contain boolean field 'state'"}), 400

    # ---- call the C++ layer via our psu instance ----
    if desired:
        ok = psu.switch_on()
    else:
        ok = psu.switch_off()

    if not ok:
        return jsonify({"error": "PSU did not accept the command"}), 500

    return jsonify({"on": psu.is_relay_on()})   # echo current state



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
