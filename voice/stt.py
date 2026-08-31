import speech_recognition as sr
from config import settings
from utils.logger import get_logger

logger = get_logger()

class STTManager:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = settings.STT_ENERGY_THRESHOLD
        self.recognizer.dynamic_energy_threshold = settings.STT_DYNAMIC_ENERGY_THRESHOLD
        self.recognizer.pause_threshold = settings.STT_PAUSE_THRESHOLD
        self.recognizer.non_speaking_duration = settings.STT_NON_SPEAKING_DURATION

    def _open_microphone(self):
        device_index = settings.MICROPHONE_INDEX
        microphone_names = []

        try:
            microphone_names = sr.Microphone.list_microphone_names()
            logger.info(f"STT: {len(microphone_names)} microphone(s) detected:")
            for idx, name in enumerate(microphone_names):
                logger.info(f"  [{idx}] {name}")
        except Exception as e:
            logger.warning(f"STT: Could not list microphones: {e}")

        if device_index is not None:
            if microphone_names and 0 <= device_index < len(microphone_names):
                logger.info(
                    f"STT: Using configured microphone index {device_index}: {microphone_names[device_index]}"
                )
            else:
                logger.warning(
                    f"STT: Configured microphone index {device_index} is invalid or unavailable. "
                    "Falling back to default microphone."
                )
                device_index = None
        else:
            logger.info("STT: Using default microphone.")

        try:
            return sr.Microphone(device_index=device_index)
        except OSError as e:
            logger.error(f"STT: Cannot open microphone (device_index={device_index}): {e}")
            raise

    def listen(self, timeout=settings.STT_TIMEOUT, phrase_time_limit=settings.STT_PHRASE_LIMIT):
        """
        Listen to the microphone and return transcribed text using Google Speech Recognition.
        Blocks while listening, so this must be called from a worker thread.

        Returns:
            str: Transcribed text, "" if not understood, or None if timed out / failed.
        """
        try:
            with self._open_microphone() as source:
                logger.info("STT: Calibrating for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(
                    source, duration=settings.STT_AMBIENT_NOISE_DURATION
                )
                logger.info("STT: Listening...")

                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )

                logger.info("STT: Voice detected. Recognizing speech...")
                text = self.recognizer.recognize_google(
                    audio, language=settings.STT_LANGUAGE
                )
                logger.info(f"STT Recognized text: '{text}'")
                return text

        except sr.WaitTimeoutError:
            logger.info("STT: Listening timed out waiting for speech.")
            return None
        except sr.UnknownValueError:
            logger.info("STT: Could not understand audio.")
            return ""
        except sr.RequestError as e:
            logger.error(f"STT: Speech recognition request failed: {e}")
            return None
        except OSError as e:
            logger.error(f"STT: Microphone unavailable or error opening device: {e}")
            return None
        except Exception as e:
            logger.error(f"STT: Unexpected speech recognition failure: {e}", exc_info=True)
            return None

# Singleton instance
stt_manager = STTManager()
