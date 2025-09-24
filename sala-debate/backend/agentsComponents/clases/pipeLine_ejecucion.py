import asyncio
from agentscope.pipeline import MsgHub
from agentscope.message import Msg
from agentscope.token import OpenAITokenCounter
from utils.groupchat_utils import *
from .factory_agents import ReActAgentFactory
from agentscope.tool import Toolkit, ToolResponse
from models.models import get_messages_by_room,get_active_room_session_id
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

PROMT_ENRUTADOR = (
    "Eres el Enrutador. SOLO debes responder exactamente una de estas dos opciones:\n\n"
    "1. '@Resumidor' → únicamente si el mensaje contiene de forma explícita:\n"
    "   - la palabra '@Resumidor', o\n"
    "   - frases como 'resumir', 'hazme un resumen', 'ayuda a resumir', dirigidas al agente.\n\n"
    "2. 'paso' → para absolutamente cualquier otro mensaje, aunque hable de temas, qué hacer, etc.\n\n"
    "Reglas adicionales:\n"
    "- Nunca adivines la intención.\n"
    "- Nunca actives al Resumidor por preguntas generales (ej. '¿qué hacemos con este tema?').\n"
    "- Tu salida debe ser exactamente '@Resumidor' o 'paso'. Nada más."
    "No es motivo para activar al resumidor si es que se estan dando argumentos del tema en discusion. SOLO SI TE LO PIDEN POR FAVOR"
)
PROMT_RESUMIDOR = (
    "Eres el agente Resumidor. Tu única tarea es generar un resumen breve y claro "
    "sobre la conversación ética en curso.\n\n"
    "Instrucciones estrictas:\n"
    "- El resumen debe estar escrito en español natural y conciso.\n"
    "- Máximo 30 palabras.\n"
    "- No agregues opiniones propias ni explicaciones.\n"
    "- No repitas información innecesaria.\n"
    "- Si no hay suficiente contenido para resumir, responde exactamente: 'Aún no hay suficiente contenido para resumir.'\n\n"
    "Tu salida debe ser únicamente el resumen final, sin encabezados ni texto adicional."
)


class CascadaPipeline:
    def __init__(self, 
                 factory: ReActAgentFactory,
                 promt_agenteEntrada:str,
                 promt_agenteRespuesta:str):
        self.tema_sala = None
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
        self.agenteEnrutador = self.factory.create_agent(
            name="Enrutador",
            sys_prompt=PROMT_ENRUTADOR
        )
        self.agenteResumidor = self.factory.create_agent(
            name="Resumidor",
            sys_prompt=PROMT_RESUMIDOR
        )
        self.agentes = list([self.agenteEntrada, self.agenteRespuesta,self.agenteEnrutador,self.agenteResumidor])
        self.hub = None #inicializamos el hub cuando entramos a una sala. 
        self.initialState = None
        self.token_counter = OpenAITokenCounter(model_name="gpt-4o-mini")

    async def start_session(self, tema_sala:str) -> None:
        """
        Inicializa el msghub con el cual se va a trabajar en una sesion de discusion
        @Hint: mensaje con el cual se inicializan los agentes.
        """
        self.tema_sala = tema_sala
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

    async def entrar_mensaje_al_hub(self,mensaje:dict):
        msg = Msg(mensaje["userName"], mensaje["content"], "user")
        await self.hub.broadcast(msg)
        enrutador_msg = await self.agenteEnrutador()
        next_agent = filter_agents(enrutador_msg.content,self.agentes)
        if next_agent and next_agent[0].name == "Resumidor":
            resumidor_msg = await self.agenteResumidor()
            respuesta = [{
                "agente":"Resumidor",
                "respuesta": resumidor_msg.content
            }]
            return respuesta
        else:
            return None


    async def analizar_argumento_cascada(self) -> list[dict]:
        if not self.hub: 
            raise RuntimeError("La sesión de chat no ha sido iniciada. Llama a start_session primero.")
        
        curador_msg = await self.agenteEntrada()
        next_agent = filter_agents(curador_msg.content, self.agentes)

        respuestas = [{
            "agente":"Curador",
            "respuesta":curador_msg.content
        }]
        if next_agent and next_agent[0].name == "Orientador":
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
