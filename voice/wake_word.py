
import json
import threading
from pathlib import Path

import pyaudio
from vosk import Model, KaldiRecognizer


class WakeWordDetector:

    def __init__(self, microphone_index=1):

        self.microphone_index = microphone_index
        self.stop_event = threading.Event()

        model_path = (
            Path(__file__).resolve().parent.parent
            / "models"
            / "vosk-model-small-en-us-0.15"
        )

        self.model = Model(str(model_path))

    def stop(self):
        self.stop_event.set()

    def wait_for_wake_word(self):

        self.stop_event.clear()

        audio = pyaudio.PyAudio()
        stream = None

        try:
            device = audio.get_device_info_by_index(
                self.microphone_index
            )

            rate = int(device["defaultSampleRate"])

            recognizer = KaldiRecognizer(
                self.model,
                rate,
                '["hey astra", "hello astra", "[unk]"]'
            )

            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=rate,
                input=True,
                input_device_index=self.microphone_index,
                frames_per_buffer=4000
            )

            print("ASTRA standby: Say Hey Astra")

            while not self.stop_event.is_set():

                data = stream.read(
                    4000,
                    exception_on_overflow=False
                )

                if recognizer.AcceptWaveform(data):

                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").strip()

                    if text in {"hey astra", "hello astra"}:
                        print("Wake word detected!")
                        return True

            return False

        finally:

            if stream is not None:
                stream.stop_stream()
                stream.close()

            audio.terminate()
