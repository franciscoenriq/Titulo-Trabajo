from agentscope import init
from agentscope.agents import DictDialogAgent
from agentscope.parsers import MarkdownJsonDictParser
from agentscope.message import Msg
from agentscope.msghub import msghub
import os 
import json  
import ast    
#ruta absoluta en donde esta el script.
base_dir = os.path.dirname(os.path.abspath(__file__))
model_config_path = os.path.join(base_dir,"configs","model_configs.json")

DEFAULT_TOPIC = """
En este chat se va discutir acerca de la bicicleta y por que deberia popularizarse más para combatir el cambio climatico.
"""


init(
    model_configs=model_config_path,
    project="prueba cde calidad"
    )

# Cargar el prompt inicial desde un archivo en la carpeta 'prompt'
prompt_path = os.path.join(base_dir, "prompt", "prompt_v2.txt")
with open(prompt_path, "r", encoding="utf-8") as f:
    prompt_inicial = f.read()

charles = DictDialogAgent(
    name = "Charles",
    model_config_name = "openai_chat_gpt-4o",
    sys_prompt=prompt_inicial
)

parser1 = MarkdownJsonDictParser(
    content_hint={
        "evaluacion":"breve juicio de calidad del argumento",
        "respuesta":"espuesta opcional si hay baja calidad",
        "intervencion":"true si decides intervenir, false en caso contrario (tipo booleano)"
    },
    keys_to_metadata="intervencion",
    required_keys=["evaluacion","intervencion"],
)
charles.set_parser(parser1)

hint = Msg(
    name="Host",
    content=DEFAULT_TOPIC,
    role="assistant",
)
agents = [charles]

# Historial de mensajes
historial = []

# Bucle de entrada del humano
print("Inicio del análisis. Escribe tus argumentos uno a uno (Ctrl+C para salir).")
try:
    with msghub(agents,announcement=hint):
        while True:
            user_input = input(" Humano: ")
            msg = Msg("Estudiante", user_input, "user")
            historial.append(msg)

            # El agente analiza todo el historial
            respuesta = charles(historial)
            print(respuesta.metadata)
            print(type(respuesta.metadata))
            try:
                parsed = ast.literal_eval(respuesta.content)
                print("Evaluación:", parsed["evaluacion"])
                print(respuesta)
                if respuesta.metadata is False: 
                    print("no se evalua aun")
            except (ValueError, SyntaxError) as e:
                print("Error al parsear la respuesta del modelo:")
                print(e)
                print("Contenido recibido:", respuesta.content)
            except KeyError as e:
                print("Falta una clave esperada en la respuesta parseada:")
                print(e)
                print("Contenido parseado:", parsed if 'parsed' in locals() else 'No disponible')
except KeyboardInterrupt:
    print("\nSesión finalizada.")