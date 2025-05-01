# embeddings.py
from sentence_transformers import SentenceTransformer
from db import Session, Conversation

_model = SentenceTransformer("all-MiniLM-L6-v2")
_session = Session()

def log_message(role: str, text: str):
    vec = _model.encode(text).astype("float32").tolist()
    msg = Conversation(role=role, message=text, embedding=vec)
    _session.add(msg)
    _session.commit()

def fetch_similar(text: str, k: int = 5):
    q_vec = _model.encode(text).astype("float32").tolist()
    results = (
        _session.query(Conversation)
                .order_by(Conversation.embedding.op("<->")(q_vec))
                .limit(k)
                .all()
    )
    return [r.message for r in results]
