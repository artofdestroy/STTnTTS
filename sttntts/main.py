import speech_recognition as sr
from queue import Queue, Empty
from sttntts import audio_detect_thr
from sttntts import stt_thr
from sttntts import tts
from sttntts import audio_player
from sttntts import twitch_sender
import logging
import asyncio

logging.basicConfig(format='%(asctime)s [%(threadName)s][%(levelname)s] %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def find_mic(mic_name:str)->sr.Microphone|None:
    mic_list = sr.Microphone.list_microphone_names()
    for mic_num in range(len(mic_list)):
        tmp_name = str(mic_list[mic_num])
        if mic_name in tmp_name:
            return sr.Microphone(mic_num)
    return None

def start_app(mic_name:str, speaker_name:str, credentials_json:str, twitch_json:str)->None:
    # Find the microphone
    mic = find_mic(mic_name)
    if mic is None:
        logger.error(f"Cannot find mic with name {mic_name}")
        return
    else:
        logger.info(f"Found mic with name {mic_name}")

    # Create data queue
    audio_in_queue: Queue[sr.AudioData] = Queue()
    text_out_queue: Queue[str] = Queue()
    tts_in_queue: Queue[str] = Queue()
    wav_file_queue: Queue[str] = Queue()

    # Start all worker thread
    logger.info("===Start===")
    audio_detect = audio_detect_thr.AudioDetect(audio_in_queue, mic)
    stt = stt_thr.STT(audio_in_queue=audio_in_queue, text_out_queue=text_out_queue, credentials_json=credentials_json)
    cloud_tts = tts.GoogleTTS(tts_in_queue, wav_file_queue, api_key=credentials_json)
    wav_player = audio_player.WavPlayer(wav_file_queue, speaker_name)
    twitch_tsk = twitch_sender.TwitchSender(twitch_json, "artofdestroy")

    cloud_tts.start()
    wav_player.start()
    audio_detect.start()
    stt.start()
    twitch_tsk.start()

    while True:
        try:
            stt_rslt = text_out_queue.get(block=True, timeout=0.5)
            logger.info(f"STT Result: {stt_rslt}")

            if "ปิดโปรแกรม" in stt_rslt:
                break
            twitch_tsk.send_msg(stt_rslt)
            tts_in_queue.put(stt_rslt)
        except Empty:
            pass
        except KeyboardInterrupt:
            break

    logger.warning("===Teardown===")

    cloud_tts.shutdown()
    wav_player.shutdown()
    audio_detect.shutdown()
    stt.shutdown()
    twitch_tsk.shutdown()
    cloud_tts.join()
    wav_player.join()
    audio_detect.join()
    stt.join()
    twitch_tsk.join()
    
    logger.warning("===End===")

def main():
    mic_name = "VoiceMeeter VAIO3 Output"
    speaker_name = "CABLE Input"
    credentials_json = "credential/google_cloud_credential.json"
    twitch_json = "credential/twitch_key.json"
    start_app(mic_name, speaker_name, credentials_json, twitch_json)

if __name__ == "__main__":
    main()