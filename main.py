import json
import os
import sounddevice as sd
from llama_cpp import Llama
from TTS.api import TTS

# Initialize the Llama model
llm = Llama(
    model_path="D:\\repos\\mine\\JarvisAssist\\ollama\\llm\\llama.cpp\\models\\dolphin-2.9-llama3-8b.Q8_0.gguf",
    chat_format="chatml",
    n_gpu_layers=-1  # Uncomment to use GPU acceleration
    # seed=1337,        # Uncomment to set a specific seed
    # n_ctx=2048,       # Uncomment to increase the context window
)

# Initialize the TTS model
tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False, gpu=True)
default_sampling_rate = 22050  # Set a default sampling rate

# Initialize the conversation history
conversation_history = []

def update_conversation_history(role, content):
    conversation_history.append({"role": role, "content": content})

def prepare_input(conversation_history, user_input):
    context = [
        {
            "role": "system",
            "content": "You are Jarvis, an intelligent assistant. Provide concise and accurate information in plain text."
        }
    ] + conversation_history + [{"role": "user", "content": user_input}]
    return context

def generate_response(conversation_history, user_input):
    input_messages = prepare_input(conversation_history, user_input)
    response = llm.create_chat_completion(
        messages=input_messages,
        temperature=0.7,
    )
    return response['choices'][0]['message']['content']

def text_to_speech(text):
    wav = tts.tts(text)
    sd.play(wav, samplerate=default_sampling_rate)
    sd.wait()

def main():
    print("Jarvis: Hello, I am Jarvis. How can I assist you today?")
    text_to_speech("Hello, I am Jarvis. How can I assist you today?")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Jarvis: Goodbye!")
            text_to_speech("Goodbye!")
            break
        response = generate_response(conversation_history, user_input)
        print(f"Jarvis: {response}")
        text_to_speech(response)
        update_conversation_history("user", user_input)
        update_conversation_history("assistant", response)

if __name__ == "__main__":
    main()
