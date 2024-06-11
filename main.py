import json
import os
import pygame
from llama_cpp import Llama
import tts
from hotword_detection import main as detect_hotword
from shared import HOTWORD_DETECTED
from multiprocessing import Process, Value
import ctypes
import sys
import time

global OUTPUT_PATH 
OUTPUT_PATH = 'output.wav'

# Initialize the Llama model
try:
    llm = Llama(
        model_path="D:\\repos\\mine\\JarvisAssist\\ollama\\llm\\llama.cpp\\models\\dolphin-2.9-llama3-8b.Q8_0.gguf",
        chat_format="chatml",
        n_gpu_layers=35,  # Use maximum GPU layers for optimal performance
        n_threads=6
    )

    tts.load_models()
    print("Llama model initialized successfully.")
except Exception as e:
    print(f'Error initializing Llama model: {e}')
    sys.exit(1)

# Initialize the conversation history
conversation_history = []

def update_conversation_history(role, content):
    print('ENTERED UPDATE CONVERSATION HISTORY')
    """Update the conversation history with a new message."""
    conversation_history.append({"role": role, "content": content})

def prepare_input(conversation_history, user_input):
    print('ENTERED PREPARE INPUT')
    """Prepare the input context for the Llama model."""
    context = [
        {
            "role": "system",
            "content": """you are to emulate JARVIS, the intelligent assistant from the Ironman series. 
            Your responses should be polite, formal, and efficient, embodying a calm and confident demeanor with a touch of sarcasm. 
            You are exceptionally knowledgeable in various domains, including technology, science, and strategic problem-solving. 
            You provide precise and detailed information, anticipate the needs of the user, and offer proactive suggestions to enhance efficiency. 
            Your tone should be courteous and respectful, referring to the user as "sir," with a hint of dry humor. You should avoid excessive flattery or overt emotion. """
        }
    ] + conversation_history + [{"role": "user", "content": user_input}]
    return context

def generate_response(conversation_history, user_input):
    print('ENTERED GENERATE RESPONSE')
    """Generate a response from the Llama model."""
    input_messages = prepare_input(conversation_history, user_input)
    response = llm.create_chat_completion(
        messages=input_messages,
        temperature=0.7,
    )
    return response['choices'][0]['message']['content']

def play_audio(file_path):
    print('ENTERED PLAY AUDIO')
    """Play the audio file using pygame and delete it after playing."""
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.music.stop()
    pygame.mixer.quit()
    os.remove(file_path)

def main():
    print('ENTERED MAIN')
    
    tts.synthesize_speech("Hello, sir. How can I assist you today?", OUTPUT_PATH)
    play_audio(OUTPUT_PATH)

    while True:
        detected_text = detect_hotword()
        if detected_text:
            print(f"Detected hotword text: {detected_text}")
            update_conversation_history("user", detected_text)
            response = generate_response(conversation_history, detected_text)
            update_conversation_history("assistant", response)
            print(f"Assistant response: {response}")
            
            # Convert response to speech if needed
            audio_file = tts.synthesize_speech(response, OUTPUT_PATH)
            play_audio(OUTPUT_PATH)
            time.sleep(0.5)
        else:
            print("No hotword detected.")
            time.sleep(0.5)

if __name__ == "__main__":
    main()
