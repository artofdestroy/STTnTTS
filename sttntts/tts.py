from openai import OpenAI
from google.cloud import texttospeech
from queue import Queue, Empty
from threading import Thread
import time
import logging

logger = logging.getLogger()

class OpenAiTTS(Thread):
    def __init__(self, tts_in_queue:Queue[str], wav_file_queue:Queue[str], api_key:str)->None:
        Thread.__init__(self)
        self.setDaemon(True)
        self.name = "OpenAiTTS"
        self.stop_req = False
        self.tts_in_queue = tts_in_queue
        self.wav_file_queue = wav_file_queue
        self.client = OpenAI(api_key = api_key)

    def shutdown(self)->None:
        self.stop_req = True

    def tts(self, text:str, filename:str)->None:
        response = self.client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text,
            response_format="wav"
        )

        response.write_to_file(filename)

    def run(self)->None:
        logger.info("===Start===")
        while not self.stop_req:
            try:
                text = self.tts_in_queue.get(block=True, timeout=0.5)
                filename = f"{time.time()}.wav"
                self.tts(text, filename)
                self.wav_file_queue.put(filename)
            except Empty:
                pass
        logger.warning("===Stop===")

class GoogleTTS(Thread):
    def __init__(self, tts_in_queue:Queue[str], wav_file_queue:Queue[str], api_key:str)->None:
        Thread.__init__(self)
        self.setDaemon(True)
        self.name = "GoogleTTS"
        self.stop_req = False
        self.tts_in_queue = tts_in_queue
        self.wav_file_queue = wav_file_queue
        self.client = texttospeech.TextToSpeechClient.from_service_account_json(api_key)

    def shutdown(self)->None:
        self.stop_req = True

    def tts(self, text:str, filename:str)->None:
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="th-TH",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
            name="th-TH-Standard-A"
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16
        )

        response = self.client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        with open(filename, "wb") as out:
            # Write the response to the output file.
            out.write(response.audio_content)

    def run(self)->None:
        logger.info("===Start===")
        while not self.stop_req:
            try:
                text = self.tts_in_queue.get(block=True, timeout=0.5)
                filename = f"{time.time()}.wav"
                self.tts(text, filename)
                self.wav_file_queue.put(filename)
            except Empty:
                pass
        logger.warning("===Stop===")
