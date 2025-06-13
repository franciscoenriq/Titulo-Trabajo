import os
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from dotenv import load_dotenv

load_dotenv()  # Carga la API Key desde .env

openai_api_key = os.getenv("API_KEY")
if not openai_api_key:
    raise ValueError("API_KEY no encontrada en el archivo .env")

chat = ChatOpenAI(
    model_name="gpt-4o",  
    openai_api_key=openai_api_key,
    temperature=0.7
)

def get_chat_response(user_input):
    messages = [HumanMessage(content=user_input)]
    response = chat(messages)
    return response.content
