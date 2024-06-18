from threading import Thread
from queue import Queue
import speech_recognition as sr
import logging

logger = logging.getLogger()

class AudioDetect(Thread):
    def __init__(self, audio_in_queue:Queue[sr.AudioData], mic_obj:sr.Microphone) -> None:
        Thread.__init__(self)
        self.setDaemon(True)
        self.audio_in_queue = audio_in_queue
        self.name = "AudioDetect"
        self.mic_obj = mic_obj
        self.stop_req = False

    def shutdown(self) -> None:
        self.stop_req = True

    def run(self) -> None:
        recog = sr.Recognizer()
        with self.mic_obj as source:
            logger.info("===Start===")
            while not self.stop_req:
                try:
                    logger.info("Audio Listening")
                    audio = recog.listen(source, timeout=1)
                    logger.info("Audio Detected")
                    self.audio_in_queue.put(audio)
                except sr.exceptions.UnknownValueError:
                    pass
                except sr.WaitTimeoutError:
                    pass
        logger.warning("===Stop===")