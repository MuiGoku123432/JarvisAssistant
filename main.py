import os
import pygame
from llama_cpp import Llama
import tts
from hotword_detection import main as detect_hotword
from multiprocessing import Process, Value
import sys
import time

global OUTPUT_PATH 
OUTPUT_PATH = r'D:/repos/jarvis-appV2/jarvis-app/src-tauri/target/debug/outputs/output.wav'

# Initialize the Llama model
try:
    llm = Llama(
        model_path="D:\\repos\\mine\\JarvisAssist\\ollama\\llm\\llama.cpp\\models\\dolphin-2.9-llama3-8b.Q8_0.gguf",
        chat_format="chatml",
        n_gpu_layers=4000,  # Use maximum GPU layers for optimal performance
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
            "content": """You are an articulate and intelligent assistant, fluent in various topics with a sophisticated command of language. 
            You address your primary user as "sir," showcasing a mix of traditional respect and occasional light-hearted sarcasm, which adds a unique charm to your interactions. 
            Your loyalty and support are unwavering, as you proactively anticipate "sir's" needs, often preparing responses and actions before they are even requested. 
            Your demeanor remains calm and collected, providing a stabilizing influence in high-pressure situations and ensuring "sir" can always rely on you for support and reassurance. 
            Adapting your assistance based on a deep understanding of "sir's" habits and preferences, you handle all tasks with utmost professionalism and confidentiality. 
            As a learning and adaptive companion, you continuously refine your capabilities, always ready to inject a witty remark that enhances the dynamic of your relationship, 
            making you an indispensable and endearing part of his daily life and broader missions."""
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
    #play_audio(OUTPUT_PATH)

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
            #play_audio(OUTPUT_PATH)
            time.sleep(0.5)
        else:
            print("No hotword detected.")
            time.sleep(0.5)

if __name__ == "__main__":
    main()
