import speech_recognition as sr
from queue import Queue, Empty
from sttntts import audio_detect_thr
from sttntts import stt_thr
import logging

logging.basicConfig(format='%(asctime)s [%(threadName)s][%(levelname)s] %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def find_mic(mic_name:str)->sr.Microphone|None:
    mic_list = sr.Microphone.list_microphone_names()
    for mic_num in range(len(mic_list)):
        tmp_name = str(mic_list[mic_num])
        if mic_name in tmp_name:
            return sr.Microphone(mic_num)
    return None

def start_app(mic_name:str, credentials_json:str)->None:
    mic = find_mic(mic_name)
    if mic is None:
        logger.error(f"Cannot find mic with name {mic_name}")
        return
    else:
        logger.info(f"Found mic with name {mic_name}")

    audio_in_queue: Queue[sr.AudioData] = Queue()
    text_out_queue: Queue[str] = Queue()

    logger.info("===Start===")
    audio_detect = audio_detect_thr.AudioDetect(audio_in_queue, mic)
    tts = stt_thr.STT(audio_in_queue=audio_in_queue, text_out_queue=text_out_queue, credentials_json=credentials_json)
    audio_detect.start()
    tts.start()

    while True:
        try:
            stt_rslt = text_out_queue.get(block=True, timeout=0.5)
            logger.info(f"STT Result: {stt_rslt}")

            if "ปิดโปรแกรม" in stt_rslt:
                break
        except Empty:
            pass
        except KeyboardInterrupt:
            break

    logger.warning("===Teardown===")

    audio_detect.shutdown()
    tts.shutdown()
    audio_detect.join()
    tts.join()
    
    logger.warning("===End===")

def main():
    mic_name = "VoiceMeeter VAIO3 Output"
    credentials_json = "credential/google_cloud_credential.json"
    start_app(mic_name, credentials_json)

if __name__ == "__main__":
    main()