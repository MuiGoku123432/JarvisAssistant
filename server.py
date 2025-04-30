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
import base64
from urllib.parse import parse_qs
from flask import Flask, send_file, request
from flask_cors import CORS
import threading
import uuid
import soundfile as sf
import io
import numpy as np
import wave
from flask import jsonify
from collections.abc import Sequence


#DURATION = 5  # Duration in seconds

class ListeningState:
    IDLE = 0
    LISTENING = 1
    PROCESSING = 2

listening_state = Value('i', ListeningState.IDLE)


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_PATH = os.environ.get('MODEL_PATH')
EXE_PATHS = os.environ.get('EXE_PATHS').split(",")
KB_DIR = os.environ.get('KB_DIR')

conversation_history = []


jarvis = JarvisAssistant(exe_paths=EXE_PATHS)
initialize_model()
tts.load_models()
logger.info("Models initialized successfully.")



last_response = ""

# Initialize Flask app
app = Flask(__name__)
CORS(app)
AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audio_files')
os.makedirs(AUDIO_DIR, exist_ok=True)

tts.synthesize_speech("Hello, sir. How can I assist you today?", AUDIO_DIR)

UPLOAD_FOLDER = 'temp_audio'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    if 'audio' not in request.files:
        return 'No audio file', 400
    
    file = request.files['audio']
    if file.filename == '':
        return 'No selected file', 400
    
    if file:
        filename = 'temp_audio.wav'
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        logger.info(f"Saved audio file: {filepath}")
        logger.info(f"File size: {os.path.getsize(filepath)} bytes")
        
        try:
            with wave.open(filepath, 'rb') as wav_file:
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                framerate = wav_file.getframerate()
                frames = wav_file.getnframes()
            
            logger.info(f"Uploaded audio file: {filepath}")
            logger.info(f"Channels: {channels}, Sample Width: {sample_width}, Framerate: {framerate}, Frames: {frames}")
            
            return 'File uploaded and verified successfully', 200
        except EOFError:
            logger.error(f"EOFError: The WAV file appears to be empty or corrupted: {filepath}")
            return 'Invalid WAV file: File is empty or corrupted', 400
        except wave.Error as e:
            logger.error(f"Wave error: {str(e)}")
            return f'Invalid WAV file: {str(e)}', 400
        except Exception as e:
            logger.error(f"Unexpected error processing WAV file: {str(e)}")
            return 'Error processing audio file', 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_file(os.path.join(AUDIO_DIR, filename), mimetype='audio/wav')

# Create shared variables for hotword detection
hotword_detected = Value('b', False)
hotword_text = Array('c', 1024)

def cleanup_old_audio_files(max_age_hours=24):
    current_time = time.time()
    for filename in os.listdir(AUDIO_DIR):
        file_path = os.path.join(AUDIO_DIR, filename)
        if os.path.isfile(file_path):
            file_age = current_time - os.path.getmtime(file_path)
            if file_age > max_age_hours * 3600:
                os.remove(file_path)
                logger.info(f"Deleted old audio file: {filename}")

async def periodic_cleanup():
    while True:
        cleanup_old_audio_files()
        await asyncio.sleep(3600)  # Sleep for 1 hour


async def listen_for_input(use_hotword):
    filepath = os.path.join(UPLOAD_FOLDER, 'temp_audio.wav')
    logger.info(f"Processing audio file: {filepath}")

    if not os.path.exists(filepath):
        logger.error(f"Audio file not found: {filepath}")
        return None
    
    sample_rate = 16000  # Assuming 16kHz sample rate, adjust if different

    try:
        if use_hotword:
            logger.info("Checking for hotword in mobile audio...")
            return await asyncio.to_thread(listen_for_hotword, filepath, sample_rate)
        else:
            logger.info("Transcribing mobile audio without hotword check...")
            return await asyncio.to_thread(listen_without_hotword, filepath, sample_rate)
    except Exception as e:
        logger.error(f"Error processing mobile audio: {str(e)}")
        return None
    finally:
        # Clean up the temporary file
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Deleted temporary audio file: {filepath}")

async def process_command(websocket, user_input):
    global last_response
    
    logger.info(f"Processing command: {user_input}")
    command_response = jarvis.execute_command(user_input)
    logger.info(f"Raw command_response type: {type(command_response)}, value: {command_response}")


    if isinstance(command_response, Sequence) and not isinstance(command_response, str):
         # 1) flatten the list into a single string block
        files_block = "\n".join(f"- {p}" for p in command_response) or "*(none found)*"

        # 2) update history with raw results as system info
        update_conversation_history("user", user_input)
        update_conversation_history("assistant", f"Search results:\n{files_block}")

        # 3) ask the LLM to craft a friendly reaction
        prompt = (
            "I ran a file search for your query and got the following results:\n"
            f"{files_block}\n\n"
            "Please respond back to the user with a friendly summary and next steps."
        )
        llm_response = generate_response(conversation_history, prompt)
    
    elif command_response:
        update_conversation_history("user", user_input)
        update_conversation_history("assistant", command_response)
        combined_input = f"{user_input}. The result of the command is: {command_response}"
        llm_response = generate_response(conversation_history, combined_input)

    else:
        update_conversation_history("user", user_input)
        llm_response = generate_response(conversation_history, user_input)
    
    update_conversation_history("assistant", llm_response)
    last_response = llm_response
    
    logger.info(f"Generating speech for response: {llm_response[:50]}...")
    
    audio_filename = f"output_{int(time.time())}.wav"
    audio_file_path = os.path.join(AUDIO_DIR, audio_filename)
    
    tts.synthesize_speech(llm_response, audio_file_path)
    
    if not os.path.exists(audio_file_path):
        logger.error(f"Failed to generate audio file or file does not exist: {audio_file_path}")
        return None
    
    audio_url = f"http://192.168.254.23:5000/audio/{audio_filename}"
    
    logger.info(f"Finished processing command: {user_input}")
    logger.info(f"Sending response: {llm_response[:50]}...")
    
    return {
        "type": "chat_response",
        "response": llm_response,
        "audio_url": audio_url
    }

async def handle_client(websocket, path):
    global listening_state, last_response
    
    logger.info("New client connected")
    
    try:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            
            if data['type'] == 'listen':
                listening_state.value = ListeningState.LISTENING
                use_hotword = not last_response.strip().endswith('?')
                await websocket.send(json.dumps({"type": "start_listening"}))
                
            elif data['type'] == 'process_audio':
                try:
                    listening_state.value = ListeningState.PROCESSING
                    filepath = os.path.join(UPLOAD_FOLDER, 'temp_output.wav')
                    
                    use_hotword = not last_response.strip().endswith('?')
                    detected_text = await listen_for_input(use_hotword)

                    if detected_text:
                        logger.info(f"Detected text: {detected_text}")
                        await websocket.send(json.dumps({
                            "type": "transcription_result",
                            "text": detected_text
                        }))
                        # response = await process_command(websocket, detected_text)
                        # if response:
                        #     await websocket.send(json.dumps(response))
                        result = await process_command(websocket, detected_text)
                        # if process_command already sent a file_response, it returns None
                        if result:
                            await websocket.send(json.dumps(result))
                    else:
                        logger.info("No valid speech detected")
                        await websocket.send(json.dumps({
                            "type": "transcription_result",
                            "text": None
                        }))
                
                except Exception as e:
                    logger.error(f"Error processing audio: {str(e)}")
                finally:
                    listening_state.value = ListeningState.IDLE
                    # Ensure the file is deleted even if an exception occurred
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        logger.info(f"Deleted temporary audio file: {filepath}")
                    await websocket.send(json.dumps({"type": "start_listening"}))

            elif data['type'] == 'stop_listening': 
                listening_state.value = ListeningState.IDLE
                await websocket.send(json.dumps({
                    "type": "stop_listening_response",
                    "status": "ok"
                }))

            else:
                logger.warning(f"Received unknown message type: {data['type']}")

    except websockets.exceptions.ConnectionClosed:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"Error in handle_client: {e}")
    finally:
        listening_state.value = ListeningState.IDLE
        logger.info("Client disconnected")

def run_flask():
    app.run(host='0.0.0.0', port=5000)

async def main():
    logger.info("Starting WebSocket server...")
    server = await websockets.serve(handle_client, "0.0.0.0", 8765)
    logger.info("WebSocket server is running on ws://localhost:8765")
    
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    asyncio.create_task(periodic_cleanup())

    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())