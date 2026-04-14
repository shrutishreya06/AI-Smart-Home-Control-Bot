import threading
import subprocess
import speech_recognition as sr
import pyttsx3

_engine_lock = threading.Lock()
_recognizer = sr.Recognizer()
_mic = sr.Microphone()

try:
    _engine = pyttsx3.init("sapi5")
except Exception:
    _engine = pyttsx3.init()

_engine.setProperty("rate", 170)
_engine.setProperty("volume", 1.0)

with _mic as source:
    _recognizer.adjust_for_ambient_noise(source)

def _windows_speak(text):
    safe = text.replace("'", "''")
    ps = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$s.Volume = 100; "
        "$s.Rate = 0; "
        f"$s.Speak('{safe}')"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        capture_output=True,
        text=True
    )

def speak(text):
    print("Nova:", text)
    try:
        _windows_speak(text)
        return
    except Exception as e:
        print("Windows TTS error:", e)

    try:
        with _engine_lock:
            try:
                _engine.stop()
            except Exception:
                pass
            _engine.say(text)
            _engine.runAndWait()
    except Exception as e:
        print("pyttsx3 error:", e)

def listen():
    try:
        with _mic as source:
            print("Listening...")
            audio = _recognizer.listen(source, timeout=5, phrase_time_limit=7)

        text = _recognizer.recognize_google(audio)
        print("You said:", text)
        return text.lower()

    except sr.WaitTimeoutError:
        return ""
    except sr.UnknownValueError:
        return ""
    except Exception as e:
        print("Voice error:", e)
        return ""