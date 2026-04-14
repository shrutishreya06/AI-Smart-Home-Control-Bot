from threading import Lock

_STATE = {
    "fan": False,
    "light": False,
    "ac": False,
    "tv": False,
    "fridge": False
}

_LOCK = Lock()

def set_device(device, state):
    with _LOCK:
        if device not in _STATE:
            return False
        _STATE[device] = bool(state)
        return True

def get_devices():
    with _LOCK:
        return _STATE.copy()