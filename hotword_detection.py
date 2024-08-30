import speech_recognition as sr
import whisper
import torch
import multiprocessing as mp
from JarvisFileInteraction import JarvisAssistant
import time
import os
import soundfile as sf
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the Whisper model
audio_model = whisper.load_model("base.en")
print("Model loaded.\n")

HOTWORD = "jarvis"
DURATION = 5  # Duration in seconds for recording audio

def list_microphones():
    """List available microphones."""
    mic_list = sr.Microphone.list_microphone_names()
    return [{"index": i, "name": name} for i, name in enumerate(mic_list)]

def record_audio(recognizer, microphone, duration):
    """Record audio from the microphone."""
    print("Recording audio...")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)  # Adjust for ambient noise
        recognizer.energy_threshold = 300  # Set energy threshold for more sensitivity
        audio = recognizer.record(source, duration=duration)
    return audio

# def transcribe_audio(audio, audio_model):
#     """Transcribe the recorded audio using Whisper model."""
#     print("Transcribing audio...")
#     audio_data = sr.AudioData(audio.get_raw_data(), audio.sample_rate, audio.sample_width)
#     wav_data = audio_data.get_wav_data()
#     temp_file = "temp_audio.wav"
    
#     with open(temp_file, 'wb') as f:
#         f.write(wav_data)
    
#     result = audio_model.transcribe(temp_file, fp16=torch.cuda.is_available())
#     return result['text'].strip()
def transcribe_audio(audio_file, audio_model):
    recognizer = sr.Recognizer()


    """Transcribe the recorded audio using Whisper model."""
    logger.info(type(audio_file))
    audioPre = sr.AudioFile(audio_file)
    logger.info(type(audioPre))
    with audioPre as source:
        audio = recognizer.record(source)
        logger.info(type(audio))

    print("Transcribing audio...")
    audio_data = sr.AudioData(audio.get_raw_data(), audio.sample_rate, audio.sample_width)
    wav_data = audio_data.get_wav_data()
    temp_file = "temp_audio.wav"
    
    with open(temp_file, 'wb') as f:
        f.write(wav_data)
    
    result = audio_model.transcribe(temp_file, fp16=torch.cuda.is_available())
    return result['text'].strip()

def listen_for_hotword(audio_data, sample_rate):
    print("Listening for the hotword...\n")
    transcription = transcribe_audio(audio_data, audio_model)

    logger.info(f"Transcription result: {transcription}")
    
    if HOTWORD.lower() in transcription.lower():
        print(f"Hotword '{HOTWORD}' detected!")
        return transcription.strip()            
    else:
        return None

def listen_without_hotword(audio_data, sample_rate, duration=DURATION):
    time.sleep(5)

    print("Listening for response...")
    transcription = transcribe_audio(audio_data, audio_model)

    print(f"Transcription result: {transcription}")
    
    return transcription.strip()

def main(use_hotword=True):
    if use_hotword:
        jarvisFile = JarvisAssistant();
        hotword_detected = mp.Value('b', False)
        hotword_text = mp.Array('c', 1024)

        listen_process = mp.Process(target=listen_for_hotword, args=(hotword_detected, hotword_text))
        listen_process.start()
        listen_process.join()

        if hotword_detected.value:
            detected_text = hotword_text.value.decode('utf-8').strip()
            return detected_text
    else:
        return listen_without_hotword()
    
    return None

if __name__ == "__main__":
    detected_text = main()
    print(f"Detected hotword text: {detected_text}")
