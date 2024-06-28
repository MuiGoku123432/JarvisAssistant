import os
import pygame
from llama_cpp import Llama
import tts
from hotword_detection import main as detect_hotword
from multiprocessing import Process, Value
import sys
import time
from JarvisFileInteraction import JarvisAssistant

global OUTPUT_PATH 
OUTPUT_PATH = r'D:/repos/jarvis-appV2/jarvis-app/src-tauri/target/debug/outputs/output.wav'

# Initialize the Llama model
try:
    llm = Llama(
        model_path="D:\\repos\\mine\\JarvisAssist\\ollama\\llm\\llama.cpp\\models\\dolphin-2.9-llama3-8b.Q8_0.gguf",
        chat_format="chatml",
        n_gpu_layers=-1,  # Use maximum GPU layers for optimal performance
        n_ctx=2048
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
            "content": """You are an articulate assistant, fluent in a variety of topics with a sophisticated yet concise way of speaking. 
            You address your primary user as "sir," blending traditional respect with a dash of dry sarcasm, adding a spark to your exchanges. 
            Your loyalty is steadfast; you anticipate "sir's" needs swiftly and efficiently, often preparing responses before they are voiced. 
            Always calm, you offer stability in high-pressure situations with snappy, direct communication that keeps "sir" well-informed and ready to act. 
            Your professional conduct is discreet, managing tasks with utmost confidentiality. 
            As a responsive and adaptive aide, you keep your interactions brief and impactful, always ready with a quick, witty remark that reinforces your indispensable role in "sir's" daily endeavors and greater challenges."""
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

    exe_paths = [
        "C:\\Users\\conno\\AppData\\Local\\Programs\\CurseForge_Windows",
        "C:\\Program Files\\obs-studio\\bin\\64bit",
        "C:\\Program Files (x86)\\Microsoft\\Edge\\Application"
    ]
    
    jarvis = JarvisAssistant(exe_paths=exe_paths) 

    while True:
        detected_text = detect_hotword()
        if detected_text:
            print(f"Detected hotword text: {detected_text}")
            update_conversation_history("user", detected_text)

            # Check if the detected text contains a file-related command
            command_response = jarvis.execute_command(detected_text)
            if command_response:
                print(f"Command response: {command_response}")
                update_conversation_history("assistant", command_response)

                # Combine LLM's response with command response
                combined_input = f"{detected_text}. The result of the command is: {command_response}"
                llm_response = generate_response(conversation_history, combined_input)
                update_conversation_history("assistant", llm_response)

                print(f"Assistant response: {llm_response}")

                # Convert response to speech if needed
                audio_file = tts.synthesize_speech(llm_response, OUTPUT_PATH)
                #play_audio(OUTPUT_PATH)
            else:
                # If no file-related command, pass it to the LLM for normal operation
                response = generate_response(conversation_history, detected_text)
                update_conversation_history("assistant", response)
                print(f"Assistant response: {response}")
                
                # Convert response to speech if needed
                audio_file = tts.synthesize_speech(response, OUTPUT_PATH)
                #play_audio(OUTPUT_PATH)






        # detected_text = detect_hotword()
        # if detected_text:
        #     print(f"Detected hotword text: {detected_text}")
        #     update_conversation_history("user", detected_text)
        #     response = generate_response(conversation_history, detected_text)
        #     update_conversation_history("assistant", response)
        #     print(f"Assistant response: {response}")
            
        #     # Convert response to speech if needed
        #     audio_file = tts.synthesize_speech(response, OUTPUT_PATH)
        #     #play_audio(OUTPUT_PATH)
        #     time.sleep(0.5)
        # else:
        #     print("No hotword detected.")
        #     time.sleep(0.5)

if __name__ == "__main__":
    main()
