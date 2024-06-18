from threading import Thread
from queue import Queue, Empty
import speech_recognition as sr
import logging

logger = logging.getLogger()

class STT(Thread):
    def __init__(self, audio_in_queue:Queue[sr.AudioData], text_out_queue:Queue[str], credentials_json:str, language:str="th") -> None:
        Thread.__init__(self)
        self.setDaemon(True)
        self.audio_in_queue = audio_in_queue
        self.text_out_queue = text_out_queue
        self.name = "SpeechToText"
        self.credentials_json = credentials_json
        self.language = language
        self.stop_req = False

    def shutdown(self) -> None:
        self.stop_req = True

    def run(self) -> None:
        logger.info("===Start===")
        recog = sr.Recognizer()
        while not self.stop_req:
            try:
                audio = self.audio_in_queue.get(block=True, timeout=0.5)
                logger.info("Processing speech to text")
                if self.credentials_json is not None:
                    rslt_text = recog.recognize_google_cloud(audio,language=self.language, credentials_json="credential/google_cloud_credential.json")
                else:
                    rslt_text = recog.recognize_google(audio, language=self.language)
                self.text_out_queue.put(rslt_text)
            except Empty:
                pass
            except sr.exceptions.UnknownValueError:
                pass
        logger.warning("===Stop===")