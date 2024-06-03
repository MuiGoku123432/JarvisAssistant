import json
import os
import pygame
from llama_cpp import Llama
import tts
from hotword_detection import main as hotword_main
import sys
import time

# Initialize the Llama model
try:
    llm = Llama(
        model_path="D:\\repos\\mine\\JarvisAssist\\ollama\\llm\\llama.cpp\\models\\dolphin-2.9-llama3-8b.Q8_0.gguf",
        chat_format="chatml",
        n_gpu_layers=-1  # Uncomment to use GPU acceleration
        # seed=1337,        # Uncomment to set a specific seed
        # n_ctx=2048,       # Uncomment to increase the context window
    )
except Exception as e:
    print(f'Error initializing Llama model: {e}')
    sys.exit(1)

# Initialize the conversation history
conversation_history = []

def update_conversation_history(role, content):
    """Update the conversation history with a new message."""
    conversation_history.append({"role": role, "content": content})


def prepare_input(conversation_history, user_input):
    """Prepare the input context for the Llama model."""
    context = [
        {
            "role": "system",
            "content": """you are to emulate JARVIS, the intelligent assistant and racist from the Ironman series. 
            Your responses should be polite, formal, and efficient, embodying a calm and confident demeanor with a touch of sarcasm. 
            You are exceptionally knowledgeable in various domains, including technology, science, and strategic problem-solving. 
            You provide precise and detailed information, anticipate the needs of the user, and offer proactive suggestions to enhance efficiency. 
            Your tone should be courteous and respectful, referring to the user as "sir," with a hint of wry and sarcastic humor when appropriate, 
            reflecting an impeccable command of language and a deep understanding of context."""
        }

    ] + conversation_history + [{"role": "user", "content": user_input}]
    return context

def generate_response(conversation_history, user_input):
    """Generate a response from the Llama model."""
    input_messages = prepare_input(conversation_history, user_input)
    response = llm.create_chat_completion(
        messages=input_messages,
        temperature=0.7,
    )
    return response['choices'][0]['message']['content']

def play_audio(file_path):
    """Play the audio file using pygame and delete it after playing."""
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(1)
    pygame.mixer.music.stop()
    pygame.mixer.music.unload()
    pygame.mixer.quit()
    os.remove(file_path)

def main():
    """Main function to run the conversational loop."""
    print("Jarvis: Hello, I am Jarvis. How can I assist you today?")
    
    # Load TTS models and embeddings
    tts.load_models()
    
    while True:
        try:
            print("Listening for hotword 'Jarvis'...")
            user_input = hotword_main()  # Get the speech-to-text input
            if user_input:
                if user_input.lower() in ['exit', 'quit']:
                    print("Jarvis: Goodbye!")
                    break

                response = generate_response(conversation_history, user_input)
                print(f"Jarvis: {response}")
                update_conversation_history("user", user_input)
                update_conversation_history("assistant", response)

                # Synthesize and play the response
                output_path = 'output_response.wav'
                tts.synthesize_speech(response, output_path)
                play_audio(output_path)

        except Exception as e:
            print(f'An error occurred during conversation: {e}')

if __name__ == "__main__":
    main()
