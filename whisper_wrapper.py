import pywhispercpp as whisper

def transcribe_audio(audio_path):
    try:
        # Load the Whisper model
        model = whisper.Whisper('base')

        # Transcribe the audio
        result = model.transcribe(audio_path)

        # Return the transcribed text
        print(f"Transcription: {result['text']}")
        return result['text']
    except Exception as e:
        print(f"An error occurred during transcription: {e}")
        return None
