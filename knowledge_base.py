import os
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class KnowledgeBase:
    def __init__(self, data_dir: str, model_name: str = 'all-MiniLM-L6-v2'):
        self.data_dir = data_dir
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.documents = []
        print("Starting to load documents")
        self.load_documents()
        print("Starting to create index")
        self.create_index()
        print("Initialization complete")

    def load_documents(self):
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.txt'):
                file_path = os.path.join(self.data_dir, filename)
                logger.info(f"Processing file: {file_path}")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        projects = self.parse_projects(content)
                        for project in projects:
                            if project:
                                self.documents.append({
                                    'content': project['title'] + '\n' + project['description'],
                                    'source': filename,
                                    'project': project
                                })
                        logger.info(f"Added {len(projects)} projects from {filename}")
                except Exception as e:
                    logger.error(f"Error processing file {filename}: {str(e)}")

        logger.info(f"Loaded {len(self.documents)} documents in total")

    def parse_projects(self, content: str) -> List[Dict]:
        projects = []
        lines = content.split('\n')
        current_project = None
        current_component = None

        for i, line in enumerate(lines, 1):
            try:
                line = line.strip()
                logger.debug(f"Processing line {i}: {line}")

                if line.startswith('Project:'):
                    if current_project:
                        projects.append(current_project)
                        logger.debug(f"Appended project: {current_project['title']}")
                    current_project = {'title': line, 'description': '', 'components': []}
                    logger.debug(f"Started new project: {line}")
                elif line.endswith(':'):
                    if current_project is None:
                        logger.warning(f"Line {i}: Component found before project start: {line}")
                        continue
                    current_component = {'name': line[:-1], 'items': []}
                    current_project['components'].append(current_component)
                    logger.debug(f"Added component to project: {line}")
                elif line.startswith('- '):
                    if current_component:
                        current_component['items'].append(line[2:])
                        logger.debug(f"Added item to component: {line}")
                    elif current_project:
                        current_project['description'] += line + '\n'
                        logger.debug(f"Added description line to project: {line}")
                    else:
                        logger.warning(f"Line {i}: Item found before project or component start: {line}")
                elif line:
                    if current_project:
                        current_project['description'] += line + '\n'
                        logger.debug(f"Added description line to project: {line}")
                    else:
                        logger.warning(f"Line {i}: Text found before project start: {line}")

            except Exception as e:
                logger.error(f"Error processing line {i}: {line}")
                logger.error(f"Error details: {str(e)}")

        if current_project:
            projects.append(current_project)
            logger.debug(f"Appended final project: {current_project['title']}")

        logger.info(f"Parsed {len(projects)} projects")
        return projects

    def create_index(self):
        embeddings = self.model.encode([doc['content'] for doc in self.documents])
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype('float32'))

    def search(self, query: str, k: int = 3) -> List[Dict]:
        query_vector = self.model.encode([query])
        distances, indices = self.index.search(query_vector.astype('float32'), k)
        results = []
        for i, dist in zip(indices[0], distances[0]):
            if dist < 1.75:  # Adjust this threshold as needed
                results.append(self.documents[i])
        return results

    def get_relevant_info(self, query: str) -> str:
        relevant_docs = self.search(query)
        if not relevant_docs:
            return ""  # Return empty string if no relevant information found
        
        relevant_info = ""
        for doc in relevant_docs:
            relevant_info += f"From {doc['source']}:\n"
            relevant_info += f"Project: {doc['project']['title']}\n\n"
            relevant_info += f"Description: {doc['project']['description']}\n\n"
            for component in doc['project']['components']:
                relevant_info += f"{component['name']}:\n"
                for item in component['items']:
                    relevant_info += f"  - {item}\n"
            relevant_info += "\n"
        return relevant_info.strip()