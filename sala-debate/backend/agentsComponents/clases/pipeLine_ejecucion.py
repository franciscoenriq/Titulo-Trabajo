import asyncio
from agentscope.pipeline import MsgHub
from agentscope.message import Msg
from utils.groupchat_utils import *
from .factory_agents import ReActAgentFactory

DEFAULT_TOPIC = """
    Esta es una sala de conversación entre usuarios humanos, ustedes como agentes tienen la finalidad de detectar baja calidad argumentativa , 
    saber cuando hay que intervenir y saber que decir. Dependiendo de sus roles asignados.  
    """
SYS_PROMPT = """
    Tu puedes designar a un miembro para responder a tu mensaje, debes usar el simbolo @ 
    Esto significa que debes incluir el simbolo @ seguido del nombre de la persona y 
    dejar un espacio luego de colocar el nombre. 
    Todos los participantes son: {nombre_Agentes}.
    El mensaje del usuario se les pasará en forma de broadcast a todos los agentes
    """
class CascadaPipeline:
    def __init__(self, 
                 factory: ReActAgentFactory,
                 promt_agenteEntrada:str,
                 promt_agenteRespuesta:str):
        
        self.factory = factory
        self.promt_agenteEntrada = promt_agenteEntrada
        self.promt_agenteRespuesta = promt_agenteRespuesta
        #Creamos los agentes de la arquitectura
        self.agenteEntrada = self.factory.create_agent(
            name="Curador",
            sys_prompt=self.promt_agenteEntrada
        )
        self.agenteRespuesta = self.factory.create_agent(
            name="Orientador",
            sys_prompt=self.promt_agenteRespuesta
        )
        self.agentes = list([self.agenteEntrada, self.agenteRespuesta])
        self.hub = None #inicializamos el hub cuando entramos a una sala. 


    async def start_session(self) -> None:
        """
        Inicializa el msghub con el cual se va a trabajar en una sesion de discusion
        @Hint: mensaje con el cual se inicializan los agentes.
        """
        hint = Msg(
            name="Host",
            role="system",
            content=DEFAULT_TOPIC
            +SYS_PROMPT.format(
                nombre_Agentes=[agent.name for agent in self.agentes]
            )
        )
        self.hub = await MsgHub(participants=self.agentes,announcement=hint).__aenter__()
        

    async def stop_session(self) -> None:
        """
        Cierra el MsgHub cuando termina la sesión de chat.
        """
        if self.hub:
            await self.hub.__aexit__(None, None, None)
            self.hub = None

    async def analizar_argumento_cascada(self,user_input:str, user_name:str) -> dict:
        if not self.hub: 
            raise RuntimeError("La sesión de chat no ha sido iniciada. Llama a start_session primero.")
        
        msg = Msg(user_name, user_input, "user")
        await self.hub.broadcast(msg)  # Broadcast al hub

        curador_msg = await self.agenteEntrada()
        next_agent = filter_agents(curador_msg.content, self.agentes)
        if next_agent and next_agent[0].name == "Orientador":
            print("habla el orientador")
            orientador_msg = await self.agenteRespuesta()
            return {
                "evaluacion": "termino de la intervencion",
                "respuesta": orientador_msg.content,
                "agente": "orientador",
                "evaluado": user_name,
                "intervencion":True
            }
        else: 
            print("se termina el asuntoo")
            return {
                "evaluacion": "Evaluación Orientador",
                "respuesta": curador_msg.content,
                "agente": "Orientador",
                "evaluado": user_name,
                "intervencion":False
                
            }
        

    async def show_memory(self) -> dict:
        """
        retornamos la memoria de los agentes
        """
        memoria_total = {}
        for agente in self.agentes:
            memoria_agente = []
            mensajes_historial = await agente.memory.get_memory() 
            for msg in mensajes_historial:
                memoria_agente.append(msg.get_text_content())
            memoria_total[agente.name] = memoria_agente
        return memoria_total