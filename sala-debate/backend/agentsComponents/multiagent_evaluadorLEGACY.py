# -*- coding: utf-8 -*-
""" A group chat where user can talk any time implemented by agentscope. """
'''

from utils.groupchat_utils import * 
import agentscope
import os 
import time
from agentscope.agents import UserAgent
from agentscope.message import Msg
from agentscope.msghub import msghub
from agentscope.exception import JsonParsingError
from openai import RateLimitError
import json 
USER_TIME_TO_SPEAK = 10
DEFAULT_TOPIC = """
Esta es una sala de conversación entre usuarios humanos, ustedes como agentes tienen la finalidad de detectar baja calidad argumentativa , 
saber cuando hay que intervenir y saber que decir. Dependiendo de sus roles asignados.  
"""

SYS_PROMPT = """
Tu puedes designar a un miembro para responder a tu mensaje, debes usar el simbolo @ 
Esto significa que debes incluir el simbolo @ seguido del nombre de la persona y 
dejar un espacio luego de colocar el nombre. 
Todos los participantes son: {agent_names}
El tema a discutir en la sala es el siguiente:
"""
base_dir = os.path.dirname(os.path.abspath(__file__))
model_config_path = os.path.join(base_dir, "configs", "model_configs.json")
agent_config_path = os.path.join(base_dir, "configs", "agent_configs.json")

"""group chat"""
npc_agents = agentscope.init(
    model_configs=model_config_path,
    agent_configs=agent_config_path,
)

agents = list(npc_agents) 


def inicializar_conversacion_cascada(room, promt_inicial):
    if room in conversaciones:
        return
    hint = Msg(
        name="Host",
        content=DEFAULT_TOPIC
        + SYS_PROMPT.format(
            agent_names=[agent.name for agent in agents],
        ) + promt_inicial,
        role="assistant",
    )
    conversaciones[room] = msghub(agents, announcement=hint)
    conversaciones[room].__enter__()  # Inicia manualmente el contexto
    historiales[room] = []

def analizar_argumento_cascada(room,user_input,user_name):
    if room not in historiales or room not in conversaciones:
        raise ValueError(f"La conversación para la sala {room} no ha sido inicializada.")

    msg = Msg(user_name, user_input, "user")
    historiales[room].append(msg)

    intentos = 0 
    max_reintentos = 2

    while intentos < max_reintentos:
        try: 
            # A1 responde
            curador = npc_agents[0]
            curador_msg = curador(msg)
            # Detectamos si el Orientador fue mencionado por el Curador
            next_agents = filter_agents(curador_msg.content, npc_agents)

            if next_agents and next_agents[0].name == "Orientador":
                print("Orientador fue mencionado")
                Orientador = next_agents[0]
                orientador_msg = Orientador()  # A2 responde
                # Verificamos si A3 fue mencionado por A2
                next_agents = filter_agents(orientador_msg.content, npc_agents)
                if next_agents and next_agents[0].name == "a3":
                    print("agente 3 fue mencionado")
                    a3 = next_agents[0]
                    #a3_msg = a3()  # A3 responde
                return {
                    "evaluacion": "Evaluación Final (Orientador)",
                    "respuesta": orientador_msg.content.replace("@a3",""),
                    "intervencion": True,
                    "agente": orientador_msg.name,
                    "evaluado": user_name
                }

            else:
                return {
                    "evaluacion": "Evaluación Inicial (Curador)",
                    "respuesta": curador_msg.content,
                    "intervencion": False,
                    "agente": curador_msg.name,
                    "evaluado": user_name
                }
        except (ValueError, SyntaxError, KeyError, JsonParsingError) as e:
            intentos += 1
            print(f"[Error de parseo - intento {intentos }]:", e)
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


def llamar_relator(room,user_input,user_name):
    """
    El relator es el encargado de resumir la conversasion, si es llamado entonces se ejecuta. 
    """
    if room not in historiales or room not in conversaciones:
        raise ValueError(f"La conversación para la sala {room} no ha sido inicializada.")

    next_agents = filter_agents(user_input, npc_agents)
    if next_agents and next_agents[0].name == "Relator":
        print("El relator fue llamado")
        Relator = next_agents[0]
        Relator_msg = Relator()  #El relator resume 
        return {
                "evaluacion": "Evaluación Final (A2)",
                "respuesta": (Relator_msg.content).replace("@a3",""),
                "intervencion": False,
                "agente": Relator_msg.name,
                "evaluado": user_name
                }

'''