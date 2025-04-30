# embeddings.py
from sentence_transformers import SentenceTransformer
from db import Session, Conversation

model   = SentenceTransformer("all-MiniLM-L6-v2")
session = Session()

def log_message(role: str, text: str):
    vec = model.encode(text).astype("float32").tolist()
    msg = Conversation(role=role, message=text, embedding=vec)
    session.add(msg)
    session.commit()
    return msg.id
