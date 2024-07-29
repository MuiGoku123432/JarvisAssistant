import os
import json
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class KnowledgeBase:
    def __init__(self, data_dir: str, model_name: str = 'all-MiniLM-L6-v2'):
        self.data_dir = data_dir
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.documents = []
        self.load_documents()
        self.create_index()

    def load_documents(self):
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.txt'):
                with open(os.path.join(self.data_dir, filename), 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.documents.append({
                        'content': content,
                        'source': filename
                    })

    def create_index(self):
        embeddings = self.model.encode([doc['content'] for doc in self.documents])
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype('float32'))

    def search(self, query: str, k: int = 3) -> List[Dict[str, str]]:
        query_vector = self.model.encode([query])
        distances, indices = self.index.search(query_vector.astype('float32'), k)
        results = []
        for i in indices[0]:
            results.append(self.documents[i])
        return results

    def add_to_context(self, query: str, context: List[Dict[str, str]]) -> str:
        relevant_docs = self.search(query)
        kb_context = "\n\nRelevant information from knowledge base:\n"
        for doc in relevant_docs:
            kb_context += f"From {doc['source']}:\n{doc['content']}\n\n"
        return kb_context