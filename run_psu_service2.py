#!/usr/bin/env python3
from flask import Flask, request, jsonify
import run_psu                    # this already imports heinzinger_control

psu = run_psu.get_psu_instance(device_index=1)
app = Flask(__name__)

@app.post("/set_voltage")
def set_voltage():
    
    v = float(request.json["value"])
    ok = psu.set_voltage(v)
    #Expects a JSON payload with a "value" key representing the desired voltage.
    #Returns a JSON response indicating success or failure of the operation.

@app.post("/set_current")
def set_current():
    i = float(request.json["value"])
    ok = psu.set_current(i)
    return jsonify({"ok": ok})

@app.get("/read")
def read():
    return jsonify({
        "voltage": psu.read_voltage(),
        "current": psu.read_current()
    })

@app.post("/relay")
def relay():
    state = request.json["state"]          # true/false
    ok = psu.switch_on() if state else psu.switch_off()
    return jsonify({"ok": ok})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, threaded=True)
