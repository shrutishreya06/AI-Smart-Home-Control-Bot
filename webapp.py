from flask import Flask, jsonify, render_template, request
from devices import get_devices, set_device

app = Flask(__name__)

# Nova listening state
_nova_status = {"listening": False}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/status")
def status():
    return jsonify(get_devices())


@app.route("/update", methods=["POST"])
def update():
    data = request.get_json(silent=True) or {}
    device = (data.get("device") or "").strip().lower()
    state = data.get("state")

    if device not in get_devices():
        return jsonify({"ok": False, "error": "invalid device"}), 400

    set_device(device, state)
    return jsonify({"ok": True, "device": device, "state": bool(state)})


@app.route("/nova-status")
def nova_status():
    return jsonify(_nova_status)


@app.route("/nova-listening", methods=["POST"])
def set_nova_listening():
    data = request.get_json(silent=True) or {}
    _nova_status["listening"] = bool(data.get("listening", False))
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True)
