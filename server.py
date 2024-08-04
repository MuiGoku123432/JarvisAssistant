import asyncio
import websockets
import json
import logging
from main import initialize_model, generate_response, update_conversation_history
from JarvisFileInteraction import JarvisAssistant
from hotword_detection import listen_for_hotword, listen_without_hotword
import tts
import os
from dotenv import load_dotenv
from multiprocessing import Value, Array
import time

class ListeningState:
    IDLE = 0
    LISTENING = 1
    PROCESSING = 2

listening_state = Value('i', ListeningState.IDLE)


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_PATH = os.environ.get('OUTPUT_PATH')
MODEL_PATH = os.environ.get('MODEL_PATH')
EXE_PATHS = os.environ.get('EXE_PATHS').split(",")
KB_DIR = os.environ.get('KB_DIR')

conversation_history = []


jarvis = JarvisAssistant(exe_paths=EXE_PATHS)
initialize_model()
tts.load_models()
logger.info("Models initialized successfully.")

tts.synthesize_speech("Hello, sir. How can I assist you today?", OUTPUT_PATH)

last_response = ""

# Create shared variables for hotword detection
hotword_detected = Value('b', False)
hotword_text = Array('c', 1024)

async def listen_for_input(use_hotword):
    global hotword_detected, hotword_text
    
    if use_hotword:
        logger.info("Listening for hotword...")
        hotword_detected.value = False
        hotword_text.value = b''
        await asyncio.to_thread(listen_for_hotword, hotword_detected, hotword_text)
        if hotword_detected.value:
            return hotword_text.value.decode('utf-8').strip()
    else:
        logger.info("Listening without hotword...")
        return await asyncio.to_thread(listen_without_hotword)
    
    return None

async def process_command(websocket, user_input):
    global last_response
    
    
    logger.info(f"Processing command: {user_input}")
    command_response = jarvis.execute_command(user_input)
    
    if command_response:
        update_conversation_history("user", user_input)
        update_conversation_history("assistant", command_response)
        combined_input = f"{user_input}. The result of the command is: {command_response}"
        llm_response = generate_response(conversation_history, combined_input)
    else:
        update_conversation_history("user", user_input)
        llm_response = generate_response(conversation_history, user_input)
    
    update_conversation_history("assistant", llm_response)
    last_response = llm_response
    
    audio_file = tts.synthesize_speech(llm_response, OUTPUT_PATH)

    logger.info(f"Finished processing command: {user_input}")
    logger.info(f"Sending response: {llm_response[:50]}...")
    
    await websocket.send(json.dumps({
        "type": "chat_response",
        "response": llm_response,
        "audio_path": OUTPUT_PATH
    }))

async def handle_client(websocket, path):
    global last_response, listening_state
    
    try:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            command = data.get('command')

            if command == 'listen' and listening_state.value == ListeningState.IDLE:
                listening_state.value = ListeningState.LISTENING
                use_hotword = not last_response.strip().endswith('?')
                detected_text = await listen_for_input(use_hotword)
                
                if detected_text:
                    logger.info(f"Detected text: {detected_text}")
                    await websocket.send(json.dumps({
                        "type": "listen_response",
                        "detected_text": detected_text
                    }))
                    listening_state.value = ListeningState.PROCESSING
                    await process_command(websocket, detected_text)
                    listening_state.value = ListeningState.IDLE
                else:
                    logger.info("No speech detected")
                    await websocket.send(json.dumps({
                        "type": "listen_response",
                        "detected_text": None
                    }))
                    listening_state.value = ListeningState.IDLE
            elif command == 'chat' and listening_state.value == ListeningState.IDLE:
                listening_state.value = ListeningState.PROCESSING
                user_input = data.get('message')
                await process_command(websocket, user_input)
                listening_state.value = ListeningState.IDLE
            elif command == 'stop_listening':
                logger.info("Stopping listening")
                listening_state.value = ListeningState.IDLE
                await websocket.send(json.dumps({
                    "type": "stop_listening_response",
                    "status": "ok"
                }))
            else:
                logger.info(f"Ignoring command {command} due to current state: {listening_state.value}")

    except websockets.exceptions.ConnectionClosed:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"Error in handle_client: {e}")
    finally:
        listening_state.value = ListeningState.IDLE

async def main():
    logger.info("Starting WebSocket server...")
    server = await websockets.serve(handle_client, "0.0.0.0", 8765)
    logger.info("WebSocket server is running on ws://localhost:8765")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())