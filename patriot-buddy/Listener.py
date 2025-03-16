import threading
import speech_recognition as sr
from PySide6.QtCore import Signal, QObject

class Listener(QObject):
    text_received = Signal(str, str)

    def __init__(self):
        super(Listener, self).__init__()
        self.is_listening = False
        self.record = sr.Recognizer()

    def toggle_listening(self):
        if not self.is_listening:
            self.start_listening()
            return "Listening"
        else:
            self.stop_listening()
            return "NotListening"

    def start_listening(self):
        self.is_listening = True

        def listen():
            with sr.Microphone() as source:
                self.record.adjust_for_ambient_noise(source)
                try:
                    audio = self.record.listen(source, timeout=5)
                    try:
                        text = self.record.recognize_google(audio)
                        self.text_received.emit(text, "user_input")
                    except sr.UnknownValueError:
                        self.text_received.emit("I couldn't understand that. Please try again.", "error")
                    except sr.RequestError as e:
                        self.text_received.emit(f"Speech recognition request error: {e}", "error")
                except sr.WaitTimeoutError:
                    self.text_received.emit("No speech detected", "error")            

        threading.Thread(target=listen, daemon=True).start()



    def stop_listening(self):
        self.is_listening = False              
