import speech_recognition as sr
import whisper
import torch
import multiprocessing as mp
from JarvisFileInteraction import JarvisAssistant

# Load the Whisper model
audio_model = whisper.load_model("base.en")
print("Model loaded.\n")

HOTWORD = "jarvis"
DURATION = 5  # Duration in seconds for recording audio

def record_audio(recognizer, microphone, duration):
    """Record audio from the microphone."""
    print("Recording audio...")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)  # Adjust for ambient noise
        recognizer.energy_threshold = 300  # Set energy threshold for more sensitivity
        audio = recognizer.record(source, duration=duration)
    return audio

def transcribe_audio(audio, recognizer, audio_model):
    """Transcribe the recorded audio using Whisper model."""
    print("Transcribing audio...")
    audio_data = sr.AudioData(audio.get_raw_data(), audio.sample_rate, audio.sample_width)
    wav_data = audio_data.get_wav_data()
    temp_file = "temp_audio.wav"
    
    with open(temp_file, 'wb') as f:
        f.write(wav_data)
    
    result = audio_model.transcribe(temp_file, fp16=torch.cuda.is_available())
    return result['text'].strip()

def listen_for_hotword(hotword_detected, hotword_text):
    recognizer = sr.Recognizer()
    microphone = sr.Microphone(sample_rate=16000, device_index=0)

    print("Listening for the hotword...\n")

    while True:
        audio = record_audio(recognizer, microphone, DURATION)
        transcription = transcribe_audio(audio, recognizer, audio_model)

        print(f"Transcription result: {transcription}")
        
        if HOTWORD.lower() in transcription.lower():
            print(f"Hotword '{HOTWORD}' detected!")
            with hotword_text.get_lock():
                hotword_text.value = transcription.encode('utf-8')
            hotword_detected.value = True
            break

def main():
    jarvisFile = JarvisAssistant();
    hotword_detected = mp.Value('b', False)
    hotword_text = mp.Array('c', 1024)

    listen_process = mp.Process(target=listen_for_hotword, args=(hotword_detected, hotword_text))
    listen_process.start()
    listen_process.join()

    if hotword_detected.value:
        detected_text = hotword_text.value.decode('utf-8').strip()
        return detected_text

if __name__ == "__main__":
    detected_text = main()
    print(f"Detected hotword text: {detected_text}")
