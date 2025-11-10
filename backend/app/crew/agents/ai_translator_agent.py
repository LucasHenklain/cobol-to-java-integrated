import logging
from typing import Dict, List, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts.chat import ChatPromptTemplate 
from dotenv import load_dotenv
from langchain_openai.chat_models.base import ChatOpenAI

load_dotenv()
logger = logging.getLogger(__name__)

class AITranslatorAgent:

    def __init__(self):
        self.name = "AITranslatorAgent"
    
    async def run(self, task_input: Dict[str, Any]):
        """
        Improves the translations using RAG to refactor the Java files
        """
        Caminho_DB = "db"

        try:

            job_id = task_input["job_id"]
            programs = task_input["programs"]
            java_files = task_input["java_files"]
            
            logger.info(f"[{job_id}] Using RAG to improve the Translated Files")

            for file in java_files:
                path = file["path"]
                java_code = open(path).read()

                prompt_template = """
                You are an experienced cobol and java developer working on the migration of legacy systems.

                Improve this java file fixing inconsistencies and the communication of the scripts:
                {file}

                Based on the other files of the repository:
                {base_conhecimento}

                RETURN ONLY THE JAVA CODE. DO NOT ANSWER ANY QUESTIONS OR RETURN ANYTHING THAT'S NOT A JAVA CODE.
                If you dont find any inconsistencies, improve the code and the communication without changing too much of the code.
                """

                def busca_db():
                    request_db = f"""
                    Wich segments of code communicate with this java file or have similar logic that needs to change this file for fixing and improving the comunication of the java files?
                    What are the more important parts to be changed on the following java file?

                    {java_code}
                    """

                    funcao_embedding = OpenAIEmbeddings()

                    db = Chroma(persist_directory=Caminho_DB, embedding_function=funcao_embedding)

                    resultados = db.similarity_search_with_relevance_scores(request_db, k=3)

                    if len(resultados) == 0 or resultados[0][1] < 0.7:
                        return
                    
                    textos_resultado = []
                    for resultado in resultados:
                        trecho = resultado[0].page_content
                        textos_resultado.append(trecho)
                    
                    base_conhecimento = "\n\n----\n\n".join(textos_resultado)

                    prompt = ChatPromptTemplate.from_template(prompt_template)
                    prompt = prompt.invoke({"java_file": java_code, "base_conhecimento": base_conhecimento})

                    modelo = ChatOpenAI() 
                    texto_resposta = modelo.invoke(prompt).content

                    with open(path, 'w') as f:
                        f.write(texto_resposta)

                busca_db()

        except Exception as e:
            logger.error(f"DBVetorialAgent failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }