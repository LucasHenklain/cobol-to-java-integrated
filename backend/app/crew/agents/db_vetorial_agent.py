import logging
from typing import Dict, List, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class DBVetorialAgent:
    """
    Agent responsible for vectorizing the initial Java code


    """

    def __init__(self):
        self.name = "DBVetorialAgent"
    
    async def run(self, task_input: Dict[str, Any]):
        """
            1. Load the Java documents
            2. Segment the documents in chunks
            3. Vectorize the chunks
        """

        try:
            job_id = task_input["job_id"]
            programs = task_input["programs"]
            java_files = task_input["java_files"]

            logger.info(f"[{job_id}] Loading the Java Files to the Vetorial DataBase ")

            java_codes = []
            for java_file in java_files:
                path = java_file["path"]
                java_code = open(path).read()
                java_codes.append(java_code)
            
            separar_arquivos = RecursiveCharacterTextSplitter(
                chunk_size = 2000,
                chunk_overlap = 500,
                lenght_function = len,
                add_start_index = True
            )

            chunks = separar_arquivos.split_documents(java_codes)

            db = Chroma.from_documents(chunks, OpenAIEmbeddings, persist_directory="db")
            
        
        except Exception as e:
            logger.error(f"DBVetorialAgent failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

