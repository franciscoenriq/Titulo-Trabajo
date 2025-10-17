from pydantic import BaseModel, Field, conint
from typing import Literal
from .factory_agents import ReActAgentFactory
from agentscope.message import Msg
from agentscope.pipeline import MsgHub, fanout_pipeline
from utils.groupchat_utils import *
import json
DEFAULT_TOPIC = """
    El tema que los estudiantes discutirán es el siguiente:
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
        Resetea variables que se usan durante una sesión.
        """
        #tokens_totales = await self.contar_tokens_memoria()
        #print(f"se usaron:{tokens_totales} tokens")
        if self.hub:
            self.hub = False
        memoria = await self.show_memory()
        self.msg_id = 0
        self.avisos_timer=0
        print(memoria)


    async def anunciar_entrada_participante(self,userName:str) -> None:
        """
        Funcion que avisa al Hub cuando entra un participante a la sala.
        Así el sistema tiene conciencia de cuantos participantes hay conversando acerca del tema en cuestión.
        """
        prompt = "Ha entrado a la sala el participante llamado: " + userName
        msgSystem = Msg(name="host",
                        role="system",
                        content=prompt)
        for agent in self.agentes:
            await agent.observe(msgSystem)

    async def anunciar_salida_participante(self,userName:str) -> None:
        """
        Funcion que avisa al Hub cuando sale un participante a la sala.
        """
        prompt = "Ha salido de la sala el participante llamado: " + userName
        msgSystem = Msg(name="host",
                        role="system",
                        content=prompt)
        for agent in self.agentes:
            await agent.observe(msgSystem)

    async def avisar_tiempo(self, fase_actual, remaining_phase, elapsed_phase, remaining_total, elapsed_total):
        """
        Funcion que se ejecuta con cada aviso del timer. Se actualiza el tiempo que a transcurrido a todos los agentes. 
        EL primer aviso no le pide la opinion al Puntuador porque recien parte la sala. Luego de eso sí lo hace.
        """
        mensaje = f"""
        Fase_actual:{fase_actual}
        tiempo_transcurrido_fase:{elapsed_phase//60} minutos y {elapsed_phase%60} segundos,
        tiempo_restante_fase:{remaining_phase//60} minutos y {remaining_phase%60} segundos,
        tiempo_total_transcurrido:{elapsed_total//60} minutos y {elapsed_total%60} segundos,
        tiempo_total_restante:{remaining_total//60} minutos y {remaining_total%60} segundos.
        """
        print(mensaje)
        msg = Msg(name="Timer",
                  role="system",
                  content=mensaje)
        
        if self.avisos_timer == 0:
            print("primer timer no se usa")
            for agente in self.agentes:
                await agente.observe(msg)
            self.avisos_timer = 1
            return
        print("ya no es el primer aviso")
        for agent in self.agentes:
            await agent.observe(msg)
        
        msg = Msg(name="Host",
                  role="system",
                  content="Debes decidir si es necesario intervenir ahora que tienes la actualizaciond el timer. Básate en los últimos mensajes que han entrado a la sala para decidir.")
        respuesta_puntuador = await self.agentePuntuador(msg)
        await self.agenteCurador.observe(respuesta_puntuador)
        await self.agenteOrientador.observe(respuesta_puntuador)
        puntuacion = PuntuacionModel.model_validate_json(respuesta_puntuador.content)
        return {
              "score":puntuacion.score,
              "diagnostico":puntuacion.diagnostico
          }

    async def analizar_mensaje(self,userName:str,mensage:str):
        """
        Esta funcion de ejecuta cada vez que entra un mensaje a la sala. 
        Analiza un mensaje de usuario con los agentes Clasificador y Puntuador,
        y genera una evaluación estructurada para el Curador.
        """
        msg_usuario = Msg(name=userName,
                          role="user",
                          content=mensage)

        respuestas = await fanout_pipeline(
        agents=[self.agenteClasificador,self.agentePuntuador],
        msg=msg_usuario,
        enable_gather=True,
        )

        clasificacion, puntuacion = None, None

        for r in respuestas:
            if r.name == "Puntuador":
                puntuacion = PuntuacionModel.model_validate_json(r.content)
                
            elif r.name == "Clasificador":  
                clasificacion = ClasificacionModel.model_validate_json(r.content)
                msg_clasificacion = Msg(
                    name="Clasificador",
                    content=json.dumps({
                        "id_mensaje":str(self.msg_id),
                        "nombreUsuario":userName,
                        "mensaje_original": mensage,
                        "clasificacion": clasificacion.model_dump()
                    }, ensure_ascii=False, indent=2),
                    role="assistant"
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

          await self.agenteOrientador.observe(msg_usuario)

          return {
              "usuario":userName,
              "mensaje":mensage,
              "score":puntuacion.score,
              "diagnostico":puntuacion.diagnostico
          }



    async def analizar_argumento_cascada(self):
        """
        Funcion que se ejecuta para pedirle la opinión al Curador si es pertinente o no 
        intervenir en la conversación.
        """
        if not self.hub or self.hub == False: 
            raise RuntimeError("La sesión de chat no ha sido iniciada. Llama a start_session primero.")
        mensaje = """
                    Se a cumplido el tamaño de la ventana, por tanto debes decidir si es necesario intervenir o no.
                  """
        msg = Msg(name="host",
                  role="system",
                  content=mensaje)
        curador_msg = await self.agenteCurador(msg)
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

    async def reactiveResponse(self,usuario:str,mensaje:str):
        """
        Funcion que se ejecuta cuando un participante de la sala llama al agente Orientador.
        """
        msgUsuario = Msg(name=usuario,
                         role="user",
                         content=mensaje)
        for agent in [self.agentePuntuador,self.agenteCurador,self.agenteOrientador]:
            await agent.observe(msgUsuario)
        respuesta = await self.agenteOrientador()
        for agent in [self.agentePuntuador,self.agenteCurador]:
            await agent.observe(respuesta)
        return [{
            "agente":"Orientador",
            "respuesta":respuesta.content
        }]
    
    
    async def timerResponse(self,puntacion:int):
        """
        Funcion que se ejecuta cuando el puntuador puntua muy baja la sala al ingresar un evento de tipo tiempo.
        Se le pregunta al curador si es necesario o no intervenir. 
        """
        msgSystem = f"""El puntuador a puntuado muy baja la conversacion con {puntacion} puntos debido a inactividad en la sala.
        Por tanto debes decidir si es pertinente o no que el agente Orientador intervenga, si decides que intervenga debes llamarlo con @Orientador
        Por ejemplo, si hubo inactividad , llamas al orientador pero despues empezó hacer actividad pero el puntaje es demasiado bajo aun sería pertinente 
        esperar a que se sigan desarronado argumentos. porque la siguiente call del timer será 20 segundos despues de puntuar baja la sala.
        """
        msg = Msg(name="host",
                  role="system",
                  content=msgSystem)
        
        respuesta_curador = await self.agenteCurador(msg)
        for agents in [self.agentePuntuador,self.agenteOrientador]:
            await agents.observe(respuesta_curador)

        respuestas = [{
            "agente":"Curador",
            "respuesta":respuesta_curador.content
        }]

        next_agent = filter_agents(respuesta_curador.content, self.agentes)
        if next_agent and next_agent[0].name == "Orientador":
            respuesta_orientador = await self.agenteOrientador()

            for agent in[self.agentePuntuador,self.agenteCurador]:
                await agent.observe(respuesta_orientador)
            respuestas.append({
                "agente":"Orientador",
                "respuesta":respuesta_orientador.content
            })
            return respuestas
        
    async def lowScoreMessageRespone(self,puntuacion:int):
        """
        Funcion que se ejecuta cuando el puntuador puntua muy baja la sala al ingresar un evento de tipo mensaje.
        osea en base a la respuesta que da en self.agregar_mesaje. 
        Se le pregunta al curador si es necesario o no intervenir. 
        """
        msgSystem = f"""
        El agente Puntuador ha asignado una puntuación muy baja ({puntuacion} puntos) a uno de los mensajes recientes.
        Si consideras que el Orientador debe intervenir para reconducir la conversación, debes mencionarlo con @Orientador.
        En cambio, si piensas que el grupo puede corregirse por sí mismo, puedes optar por no intervenir todavía y no mencionar al orientador.
        """
        
        msg = Msg(name="host",
                  role= "system", 
                  content=msgSystem)
        
        # El Curador decide si el Orientador debe intervenir
        respuesta_curador = await self.agenteCurador(msg)

        # Los demás agentes observan la decisión del Curador
        for agent in [self.agentePuntuador, self.agenteOrientador]:
            await agent.observe(respuesta_curador)

        respuestas = [{
            "agente":"Curador",
            "respuesta":respuesta_curador.content
        }]

        # Verificar si el Curador pidió al Orientador intervenir
        next_agent = filter_agents(respuesta_curador.content, self.agentes)
        if next_agent and next_agent[0].name == "Orientador":
            # Si el Curador llamó al Orientador, este responde
            respuesta_orientador = await self.agenteOrientador()

            # Curador y Puntuador observan la intervención del Orientador
            for agent in [self.agentePuntuador, self.agenteCurador]:
                await agent.observe(respuesta_orientador)
            respuestas.append({
                "agente":"Orientador",
                "respuesta":respuesta_orientador.content
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