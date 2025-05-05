# hotword_detection.py
import speech_recognition as sr
import whisper
import torch
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the Whisper model once
audio_model = whisper.load_model("base.en")
logger.info("Whisper model loaded.")

HOTWORD = "jarvis"

def transcribe_audio(audio_file: str) -> str:
    """Use Whisper to transcribe the given WAV file."""
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)
    logger.info("Transcribing audio with Whisper...")
    # write to temp file for whisper
    wav_bytes = audio.get_wav_data()
    temp_path = "temp_audio.wav"
    with open(temp_path, "wb") as f:
        f.write(wav_bytes)
    result = audio_model.transcribe(temp_path, fp16=torch.cuda.is_available())
    return result["text"].strip()

def listen_for_hotword(audio_file: str, sample_rate: int) -> str | None:
    """
    Transcribe the entire audio file, and return the transcription
    if it contains the HOTWORD; otherwise None.
    """
    text = transcribe_audio(audio_file)
    logger.info(f"Full transcription: {text}")
    if HOTWORD.lower() in text.lower():
        logger.info(f"Hotword '{HOTWORD}' detected.")
        return text
    return None

def listen_without_hotword(audio_file: str, sample_rate: int) -> str:
    """
    Simply transcribe the entire audio file without checking for hotword.
    """
    return transcribe_audio(audio_file)
