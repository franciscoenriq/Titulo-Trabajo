import asyncio
from agentscope.pipeline import MsgHub
from agentscope.message import Msg
from agentscope.token import OpenAITokenCounter
from utils.groupchat_utils import *
from .factory_agents import ReActAgentFactory

DEFAULT_TOPIC = """
    Esta es una sala de conversación entre usuarios humanos sobre temas éticos, ustedes como agentes tienen la finalidad de detectar baja calidad argumentativa , 
    saber cuando hay que intervenir y saber que decir. Dependiendo de sus roles asignados.  
    Serán avisados cuando un participante entra o salga de a la sala.
    """
SYS_PROMPT = """
    Tu puedes designar a un miembro para responder a tu mensaje, debes usar el simbolo @ 
    Esto significa que debes incluir el simbolo @ seguido del nombre de la persona y 
    dejar un espacio luego de colocar el nombre. 
    Todos los participantes son: {nombre_Agentes}.
    El mensaje del usuario se les pasará en forma de broadcast a todos los agentes

    El tema que se discutirá en esta sesion es el siguiente:
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
        self.initialState = None
        self.token_counter = OpenAITokenCounter(model_name="gpt-4o-mini")

    async def start_session(self, tema_sala:str) -> None:
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
            ) + tema_sala
        )
        self.hub = await MsgHub(participants=self.agentes,announcement=hint).__aenter__()

    async def stop_session(self) -> None:
        """
        Cierra el MsgHub cuando termina la sesión de chat.
        """
        tokens_totales = await self.contar_tokens_memoria()
        print(tokens_totales)
        if self.hub:
            await self.hub.__aexit__(None, None, None)
            self.hub = None

    async def analizar_argumento_cascada(self,mensajes:list[Msg]) -> list[dict]:
        if not self.hub: 
            raise RuntimeError("La sesión de chat no ha sido iniciada. Llama a start_session primero.")
        
        for msg_data in mensajes:
            msg = Msg(msg_data["userName"], msg_data["content"], "user")
            await self.hub.broadcast(msg)  # Broadcast al hub

        curador_msg = await self.agenteEntrada()
        next_agent = filter_agents(curador_msg.content, self.agentes)

        respuestas = [{
            "agente":"Curador",
            "respuesta":curador_msg.content
        }]
        if next_agent and next_agent[0].name == "Orientador":
            print("habla el orientador")
            orientador_msg = await self.agenteRespuesta()
            respuestas.append({
                "agente":"Orientador",
                "respuesta":orientador_msg.content
            })
        return respuestas
   

    async def anunciar_entrada_participante(self,userName:str) -> None:
        """
        Funcion que avisa al Hub cuando entra un participante a la sala.
        Así el sistema tiene conciencia de cuantos participantes hay conversando acerca del tema en cuestión.
        """
        prompt = "Ha entrado a la sala el participante llamado: " + userName
        msgSystem = Msg("system",prompt,"system")
        await self.hub.broadcast(msgSystem)

    async def anunciar_salida_participante(self,userName:str) -> None:
        """
        Funcion que avisa al Hub cuando sale un participante a la sala.
        """
        prompt = "Ha salido de la sala el participante llamado: " + userName
        msgSystem = Msg("system",prompt,"system")
        await self.hub.broadcast(msgSystem)

    async def show_memory(self) -> dict:
        """
        Retorna la memoria de los agentes
        """
        memoria_total = {}
        for agente in self.agentes:
            memoria_agente = []
            mensajes_historial = await agente.memory.get_memory() 
            for msg in mensajes_historial:
                memoria_agente.append(msg.get_text_content())
            memoria_total[agente.name] = memoria_agente
        return memoria_total
    
    
    async def contar_tokens_memoria(self) -> dict:
        """
        Retorna el conteo de tokens por cada agente en base a su memoria.
        """
        tokens_total = {}

        for agente in self.agentes:
            mensajes_historial = await agente.memory.get_memory()
            mensajes_convertidos = [
                {"role": msg.role, "content": msg.get_text_content()} 
                for msg in mensajes_historial
            ]
            n_tokens = await self.token_counter.count(mensajes_convertidos)
            tokens_total[agente.name] = n_tokens

        return tokens_total
