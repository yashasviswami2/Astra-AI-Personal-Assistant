import pyttsx3
import threading
from config import settings
from utils.logger import get_logger

logger = get_logger()

class TTSManager:
    def __init__(self):
        self.lock = threading.Lock()
        
    def speak(self, text, block=False):
        """
        Convert text to speech.
        :param text: The text string to speak.
        :param block: If True, blocks execution until speaking is complete.
        """
        def _speak():
            with self.lock:
                try:
                    # Initialize engine inside the thread to avoid SAPI5 COM threading issues
                    engine = pyttsx3.init()
                    engine.setProperty('rate', settings.TTS_RATE)
                    engine.setProperty('volume', settings.TTS_VOLUME)
                    
                    voices = engine.getProperty('voices')
                    gender_target = settings.TTS_VOICE_GENDER.lower()
                    
                    # Try to find a matching voice
                    matched = False
                    for voice in voices:
                        if gender_target in voice.name.lower():
                            engine.setProperty('voice', voice.id)
                            matched = True
                            break
                    
                    # Fallback to default if no gender match
                    if not matched and voices:
                        engine.setProperty('voice', voices[0].id)
                        
                    logger.info(f"TTS speaking: '{text}'")
                    engine.say(text)
                    engine.runAndWait()
                except Exception as e:
                    logger.error(f"TTS engine error: {e}")
        
        t = threading.Thread(target=_speak, daemon=True)
        t.start()
        if block:
            t.join()
        return t

# Singleton instance
tts_manager = TTSManager()
