import os
from datetime import datetime
from .factory_agents import ReActAgentFactory
from .base_pipeline import BasePipeline
from agentscope.message import Msg
from agentscope.pipeline import MsgHub
from.utils.utilsForAgents import *
import logging
logger = logging.getLogger("pipeline_toulmin")
class PipelineToulmin(BasePipeline):
    def __init__(self,factory: ReActAgentFactory,
                 prompt_agenteValidador:str,
                 promtp_agenteCurador:str,
                 promt_agenteOrientador:str
                 ):
        super().__init__(timeout=15)
        self.agenteValidador = factory.create_agent(
            name="Validador",
            sys_prompt=prompt_agenteValidador
        )
        self.agenteOrientador = factory.create_agent(
            name="Orientador",
            sys_prompt=promt_agenteOrientador
        )
        self.agenteCurador = factory.create_agent(
            name="Curador",
            sys_prompt=promtp_agenteCurador
        )

        self.agentes = list([self.agenteCurador,self.agenteOrientador])
        self.tema_sala = None

    

    async def start_session(self, tema_sala:str,usuarios_sala:list,idioma:str) -> None:
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
        idioma_prompt = f"""
        El idioma principal de esta conversación es **{idioma}**.
        Por lo tanto:
        1. Todos los análisis lingüísticos y semánticos (incluido el reconocimiento de argumentos según el modelo de Toulmin) deben realizarse en este idioma.
        2. Las respuestas, mensajes y retroalimentaciones generadas por el agente Orientador deben estar redactadas completamente en {idioma}.
        3. No traduzcas ni interpretes al inglés u otros idiomas a menos que el sistema o los participantes lo soliciten explícitamente.
        """
        self.tema_sala = tema_sala
        hint = Msg(
            name="Host",
            role="system",
            content= participantes + idioma_prompt
        )
        participantesMsg = Msg(
            name="Host",
            role="system",
            content=participantes
        )

        self.hub = await MsgHub(participants=self.agentes,announcement=hint).__aenter__()
        respuesta_validador = await self._call_agent(self.agenteValidador,participantesMsg)
        mensaje = Msg(
            name="Host",
            role="system",
            content="La sesión de debate ha comenzado. Orientador por favor da un mensaje de bienvenida y explica el objetivo de la actividad."
        )
        await self._observe_agent(agent=self.agenteValidador,msg=mensaje)   
        await self._broadcast(mensaje)
        respuesta_orientador = await self._call_agent(self.agenteOrientador,mensaje)
        return [{
            "agente":"Orientador",
            "respuesta":respuesta_orientador.content
        }]


    async def stop_session(self) -> None:
        """
        Cierra el MsgHub cuando termina la sesión de chat.
        """
        #tokens_totales = await self.contar_tokens_memoria()
        #print(tokens_totales)
        if self.hub:
            try:
                ruta = f"./logs/conversacion_{self.tema_sala[:100]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                os.makedirs(os.path.dirname(ruta), exist_ok=True)
                self.agentes.append(self.agenteValidador)
                await self.guardar_conversacion_json(ruta)
                print(f"[✅ Conversación exportada antes de cerrar hub]: {ruta}")
            except Exception as e:
                print(f"[❌ Error exportando conversación antes del cierre]: {e}")

            await self.hub.__aexit__(None, None, None)
            self.hub = None
        memoria = await self.show_memory()
        print(memoria)


    async def entrar_mensaje_a_la_sala(self,username:str,mensaje:str):
        username_sanitized = sanitize_name(username)

        msg = Msg(name=username_sanitized,
                  role='user',
                  content=mensaje)
        await self._broadcast(msg)  
        respuesta_validador = await self._call_agent(self.agenteValidador,msg)
        return respuesta_validador.content
        
       

    async def evaluar_intervencion_en_cascada(self):
        print("se llama al Curador")
        msg_curador = Msg(
            name="Host",
            role="system",
            content="Como Curador, evalúa si la sala necesita intervención del agente Orientador o no."
        )
        curador_msg = await self._call_agent(self.agenteCurador,msg_curador)
        print("respuesta del curador obtenida")
        respuestas = [{
            "agente":"Curador",
            "respuesta":curador_msg.content
        }]
        next_agent = filter_agents(curador_msg.content, self.agentes)
        if next_agent and next_agent[0].name == "Orientador":
            orientador_msg = await self._call_agent(self.agenteOrientador)
            await self._observe_agent(agent=self.agenteValidador,msg=orientador_msg)
            respuestas.append({
                "agente":"Orientador",
                "respuesta":orientador_msg.content
            })
        return respuestas
    
    async def reactiveResponse(self,usuario:str,mensaje:str):
        """
        Funcion que se ejecuta cuando un participante de la sala llama al agente Orientador.
        """
        username_sanitized = sanitize_name(usuario)
        msgUsuario = Msg(name=username_sanitized,
                         role="user",
                         content=mensaje)
        await self._broadcast(msgUsuario)
        await self._observe_agent(agent=self.agenteValidador,msg=msgUsuario)
        respuesta = await self._call_agent(self.agenteOrientador,msgUsuario)
        await self._observe_agent(agent=self.agenteValidador,msg=respuesta)

        return [{
            "agente":"Orientador",
            "respuesta":respuesta.content
        }]
    
    async def avisar_tiempo(self, elapsed_time, remaining_time):
        """
        Envía un aviso de tiempo legible para los agentes, informando cuánto ha transcurrido y cuánto queda
        tanto en la fase actual como en la sesión total. En el primer aviso solo informa; en los siguientes,
        también solicita al Puntuador una evaluación.
        """
        if not self.hub:
            print("[Pipeline] Hub no disponible en avisar_tiempo")
            return None
        mensaje_tiempo = (
            f"**Actualización del tiempo**\n"
            f"- Tiempo transcurrido: {formato_tiempo(elapsed_time)}\n"
            f"- Tiempo restante: {formato_tiempo(remaining_time)}\n\n"
        )
        print("ACTUALIZACION DEL TIMER")
        msg_tiempo = Msg(
            name="Timer",
            role="system",
            content=mensaje_tiempo
        )
        print("AVISO TIMER ENVIADO AL HUB")
        try:
            await self._observe_agent(agent=self.agenteOrientador,msg=msg_tiempo)
            await self._observe_agent(agent=self.agenteCurador,msg=msg_tiempo)
        except Exception as e:
            print(f"[Pipeline] Error broadcast msg_tiempo: {e}")
        return None
    
    async def mensaje_hito_temporal(self, hito: int, mensaje_base: str, elapsed_time: int, remaining_time: int):
        """
        Genera un mensaje del Orientador contextualizado para un hito temporal específico.
        
        Args:
            hito: Porcentaje del tiempo completado (25, 50, 75, 100)
            mensaje_base: Mensaje predefinido para este hito
            elapsed_time: Tiempo transcurrido en segundos
            remaining_time: Tiempo restante en segundos
        """
        instruccion = f"""
        **HITO TEMPORAL ALCANZADO: {hito}% del tiempo completado**
        Tiempo transcurrido: {formato_tiempo(elapsed_time)}
        Tiempo restante: {formato_tiempo(remaining_time)}
        {mensaje_base}
        
        Por favor, como Orientador:
        1. Haz una breve reflexión sobre el progreso del debate hasta ahora
        2. Da recomendaciones específicas para aprovechar el tiempo {"restante" if hito < 100 else "que tuvieron"}
        3. Debes ser crítico con el avance. Si no han avanzado lo suficiente, indícaselo a los participantes.
        4. Debes indicarle en que momento de la sesión se encuentran (inicio, mitad, casi finalizado, finalización).
        Tu mensaje debe ser conciso (máximo 3-4 oraciones) y estar en el idioma de la conversación.
        5. Recuerda no empatizar con los alumnos. 
        """

        msg_hito = Msg(
            name="Host",
            role="system",
            content=instruccion
        )

        try:
            # Broadcast del contexto temporal
            await self._broadcast(msg_hito)
            # Solicitar respuesta del Orientador
            respuesta_orientador = await self._call_agent(self.agenteOrientador, msg_hito)
            
            if not respuesta_orientador or not respuesta_orientador.content:
                return [{
                    "agente": "Orientador",
                    "respuesta": mensaje_base  # Fallback al mensaje base
                }]
            
            return [{
                "agente": "Orientador",
                "respuesta": respuesta_orientador.content
            }]
            
        except Exception as e:
            print(f"[Error generando mensaje de hito temporal]: {e}")
            return [{
                "agente": "Orientador",
                "respuesta": mensaje_base
            }]
        
    async def evento_timer(self):
        """
        Intervención por inactividad: el Orientador motiva participación.
        """
        msg = Msg(
            name="Host",
            role="system",
            content=(
                "Se ha detectado inactividad. Orientador: motiva la participación con una pregunta breve, "
                "pide profundizar un punto pendiente y no tomes postura."
            )
        )
        await self._broadcast(msg)
        respuesta_orientador = await self._call_agent(self.agenteOrientador, msg)
        return [{
            "agente": "Orientador",
            "respuesta": (respuesta_orientador.content if respuesta_orientador and respuesta_orientador.content else
                          "Para retomar, ¿qué argumento necesitan desarrollar mejor?")
        }]
    
    
        

    
