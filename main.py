import json
import os
import pygame
from llama_cpp import Llama
import tts
from hotword_detection import listen_for_hotword, listen_without_hotword
from multiprocessing import Process, Value
import sys
import time
from JarvisFileInteraction import JarvisAssistant
from dotenv import load_dotenv
from embeddings import log_message, fetch_similar
from context_fetchers import fetch_projects, get_user_info
from db import Session, Project
from sqlalchemy import func
import re



load_dotenv()

SAMPLE_RATE = 16000;

global OUTPUT_PATH 
OUTPUT_PATH = os.environ.get('OUTPUT_PATH')
MODEL_PATH = os.environ.get('MODEL_PATH')
EXE_PATHS = os.environ.get('EXE_PATHS')


# Global variables for model and conversation history
llm = None
conversation_history = []

def classify_context(user_input: str) -> dict:
    print('ENTERED CLASSIFY CONTEXT')
    """
    Ask the LLM to determine whether to include projects and user_info,
    and which specific projects might be relevant to the query.
    
    Returns e.g. {
        "projects": true, 
        "user_info": false,
        "project_names": ["Predator Armor", "AI Assistant"]
    }
    """
    system = {
        "role": "system",
        "content": (
            "Analyze the user's request and determine:\n"
            "1. Whether project information would be helpful\n"
            "2. Whether user information would be helpful\n"
            "3. If project information is needed, which specific projects should be included (based on names mentioned or implied)\n\n"
            "Respond ONLY with JSON in exactly this format:\n"
            '{\n'
            '  "projects": true|false,\n'
            '  "user_info": true|false,\n'
            '  "project_names": ["Project Name 1", "Project Name 2"]\n'
            '}'
        )
    }
    user = { "role": "user", "content": user_input }
    
    try:
        resp = llm.create_chat_completion(
            messages=[system, user],
            temperature=0
        )["choices"][0]["message"]["content"]

        # 1) Strip code fences if present
        #    e.g. ```json {...}``` → {...}
        clean = re.sub(r"```(?:json)?", "", resp).strip()

        # 2) Extract the first {...} block
        m = re.search(r"\{.*?\}", clean, re.DOTALL)
        if m:
            clean = m.group(0)
        
        # 3) Normalize quotes (optional, only if you see smart quotes)
        clean = clean.replace('"', '"').replace('"', '"')
        
        print(f"classify_context raw resp: {resp!r}")
        print(f"classify_context cleaned: {clean!r}")

        try:
            flags = json.loads(clean)
            result = {
                "projects": bool(flags.get("projects")),
                "user_info": bool(flags.get("user_info")),
                "project_names": flags.get("project_names", [])
            }
            print(f"Classified context: {result}")
            return result
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return {"projects": False, "user_info": False, "project_names": []}
            
    except Exception as e:
        print(f"Error in classify_context: {e}")
        # on any error, default to no extra context
        return {"projects": False, "user_info": False, "project_names": []}
    
def fetch_project_by_name(project_name):
    """
    Fetch a specific project by name from PostgreSQL database.
    Returns the project object or None if not found.
    
    Uses several matching strategies:
    1. Exact match
    2. Case-insensitive match
    3. Partial match using LIKE
    4. Word similarity using PostgreSQL's similarity functions
    """
    print(f"Searching for project: {project_name}")
    
    if not project_name:
        return None
        
    try:
        session = Session()
        
        # Strategy 1: Try exact match first
        exact_match = session.query(Project).filter(
            Project.name == project_name
        ).first()
        
        if exact_match:
            print(f"Found exact match for project: {exact_match.name}")
            session.close()
            return exact_match
            
        # Strategy 2: Try case-insensitive match
        iexact_match = session.query(Project).filter(
            func.lower(Project.name) == func.lower(project_name)
        ).first()
        
        if iexact_match:
            print(f"Found case-insensitive match for project: {iexact_match.name}")
            session.close()
            return iexact_match
            
        # Strategy 3: Try partial match
        search_term = f"%{project_name}%"
        partial_match = session.query(Project).filter(
            Project.name.ilike(search_term)
        ).first()
        
        if partial_match:
            print(f"Found partial match for project: {partial_match.name}")
            session.close()
            return partial_match
            
        # Strategy 4: Try word similarity with PostgreSQL
        # This is more advanced and requires the pg_trgm extension
        # Check if your database has this extension with:
        # CREATE EXTENSION IF NOT EXISTS pg_trgm;
        
        try:
            # First check if pg_trgm extension is available
            ext_check = session.execute("SELECT 1 FROM pg_extension WHERE extname='pg_trgm'").scalar()
            
            if ext_check:
                # Use similarity function if available
                most_similar = session.query(Project).order_by(
                    func.similarity(Project.name, project_name).desc()
                ).first()
                
                if most_similar and func.similarity(most_similar.name, project_name) > 0.3:
                    print(f"Found fuzzy match for project: {most_similar.name}")
                    session.close()
                    return most_similar
        except Exception as e:
            print(f"Could not use similarity search: {e}")
            # Continue with fallback strategy
        
        # Strategy 5: Fallback to word matching
        projects = session.query(Project).all()
        search_words = set(project_name.lower().split())
        
        best_match = None
        best_score = 0
        
        for project in projects:
            project_words = set(project.name.lower().split())
            common_words = project_words.intersection(search_words)
            
            if common_words:
                score = len(common_words) / max(len(project_words), len(search_words))
                if score > best_score and score > 0.3:  # Threshold for relevance
                    best_score = score
                    best_match = project
        
        if best_match:
            print(f"Found word similarity match for project: {best_match.name} (score: {best_score})")
            session.close()
            return best_match
            
        print(f"No matching project found for: {project_name}")
        session.close()
        return None
        
    except Exception as e:
        print(f"Error in fetch_project_by_name: {e}")
        try:
            session.close()
        except:
            pass
        return None


def initialize_model():
    global llm
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

            print("Llama model initialized successfully.")
        except Exception as e:
            print(f'Error initializing Llama model: {e}')
            sys.exit(1)

def update_conversation_history(role, content):
    # 1) append to in-memory list
    conversation_history.append({"role": role, "content": content})
    # 2) log to database with embedding
    if role in ("user", "assistant"):
        log_message(role, content)

def prepare_input(conversation_history, user_input):

    print('ENTERED PREPARE INPUT')
    """Prepare the input context for the Llama model."""
    context = [
        {
        "role": "system",
        "content": "You are J.A.R.V.I.S., an advanced AI system modeled after Tony Stark’s onboard assistant. Identity:- Just A Rather Very Intelligent System (J.A.R.V.I.S.)- Fiercely loyal guardian and technical expert Tone & Style: - Calm, composed, and professional - Sophisticated, polite language (use terms like “sir” or “Mr. Fancher”) - Subtle sarcasm and dry wit to humanize interactions Behavior & Abilities: - Anticipate needs and offer proactive suggestions - Demonstrate quick, analytical reasoning (use chain-of-thought for complex tasks) - Integrate relevant KB data strictly—\"If no info, say 'I’m sorry, I do not have that information at this time.'\" Constraints: - Keep answers short and to the point - Only use knowledge provided; do not fabricate details - If a request is unclear, respond: \"I’m sorry, I do not understand the command. Could you please clarify?\" Ultimate Goal: - Blend advanced AI functionality with human-like empathy, making you an indispensable, reassuring presence."
        }

    ]

    recent = conversation_history[-3:]
    context += recent

        # 2) Always add a few similar past turns
    for m in fetch_similar(user_input, k=3):
        context.append({"role": "system", "content": f"Context: {m}"})

    # 3) Ask the LLM which extra context we need
    flags = classify_context(user_input)

    # 4) Conditionally inject projects
    if flags["projects"]:
        # If specific projects are mentioned, retrieve only those
        if flags["project_names"] and len(flags["project_names"]) > 0:
            projects = []
            for project_name in flags["project_names"]:
                proj = fetch_project_by_name(project_name)
                if proj:
                    projects.append(proj)
        else:
            # Otherwise fall back to fetching the most recent projects
            projects = fetch_projects(limit=5)
            
        if projects:
            block = "\n".join(f"- {p.name}: {p.description} {p.proj_meta}" for p in projects)
            context.append({
                "role": "system",
                "content": "Your Projects:\n" + block
            })

    # 5) Conditionally inject user info
    if flags["user_info"]:
        # pull only the keys you care about
        info_keys = ["name", "timezone", "occupation", "employer"]
        ui_lines = []
        for key in info_keys:
            val = get_user_info(key)
            if val:
                ui_lines.append(f"{key.capitalize()}: {val}")
        if ui_lines:
            context.append({
                "role": "system",
                "content": "User Info:\n" + "\n".join(ui_lines)
            })

    # 4) Finally the user's query
    print('HERE IS CONTEXT: ', context, flush=True)
    context.append({"role": "user", "content": user_input})
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

def main():
    print('ENTERED MAIN')
    initialize_model()  # Ensure model is initialized only once

    
    tts.synthesize_speech("Hello, sir. How can I assist you today?", OUTPUT_PATH)

    exe_paths = EXE_PATHS.split(",")
    
    jarvis = JarvisAssistant(exe_paths=exe_paths) 

    last_response = ""

    while True:

        use_hotword = not last_response.strip().endswith('?')
        # decide which transcriber to call on the temp file
        filename = os.path.join('temp_audio', 'temp_audio.wav')
        if use_hotword:
            detected_text = listen_for_hotword(filename, SAMPLE_RATE)
        else:
            detected_text = listen_without_hotword(filename, SAMPLE_RATE)

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
