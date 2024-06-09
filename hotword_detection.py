import io
import speech_recognition as sr
import whisper
import torch
from datetime import datetime, timedelta
from queue import Queue
from tempfile import NamedTemporaryFile
import multiprocessing as mp
import ctypes
import time

HOTWORD = "jarvis"
AUDIO_FILE = "hotword_audio.wav"
RECORD_TIMEOUT = 2
PHRASE_TIMEOUT = 3

def record_audio_to_file(file_path, audio_data, sample_rate, sample_width):
    print('<<<<<<<<<<<<<<<<<<<<<ENTERED RECORD AUDIO TO FILE>>>>>>>>>>>>>>>>>>>>>')
    wav_data = io.BytesIO(audio_data.get_wav_data())
    with open(file_path, 'w+b') as f:
        f.write(wav_data.read())

def process_audio(recognizer, audio_model, data_queue, sample_rate, sample_width, hotword_detected, hotword_text):
    print('<<<<<<<<<<<<<<<<<<<<<ENTERED PROCESS AUDIO>>>>>>>>>>>>>>>>>>>>>')
    last_sample = bytes()
    phrase_time = None
    transcription = ['']

    while not hotword_detected.value:
        now = datetime.utcnow()
        if not data_queue.empty():
            phrase_complete = False
            if phrase_time and now - phrase_time > timedelta(seconds=PHRASE_TIMEOUT):
                last_sample = bytes()
                phrase_complete = True
            phrase_time = now

            while not data_queue.empty():
                data = data_queue.get()
                last_sample += data

            audio_data = sr.AudioData(last_sample, sample_rate, sample_width)
            temp_file = NamedTemporaryFile().name
            record_audio_to_file(temp_file, audio_data, sample_rate, sample_width)

            print("Transcribing audio...")
            result = audio_model.transcribe(temp_file, fp16=torch.cuda.is_available())
            text = result['text'].strip()
            print(f"Transcription result: {text}")

            if phrase_complete:
                transcription.append(text)
                if any(hot_word in text.lower() for hot_word in [HOTWORD]):
                    with hotword_text.get_lock():
                        hotword_text.value = text.encode('utf-8')
                    hotword_detected.value = True
                    print(f"Hotword detected: {text}")
                    break
                else:
                    print("Listening...")
            else:
                transcription[-1] = text
            time.sleep(0.25)

def listen_for_hotword(data_queue, hotword_detected, hotword_text):
    print('<<<<<<<<<<<<<<<<<<<<<ENTERED LISTEN FOR HOTWORD>>>>>>>>>>>>>>>>>>>>>')
    recognizer = sr.Recognizer()
    microphone = sr.Microphone(sample_rate=16000, device_index=0)

    audio_model = whisper.load_model("base.en")
    print("Model loaded.\n")

    with microphone as source:
        # Adjust for ambient noise
        recognizer.adjust_for_ambient_noise(source)
        # Set energy threshold to increase sensitivity
        recognizer.energy_threshold = 300  # You can lower this value to increase sensitivity
        recognizer.dynamic_energy_threshold = True  # Enable dynamic adjustment

    def record_callback(_, audio: sr.AudioData) -> None:
        data_queue.put(audio.get_raw_data())

    stop_listening = recognizer.listen_in_background(microphone, record_callback, phrase_time_limit=RECORD_TIMEOUT)
    
    process_audio(recognizer, audio_model, data_queue, microphone.SAMPLE_RATE, microphone.SAMPLE_WIDTH, hotword_detected, hotword_text)
    
    stop_listening(wait_for_stop=False)

def main():
    print('<<<<<<<<<<<<<<<<<<<<<ENTERED HOTWORD MAIN>>>>>>>>>>>>>>>>>>>>>') 
    data_queue = mp.Queue()
    hotword_detected = mp.Value(ctypes.c_bool, False)
    hotword_text = mp.Array(ctypes.c_char, 1024)

    listen_process = mp.Process(target=listen_for_hotword, args=(data_queue, hotword_detected, hotword_text))
    listen_process.start()
    listen_process.join()

    return hotword_text.value.decode('utf-8').strip()

if __name__ == "__main__":
    detected_text = main()
    print(f"Detected hotword text: {detected_text}")
