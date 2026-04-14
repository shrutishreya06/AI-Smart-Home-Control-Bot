import re
import threading
import requests
from voice import speak, listen

SERVER_URL = "http://127.0.0.1:5000/update"
LISTENING_URL = "http://127.0.0.1:5000/nova-listening"
BOT_NAME = "Nova"

DEVICE_ORDER = ["fan", "light", "ac", "tv", "fridge"]

DEVICE_ALIASES = {
    "fan": ["fan", "ceiling fan"],
    "light": ["light", "bulb", "lamp"],
    "ac": ["ac", "air conditioner"],
    "tv": ["tv", "television"],
    "fridge": ["fridge", "refrigerator", "ice box"]
}

PRETTY = {
    "fan": "Fan",
    "light": "Light",
    "ac": "AC",
    "tv": "TV",
    "fridge": "Fridge"
}

last_devices = []


def normalize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def join_words(items):
    items = [x for x in items if x]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def detect_state(command):
    if re.search(r"\b(turn off|switch off|power off|shut off|disable|stop|off)\b", command):
        return False
    if re.search(r"\b(turn on|switch on|power on|start|enable|on)\b", command):
        return True
    return None


def detect_devices(command):
    if re.search(r"\b(everything|all devices|all)\b", command):
        return DEVICE_ORDER[:]

    found = []
    seen = set()

    for device in DEVICE_ORDER:
        for alias in sorted(DEVICE_ALIASES[device], key=len, reverse=True):
            if re.search(rf"\b{re.escape(alias)}\b", command) and device not in seen:
                found.append(device)
                seen.add(device)
                break

    return found


def extract_duration_seconds(command):
    m = re.search(r"\bfor\s+(\d+)\s*(seconds?|secs?|sec|minutes?|mins?|min)?\b", command)
    if not m:
        return None

    value = int(m.group(1))
    unit = (m.group(2) or "seconds").lower()

    if unit.startswith("min"):
        return value * 60
    return value


def send_device(device, state):
    try:
        r = requests.post(SERVER_URL, json={"device": device, "state": state}, timeout=5)
        return r.status_code == 200
    except Exception as e:
        print("Request error:", e)
        return False


def set_listening(state: bool):
    """Tell the web dashboard whether Nova is currently listening."""
    try:
        requests.post(LISTENING_URL, json={"listening": state}, timeout=2)
    except Exception:
        pass


def announce_state(devices, state):
    names = [PRETTY[d] for d in devices]
    joined = join_words(names)
    status = "ON" if state else "OFF"

    if len(names) == 1:
        print(f"Home - {joined} has been turned {status}")
    else:
        print(f"Home - {joined} have been turned {status}")


def speak_state(devices, state):
    names = [PRETTY[d].lower() for d in devices]
    joined = join_words(names)
    speak(f"Okay, I have turned the {joined} {'on' if state else 'off'}")


def set_devices(devices, state, speak_back=True):
    if not devices:
        return False

    ok = True
    for device in devices:
        ok = send_device(device, state) and ok

    if ok:
        announce_state(devices, state)
        if speak_back:
            speak_state(devices, state)

    return ok


def auto_off(devices, seconds):
    speak(f"I will turn the {join_words([PRETTY[d].lower() for d in devices])} off after {seconds} seconds")
    threading.Event().wait(seconds)
    set_devices(devices, False, speak_back=True)


def process_command(command):
    global last_devices

    command = normalize(command)
    if not command:
        return

    if command in {"exit", "quit", "stop bot", "shutdown"}:
        speak("Goodbye")
        raise SystemExit

    if re.search(r"\bhello\b.*\bnova\b|\bnova\b.*\bhello\b|\bhello\b", command):
        speak("Hello! How can I help you?")
        return

    state = detect_state(command)
    devices = detect_devices(command)
    timer = extract_duration_seconds(command)

    if devices:
        last_devices = devices[:]
    elif last_devices and state is not None:
        devices = last_devices[:]

    if not devices or state is None:
        speak("I did not understand that command")
        print("Home - command not recognized")
        return

    ok = set_devices(devices, state, speak_back=True)

    if ok and state and timer:
        threading.Thread(target=auto_off, args=(devices, timer), daemon=True).start()


def main():
    speak("Nova is online")

    while True:
        # Signal dashboard: Nova is now listening
        set_listening(True)
        cmd = listen()
        # Signal dashboard: Nova stopped listening
        set_listening(False)

        if not cmd:
            continue
        try:
            process_command(cmd)
        except SystemExit:
            break


if __name__ == "__main__":
    main()
