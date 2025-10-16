import uuid
from pydantic import BaseModel, Field, conint
from typing import Literal
from .factory_agents import ReActAgentFactory
from agentscope.message import Msg
from agentscope.pipeline import MsgHub, fanout_pipeline
from utils.groupchat_utils import *
import json
DEFAULT_TOPIC = """
    Esta es una sala de conversación entre usuarios humanos sobre temas éticos, ustedes como agentes tienen la finalidad de detectar baja calidad argumentativa, mediante
    la tarea que se les asignó.
    El tema que las personas humanas van a discutir es:
    """

class PuntuacionModel(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Un número entero entre 0 y 100")
    diagnostico: str = Field(..., description="Breve explicación (15 palabras maximo) del score")

class ClasificacionModel(BaseModel):
    patrones_detectados: list[str] = Field(
        default_factory=list,
        description="Lista de patrones de baja calidad detectados en el mensaje"
    )

class EvaluacionMensaje(BaseModel):
    id: str = Field(..., description="Identificador único del mensaje evaluado")
    usuario: str = Field(..., description="Nombre del usuario que envió el mensaje")
    mensaje: str = Field(..., description="Contenido textual enviado por el usuario")
    clasificador: ClasificacionModel
    puntuador: PuntuacionModel

class Pipeline:
    def __init__(self,factory: ReActAgentFactory,
                 prompt_agentePuntuador:str,
                 prompt_agenteClasificador:str,
                 prompt_agenteCurador:str,
                 promt_agenteOrientador:str
                 ):
        
        self.agentePuntuador = factory.create_agent(
            name="Puntuador",
            sys_prompt=prompt_agentePuntuador
        )
        self.agenteClasificador = factory.create_agent(
            name="Clasificador",
            sys_prompt=prompt_agenteClasificador
        )
        self.agenteCurador = factory.create_agent(
            name="Curador",
            sys_prompt=prompt_agenteCurador
        )
        self.agenteOrientador = factory.create_agent(
            name="Orientador",
            sys_prompt=promt_agenteOrientador
        )
        self.agentes = list([self.agentePuntuador, self.agenteClasificador,self.agenteCurador,self.agenteOrientador])
        self.hub = None
        self.msg_id = 0
        self.avisos_timer = 0


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
            + tema_sala
        )
        self.hub = True
        for agent in self.agentes:
            await agent.observe(hint)

    async def stop_session(self) -> None:
        """
        Cierra el MsgHub cuando termina la sesión de chat.
        """
        #tokens_totales = await self.contar_tokens_memoria()
        #print(f"se usaron:{tokens_totales} tokens")
        if self.hub:
            self.hub = False
        memoria = await self.show_memory()
        print(memoria)


    async def anunciar_entrada_participante(self,userName:str) -> None:
        """
        Funcion que avisa al Hub cuando entra un participante a la sala.
        Así el sistema tiene conciencia de cuantos participantes hay conversando acerca del tema en cuestión.
        """
        prompt = "Ha entrado a la sala el participante llamado: " + userName
        msgSystem = Msg("system",prompt,"system")
        for agent in self.agentes:
            await agent.observe(msgSystem)

    async def anunciar_salida_participante(self,userName:str) -> None:
        """
        Funcion que avisa al Hub cuando sale un participante a la sala.
        """
        prompt = "Ha salido de la sala el participante llamado: " + userName
        msgSystem = Msg("system",prompt,"system")
        for agent in self.agentes:
            await agent.observe(msgSystem)

    async def avisar_tiempo(self, fase_actual, remaining_phase, elapsed_phase, remaining_total, elapsed_total):
        
        mensaje = f"""
        Fase_actual:{fase_actual}:
        tiempo_transcurrido_fase:{elapsed_phase//60} minutos y {elapsed_phase%60} segundos,
        tiempo_restante_fase:{remaining_phase//60} minutos y {remaining_phase%60} segundos,
        tiempo_total_transcurrido:{elapsed_total//60} minutos y {elapsed_total%60} segundos,
        tiempo_total_restante:{remaining_total//60} minutos y {remaining_total%60} segundos.
        """
        print(mensaje)
        msg = Msg("Timer",mensaje,"system")
        if self.avisos_timer == 0:
            print("primer timer no se usa")
            for agente in self.agentes:
                await agente.observe(msg)
            self.avisos_timer = 1
            return
        print("ya no es el primer aviso")
        msg = Msg("Timer",mensaje,"assistant")
        for agent in self.agentes:
            await agent.observe(msg)
        
        respuesta_puntuador = await self.agentePuntuador()
        await self.agenteCurador.observe(respuesta_puntuador)
        await self.agenteOrientador.observe(respuesta_puntuador)
        puntuacion = PuntuacionModel.model_validate_json(respuesta_puntuador.content)
        return {
              "score":puntuacion.score,
              "diagnostico":puntuacion.diagnostico
          }

    async def analizar_mensaje(self,userName:str,mensage:str):
        msg = Msg(userName,mensage,"user")
        respuestas = await fanout_pipeline(
        agents=[self.agenteClasificador,self.agentePuntuador],
        msg=msg,
        enable_gather=True,
        )

        await self.agenteOrientador.observe(msg)

        clasificacion = None
        puntuacion = None

        for r in respuestas:
            if r.name == "Puntuador":
                puntuacion = PuntuacionModel.model_validate_json(r.content)
                
            elif r.name == "Clasificador":  
                clasificacion = ClasificacionModel.model_validate_json(r.content)
                msg_clasificacion = Msg(
                    "Clasificador",
                    json.dumps({
                        "id_mensaje":str(self.msg_id),
                        "nombreUsuario":userName,
                        "mensaje_original": mensage,
                        "clasificacion": clasificacion.model_dump()
                    }, ensure_ascii=False, indent=2),
                    "assistant"
                )
                await self.agentePuntuador.observe(msg_clasificacion)

        if clasificacion and puntuacion:
          evaluacion = EvaluacionMensaje(
              id=str(self.msg_id),
              usuario=userName,
              mensaje=mensage,
              clasificador=clasificacion,
              puntuador=puntuacion,
          )
          evaluacion_msg = Msg(
              name="SistemaEvaluador",
              role="system",
              content=evaluacion.model_dump_json(indent=2) 
          )
          await self.agenteCurador.observe(evaluacion_msg)
          self.msg_id += 1

          return {
              "usuario":userName,
              "mensaje":mensage,
              "score":puntuacion.score,
              "diagnostico":puntuacion.diagnostico
          }



    async def analizar_argumento_cascada(self):
        if not self.hub or self.hub == False: 
            raise RuntimeError("La sesión de chat no ha sido iniciada. Llama a start_session primero.")
        
        curador_msg = await self.agenteCurador()
        await self.agenteOrientador.observe(curador_msg)
        await self.agentePuntuador.observe(curador_msg)
        next_agent = filter_agents(curador_msg.content, self.agentes)

        respuestas = [{
            "agente":"Curador",
            "respuesta":curador_msg.content
        }]
        if next_agent and next_agent[0].name == "Orientador":
            orientador_msg = await self.agenteOrientador()
            await self.agentePuntuador.observe(orientador_msg)
            await self.agenteCurador.observe(orientador_msg)
            
            respuestas.append({
                "agente":"Orientador",
                "respuesta":orientador_msg.content
            })
        return respuestas

    async def show_memory(self) -> dict:
      """
    Retorna la memoria de los agentes como texto legible
    """
      def serialize_msg_content(content):
        if isinstance(content, str):
            return content
        elif isinstance(content, BaseModel):
            return content.model_dump_json(indent=2)
        elif isinstance(content, Msg):
            # Extraemos el contenido real del Msg
            if isinstance(content.content, list):
                # Si es una lista de tool_use/tool_result, extraemos solo el texto
                texts = []
                for block in content.content:
                    if isinstance(block, dict):
                        if block.get("type") == "tool_use":
                            response = block.get("input", {}).get("response")
                            if response:
                                texts.append(response)
                        elif block.get("type") == "tool_result":
                            output_blocks = block.get("output", [])
                            for ob in output_blocks:
                                if ob.get("type") == "text":
                                    texts.append(ob.get("text"))
                return "\n".join(texts)
            else:
                return serialize_msg_content(content.content)
        else:
            return str(content)


      memoria_total = {}
      for agente in self.agentes:
          memoria_agente = []
          mensajes_historial = await agente.memory.get_memory() 
          for msg in mensajes_historial:
              memoria_agente.append(serialize_msg_content(msg))
          memoria_total[agente.name] = memoria_agente
      return memoria_total


    async def reactiveResponse(self,usuario:str,mensaje:str):
        msgUsuario = Msg(usuario,mensaje,"user")
        respuesta = await self.agenteOrientador(msgUsuario)
        await self.agentePuntuador.observe(msgUsuario)
        await self.agentePuntuador.observe(respuesta)
        await self.agenteCurador.observe(msgUsuario)
        await self.agenteCurador.observe(respuesta)
        return [{
            "agente":"Orientador",
            "respuesta":respuesta.content
        }]
    
    
    async def timerResponse(self,puntacion:int):
        msgSystem = f"El puntuador a puntuado muy baja la conversacion con {puntacion} puntos debido a inactividad en la sala. Por tanto debes intervenir "
        msg = Msg("system",msgSystem,"system")
        respuesta = await self.agenteOrientador(msg)
        return [{
            "agente":"Orientador",
            "respuesta":respuesta.content
        }]
