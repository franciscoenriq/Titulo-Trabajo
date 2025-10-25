import time
from datetime import datetime
from pydantic import BaseModel, Field, conint
from typing import Literal
from .factory_agents import ReActAgentFactory
from agentscope.message import Msg
from agentscope.pipeline import MsgHub, fanout_pipeline
from utils.groupchat_utils import *

DEFAULT_TOPIC = """
    El tema que los estudiantes discutirán es el siguiente:
    """
class PuntuacionModel(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Un número entero entre 0 y 100")
    diagnostico: str = Field(..., description="Breve explicación (15 palabras maximo) del score")

class Pipeline:
    def __init__(self,factory: ReActAgentFactory,
                 prompt_agentePuntuador:str,
                 prompt_agenteCurador:str,
                 promt_agenteOrientador:str
                 ):
        
        self.agentePuntuador = factory.create_agent(
            name="Puntuador",
            sys_prompt=prompt_agentePuntuador
        )
        self.agenteCurador = factory.create_agent(
            name="Curador",
            sys_prompt=prompt_agenteCurador
        )
        self.agenteOrientador = factory.create_agent(
            name="Orientador",
            sys_prompt=promt_agenteOrientador
        )

        self.agentes = list([self.agentePuntuador,self.agenteCurador,self.agenteOrientador])
        self.hub = None
        self.msg_id = 0
        self.avisos_timer = 0


    async def start_session(self, tema_sala:str,usuarios_sala:list) -> None:
        """
        Inicializa el msghub con el cual se va a trabajar en una sesion de discusion
        @Hint: mensaje con el cual se inicializan los agentes.
        """
        if(len(usuarios_sala) > 0):
            participantes_text = ""
            participantes_text = "\n".join(f"- {u}" for u in usuarios_sala)
        participantes = f"""
        En esta sesion hay ({len(usuarios_sala)}) usuarios.
        Los participantes en la discusión son los siguientes:
        {participantes_text}
        """

        self.tema_sala = tema_sala
        hint = Msg(
            name="Host",
            role="system",
            content=DEFAULT_TOPIC
            + tema_sala + participantes
        )
        self.hub = await MsgHub(participants=self.agentes,announcement=hint).__aenter__()

    async def stop_session(self) -> None:
        """
        Cierra el MsgHub cuando termina la sesión de chat.
        """
        #tokens_totales = await self.contar_tokens_memoria()
        #print(tokens_totales)
        if self.hub:
            await self.hub.__aexit__(None, None, None)
            self.hub = None
        memoria = await self.show_memory()
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
        await self.hub.broadcast(msgSystem)

    async def anunciar_salida_participante(self,userName:str) -> None:
        """
        Funcion que avisa al Hub cuando sale un participante a la sala.
        """
        prompt = "Ha salido de la sala el participante llamado: " + userName
        msgSystem = Msg(name="host",
                        role="system",
                        content=prompt)
        await self.hub.broadcast(msgSystem)

    async def entrar_mensaje_a_la_sala(self,username:str,mensaje:str):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        mensaje_formateado = (
        f" Mensaje enviado por {username} a las {now}:\n"
        f'{{"contenido": "{mensaje}"}}'
        )

        msg = Msg(name=username,
                  role='user',
                  content=mensaje_formateado)
        
        await self.hub.broadcast(msg)

        respuesta_puntuador = await self.agentePuntuador()
        puntuacion = PuntuacionModel.model_validate_json(respuesta_puntuador.content)

        return {
            "usuario":username,
            "mensaje":mensaje,
            "score":puntuacion.score,
            "diagnostico":puntuacion.diagnostico
        }
    
    async def avisar_tiempo(self, fase_actual, remaining_phase, elapsed_phase, remaining_total, elapsed_total):
        """
        Envía un aviso de tiempo legible para los agentes, informando cuánto ha transcurrido y cuánto queda
        tanto en la fase actual como en la sesión total. En el primer aviso solo informa; en los siguientes,
        también solicita al Puntuador una evaluación.
        """
        def formato_tiempo(segundos: int) -> str:
            minutos = segundos // 60
            segs = segundos % 60
            partes = []
            if minutos > 0:
                partes.append(f"{minutos} minuto{'s' if minutos != 1 else ''}")
            if segs > 0:
                partes.append(f"{segs} segundo{'s' if segs != 1 else ''}")
            return " y ".join(partes) if partes else "0 segundos"

        mensaje_tiempo = (
            f"**Actualización del tiempo**\n"
            f"- Fase actual: {fase_actual}\n"
            f"- Tiempo transcurrido en la fase: {formato_tiempo(elapsed_phase)}\n"
            f"- Tiempo restante en la fase: {formato_tiempo(remaining_phase)}\n"
            f"- Tiempo total transcurrido: {formato_tiempo(elapsed_total)}\n"
            f"- Tiempo total restante: {formato_tiempo(remaining_total)}\n\n"
            f"Por favor, tengan en cuenta este avance temporal para sus decisiones y evaluaciones."
        )

        print(mensaje_tiempo)

        msg_tiempo = Msg(
            name="Timer",
            role="system",
            content=mensaje_tiempo
        )

        # Primer aviso solo informa
        if self.avisos_timer == 0:
            print("Primer aviso del timer: solo se informa el estado del tiempo.")
            await self.hub.broadcast(msg_tiempo)
            self.avisos_timer = 1
            return

        # Avisos siguientes piden evaluación al Puntuador
        print("Aviso de timer con evaluación solicitada al Puntuador.")
        await self.hub.broadcast(msg_tiempo)

        instruccion_puntuador = (
            "Ahora que se ha actualizado el tiempo, evalúa brevemente cómo ha evolucionado la conversación.\n\n"
            "Ten en cuenta los siguientes criterios:\n"
            " **Ritmo del debate:** ¿Los participantes intervienen con frecuencia o hay largos periodos sin mensajes?\n"
            " **Calidad y coherencia:** ¿Las respuestas mantienen el hilo del tema y aportan ideas relevantes?\n"
            " **Gestión del tiempo:** ¿El progreso de la conversación es adecuado considerando el tiempo restante en la fase?\n"
            "**Inactividad:** Si notas que no ha habido mensajes recientes o que la sala parece detenida, "
            "refleja eso en una puntuación baja y menciónalo en tu diagnóstico.\n\n"
        )

        msg_instruccion = Msg(
            name="Host",
            role="system",
            content=instruccion_puntuador
        )

        respuesta_puntuador = await self.agentePuntuador(msg_instruccion)
        puntuacion = PuntuacionModel.model_validate_json(respuesta_puntuador.content)

        return {
            "score": puntuacion.score,
            "diagnostico": puntuacion.diagnostico
        }

    
    async def evaluar_intervencion_en_cascada(self,mensaje:Msg):
        await self.hub.broadcast(mensaje)
        curador_msg = await self.agenteCurador(mensaje)
        respuestas = [{
            "agente":"Curador",
            "respuesta":curador_msg.content
        }]
        next_agent = filter_agents(curador_msg.content, self.agentes)
        if next_agent and next_agent[0].name == "Orientador":
            orientador_msg = await self.agenteOrientador()            
            respuestas.append({
                "agente":"Orientador",
                "respuesta":orientador_msg.content
            })
        return respuestas
    
    async def reactiveResponse(self,usuario:str,mensaje:str):
        """
        Funcion que se ejecuta cuando un participante de la sala llama al agente Orientador.
        """
        mensaje = str({
            "contenido":mensaje,
            "timeStamp":datetime.now()
        })
        msgUsuario = Msg(name=usuario,
                         role="user",
                         content=mensaje)
        await self.hub.broadcast(msgUsuario)
        respuesta = await self.agenteOrientador()
        return [{
            "agente":"Orientador",
            "respuesta":respuesta.content
        }]
    
    async def evento_ventana(self):
        """
        Funcion que se ejecuta para pedirle la opinión al Curador si es pertinente o no 
        intervenir en la conversación.
        """
        if not self.hub or self.hub == False: 
            raise RuntimeError("La sesión de chat no ha sido iniciada. Llama a start_session primero.")
        
        mensaje = """
                    Se a cumplido el tamaño de la ventana, por tanto el agente Curador debe decidir si hay que intervenir o no.
                  """
    
        msg = Msg(name="host",
                  role="system",
                  content=mensaje)
        
        respuestas = await self.evaluar_intervencion_en_cascada(msg)
        return respuestas
        

    async def evento_timer(self,puntuacion:int):

        msgSystem = f"""El puntuador a puntuado muy baja la conversacion con {puntuacion} puntos debido a que se le preguntó su opinion 
        luego de una actualizacion del timer.
        El Agente Curador debe decidir si pertinente o no intervenir. 
        """

        msg = Msg(name="host",
                  role="system",
                  content=msgSystem)
        respuestas = await self.evaluar_intervencion_en_cascada(msg)
        return respuestas
    
    async def evento_lowScoreMessage(self, puntuacion:int):
        msgSystem = f"""
        El agente Puntuador ha asignado una puntuación muy baja ({puntuacion} puntos) al mensaje más reciente que ha entrado a la sala. 
        El Agente Curador debe decidir si es pertinente o no intervenir.
        """
        msg = Msg(name="host",
                  role="system",
                  content=msgSystem)
        respuestas = await self.evaluar_intervencion_en_cascada(msg)
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
        

    
