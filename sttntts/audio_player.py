import logging
import pyaudio
import wave
import os
from queue import Queue, Empty
from threading import Thread

logger = logging.getLogger()

class WavPlayer(Thread):
    def __init__(self, wav_file_queue:Queue[str], dev_name)->None:
        Thread.__init__(self)
        self.setDaemon(True)
        self.name = "WavPlayer"
        self.wav_file_queue = wav_file_queue
        self.stop_req = False
        self.dev_idx = self.__find_device(dev_name)
        if self.dev_idx is None:
            raise ValueError(f"Cannot find device with name {dev_name}")

    def __find_device(self, dev_name:str)->int|None:
        dev_idx = None

        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')

        for i in range(num_devices):
            device_info = p.get_device_info_by_host_api_device_index(0, i)
            if device_info.get('maxOutputChannels') > 0:
                if dev_name in device_info.get('name'):
                    dev_idx = i
                    break

        p.terminate()
        return dev_idx

    def shutdown(self)->None:
        self.stop_req = True

    def run(self)->None:
        logger.info("===Start===")
        while not self.stop_req:
            try:
                wav_file = self.wav_file_queue.get(block=True, timeout=0.5)
                WavPlayer.play_wav_file(wav_file, device_index=self.dev_idx)
                os.remove(wav_file)
            except Empty:
                pass
        logger.warning("===Stop===")
    
    @staticmethod
    def play_wav_file(filename, device_index=None):
        # Open the file
        wav_file = wave.open(filename, 'rb')

        # Create a PyAudio instance
        p = pyaudio.PyAudio()

        # Open a stream
        stream = p.open(format=p.get_format_from_width(wav_file.getsampwidth()),
                        channels=wav_file.getnchannels(),
                        rate=wav_file.getframerate(),
                        output=True,
                        output_device_index=device_index)

        # Read data from the WAV file
        data = wav_file.readframes(1024)

        # Play the WAV file
        while data:
            stream.write(data)
            data = wav_file.readframes(1024)

        # Stop the stream
        stream.stop_stream()
        stream.close()

        # Terminate the PyAudio instance
        p.terminate()