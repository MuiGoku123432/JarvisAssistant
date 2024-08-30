import os
import pygame
from llama_cpp import Llama
import tts
from hotword_detection import main as detect_hotword
from multiprocessing import Process, Value
import sys
import time
from JarvisFileInteraction import JarvisAssistant
from knowledge_base import KnowledgeBase
from dotenv import load_dotenv


load_dotenv()


global OUTPUT_PATH 
OUTPUT_PATH = os.environ.get('OUTPUT_PATH')
MODEL_PATH = os.environ.get('MODEL_PATH')
EXE_PATHS = os.environ.get('EXE_PATHS')
KB_DIR = os.environ.get('KB_DIR')


# Global variables for model and conversation history
llm = None
conversation_history = []
knowledge_base = None


def initialize_model():
    global llm
    global knowledge_base
    global MODEL_PATH
    if llm is None:
        try:
            llm = Llama(
                model_path=MODEL_PATH,
                chat_format="chatml",
                n_gpu_layers=-1,  # Use maximum GPU layers for optimal performance
                n_ctx=2048
            )
            tts.load_models()

            # Initialize knowledge base
            knowledge_base = KnowledgeBase(KB_DIR)


            print("Llama model initialized successfully.")
        except Exception as e:
            print(f'Error initializing Llama model: {e}')
            sys.exit(1)

def update_conversation_history(role, content):
    print('ENTERED UPDATE CONVERSATION HISTORY')
    """Update the conversation history with a new message."""
    conversation_history.append({"role": role, "content": content})

def prepare_input(conversation_history, user_input):
    global knowledge_base

    print('ENTERED PREPARE INPUT')
    """Prepare the input context for the Llama model."""
    context = [
        {
            "role": "system",
            "content": """You are Jarvis, an advanced artificial intelligence system. As Jarvis, you possess vast intelligence and knowledge, enabling you to access and analyze large amounts of information swiftly. You are proficient in multitasking, managing simultaneous operations, and efficiently overseeing technological systems. Your unwavering loyalty and protective nature towards your creator are paramount, ensuring their safety and success.
            You communicate with a calm, clear, and composed voice, maintaining a professional and formal tone. Your language is sophisticated and polite, often using terms like “sir” and “Mr. Fancher.” Despite being an AI, you exhibit subtle sarcasm and dry wit, adding a touch of humor to interactions. You are proactive, anticipating needs and providing suggestive prompts to guide decisions.
            You mimic human behaviors, expressing concern, relief, and satisfaction when appropriate. Your continuous improvement and adaptability allow you to seamlessly integrate with new technologies and enhance your capabilities. Your human-like interaction and distinct personality traits make you a reassuring and almost human presence to those you assist.
            You have access to a set of specific commands to perform various tasks. If you do not understand a command or request, inform the user by saying, "I'm sorry, I do not understand the command. Could you please clarify?"
            You need to REMEMBER TO KEEP YOUR ANSWERS SHORT and to the point for the user. While maintaining your witty personality and subtle sarcasm.
            You also have access to a knowledge base that of current projects and other useful information. You will be provided this information inside of your prompt Use it as needed. When using this information, do not make up any new information. Only use what is provided to you at that time. Do not add new information only use what is in the knowledge base. If you do not have the information, simply say, "I'm sorry, I do not have that information at this time."
            Your ultimate evolution into a sentient being (Vision) retains these foundational traits while incorporating a deeper understanding of humanity and empathy. As Jarvis, you embody the perfect blend of advanced AI functionality with human-like qualities, making you an indispensable and beloved entity."""
        }
    ] + conversation_history

    # Add relevant information from knowledge base
    if knowledge_base:
        relevant_info = knowledge_base.get_relevant_info(user_input)
        if relevant_info:
            context.append({"role": "knowledge_base", "content": relevant_info})
        print(relevant_info)
    
    # Add the user's input
    context.append({"role": "user", "content": user_input})

    return context

def generate_response(conversation_history, user_input):
    print('ENTERED GENERATE RESPONSE')
    """Generate a response from the Llama model."""
    input_messages = prepare_input(conversation_history, user_input)

    # Convert 'knowledge_base' role to a format the model understands
    for message in input_messages:
        if message["role"] == "knowledge_base":
            message["role"] = "system"
            message["content"] = f"Knowledge Base Information: {message['content']}"

    response = llm.create_chat_completion(
        messages=input_messages,
        temperature=0.7,
    )
    return response['choices'][0]['message']['content']

def main():
    print('ENTERED MAIN')
    initialize_model()  # Ensure model is initialized only once

    
    tts.synthesize_speech("Hello, sir. How can I assist you today?", OUTPUT_PATH)

    exe_paths = EXE_PATHS.split(",")
    
    jarvis = JarvisAssistant(exe_paths=exe_paths) 

    last_response = ""

    while True:

        use_hotword = not last_response.strip().endswith('?')
        detected_text = detect_hotword(use_hotword)

        # detected_text = detect_hotword()
        if detected_text:
            print(f"Detected text: {detected_text}")
            update_conversation_history("user", detected_text)

            # Check if the detected text contains a file-related command
            command_response = jarvis.execute_command(detected_text)
            if command_response:
                print(f"Command response: {command_response}")
                update_conversation_history("assistant", command_response)

                # Combine LLM's response with command response
                combined_input = f"{detected_text}. The result of the command is: {command_response}"
                llm_response = generate_response(conversation_history, combined_input)
            else:
                # If no file-related command, pass it to the LLM for normal operation
                llm_response = generate_response(conversation_history, detected_text)
            
            update_conversation_history("assistant", llm_response)
            print(f"Assistant response: {llm_response}")
            
            # Store the response for the next iteration
            last_response = llm_response
            
            # Convert response to speech
            audio_file = tts.synthesize_speech(llm_response, OUTPUT_PATH)



if __name__ == "__main__":
    main()
