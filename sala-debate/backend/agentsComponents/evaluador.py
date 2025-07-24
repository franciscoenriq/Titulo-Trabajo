# ia_module.py
from agentscope import init
from agentscope.agents import DictDialogAgent
from agentscope.parsers import MarkdownJsonDictParser
from agentscope.message import Msg
from agentscope.exception import JsonParsingError
from agentscope.msghub import msghub
from openai import RateLimitError
import os
import ast
import time 
import json 
base_dir = os.path.dirname(os.path.abspath(__file__))
model_config_path = os.path.join(base_dir, "configs", "model_configs.json")

init(
    model_configs=model_config_path,
    project="prueba cde calidad"
)

DEFAULT_TOPIC = """Estás observando una discusión en grupo entre estudiantes sobre el siguiente tema. 
    Tu tarea será evaluar la calidad argumentativa de los mensajes que envían, 
    prestando especial atención a la claridad, lógica y evidencia. 
    Solo deberás intervenir si detectas baja calidad argumentativa en el mensaje más reciente.
    Tema de discusión: """



charles = DictDialogAgent(
    name="Charles",
    model_config_name="gpt-3.5-turbo",
    sys_prompt=(
        "Eres un analista experto en detectar baja calidad argumentativa. "
        "Evalúas mensajes en busca de falta de lógica, evidencia o claridad. "
        "Debes responder solo si detectas baja calidad en el mensaje reciente.\n"
        "Tu respuesta debe ser un JSON plano, sin etiquetas de markdown como ```json o comillas triples.\n"
        "Debe tener exactamente esta estructura:\n"
        "{"
        "\"evaluacion\": \"breve juicio de calidad del argumento\", "
        "\"respuesta\": \"respuesta si hay baja calidad, o string vacío si no hay intervención\", "
        "\"intervencion\": true o false (booleano sin comillas)"
        "}\n"
        "No expliques el formato. No devuelvas texto fuera del JSON."
    )
)

parser1 = MarkdownJsonDictParser(
    content_hint={
        "evaluacion": "breve juicio de calidad del argumento",
        "respuesta": "respuesta si hay baja calidad, responde un string vacio "" en caso que no debas intervenir",
        "intervencion": "true si decides intervenir, false en caso contrario (tipo booleano)"
    },
    keys_to_metadata="intervencion",
    required_keys=["evaluacion","respuesta", "intervencion"],
)
charles.set_parser(parser1)

# Almacena historial
historiales = {}
conversaciones = {}
def inicializar_conversacion(room,prompt_inicial):
    if room in conversaciones:
        return #ya fue inicializado 
    
    hint = Msg(
        name="Host",
        content=DEFAULT_TOPIC + prompt_inicial,
        role="assistant"
    )

    conversaciones[room] = msghub([charles], announcement=hint)
    conversaciones[room].__enter__()  # Inicia manualmente el contexto
    historiales[room] = []

def cerrar_conversacion(room):
    if room in conversaciones:
        conversaciones[room].__exit__(None, None, None)
        del conversaciones[room]
        del historiales[room]


def analizar_argumento(room, user_input, user_name):

    if room not in historiales or room not in conversaciones:
        raise ValueError(f"La conversación para la sala {room} no ha sido inicializada.")


    msg = Msg(user_name, user_input, "user")
    historiales[room].append(msg)

    intentos = 0 
    max_reintentos = 2

    while intentos < max_reintentos:
        try: 
            respuesta = charles(historiales[room])
            parsed = ast.literal_eval(respuesta.content)
            #parsed = json.loads(respuesta.content)
            return {
                "evaluacion": parsed["evaluacion"],
                "respuesta": parsed["respuesta"],
                "intervencion": respuesta.metadata,
                "agente": "Agente",
                "evaluado": user_name 
            }
        except (ValueError, SyntaxError, KeyError, JsonParsingError) as e:
            intentos += 1
            print(f"[Error de parseo - intento {intentos }]:", e)
            print("Contenido recibido:", respuesta.content if respuesta else "No disponible")
            time.sleep(0.2)  # evitar saturar con múltiples llamadas seguidas
        except RateLimitError:
            print("ERROR: Límite de uso de la API de OpenAI excedido.")
            return {
                "evaluacion": "Error",
                "respuesta": "Se ha excedido el límite de uso de la API. Intenta más tarde o revisa tu cuenta.",
                "intervencion": None,
                "agente": "Agente",
                "evaluado": user_name
            }

    # Si después de los reintentos aún falla
    return {
        "evaluacion": "Error al analizar el argumento.",
        "respuesta": "No se pudo evaluar correctamente el mensaje. Intenta reformularlo.",
        "intervencion": False,
        "agente": "Agente",
        "evaluado": user_name
    }