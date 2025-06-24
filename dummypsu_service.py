#!/usr/bin/env python3
"""
dummy_psu_service.py
A stand-alone Flask server that pretends to be the Heinzinger PSU.
It keeps three in-memory variables and exposes four REST endpoints.

    POST /set_voltage   { "value": <float> }   → {"ok": true}
    POST /set_current   { "value": <float> }   → {"ok": true}
    POST /relay         { "state": true|false }→ {"ok": true}
    GET  /read                                → {"voltage":…, "current":…, "on":…}
"""
from flask import Flask, request, jsonify

app = Flask(__name__)

# --------------------------------------------------------------------
#  Fake internal “hardware registers”
# --------------------------------------------------------------------
_state = {
    "voltage": 0.0,    # volts
    "current": 0.0,    # amperes
    "on":      False   # output enabled?
}

# ---------- Helper ---------------------------------------------------
def clamp(x, lo, hi):        # stop the “supply” at 0…30 kV and 0…2 A
    return max(lo, min(hi, x))

# ---------- End-points ----------------------------------------------
@app.post("/set_voltage")
def set_voltage():
    _state["voltage"] = clamp(float(request.json["value"]), 0, 30_000)
    return jsonify(ok=True)

@app.post("/set_current")
def set_current():
    _state["current"] = clamp(float(request.json["value"]), 0, 2)
    return jsonify(ok=True)

@app.post("/relay")
def relay():
    _state["on"] = bool(request.json["state"])
    return jsonify(ok=True)

@app.get("/read")
def read():
    return jsonify(_state)

# --------------------------------------------------------------------
if __name__ == "__main__":
    # 0.0.0.0 ⇒ listen on ALL local interfaces (good for later LAN tests)
    app.run(host="0.0.0.0", port=5001, threaded=True)