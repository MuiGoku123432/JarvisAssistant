import os
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
                    paragraphs = content.split('\n\n')
                    for paragraph in paragraphs:
                        if paragraph.strip():
                            self.documents.append({
                                'content': paragraph.strip(),
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
        for i, dist in zip(indices[0], distances[0]):
            if dist < 3:  # Adjust this threshold as needed
                results.append(self.documents[i])
        return results

    def get_relevant_info(self, query: str) -> str:
        relevant_docs = self.search(query)
        if not relevant_docs:
            return ""  # Return empty string if no relevant information found
        
        relevant_info = ""
        for doc in relevant_docs:
            relevant_info += f"From {doc['source']}:\n{doc['content']}\n\n"
        return relevant_info.strip()