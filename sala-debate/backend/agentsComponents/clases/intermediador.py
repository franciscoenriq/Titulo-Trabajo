import re
from .factory_agents import ReActAgentFactory
from .pipeline import Pipeline
from .timer import Timer
from models.models import *
import asyncio
factory = ReActAgentFactory()
import threading
class Intermediario:
    def __init__(self,
                 tamañoVentana:int,
                 prompt_agentePuntuador:str,
                 prompt_agenteCurador:str,
                 prompt_agenteOrientador:str,
                 socketIo,
                 sala:str,
                 emit_callback):
        self.tamañoVentana = tamañoVentana
        self.mensajesTotales = []
        self.numeroMensajesTotales = 0
        self.pipeLine = Pipeline(factory=factory,
                                    prompt_agentePuntuador=prompt_agentePuntuador,
                                    prompt_agenteCurador=prompt_agenteCurador,
                                    promt_agenteOrientador=prompt_agenteOrientador
                                    )
        self.emit_callback = emit_callback
        self.timer = Timer()

        self.timer.callback = self.callback
        self.socketIo = socketIo
        self.sala = sala
        self.message_queue = asyncio.Queue()
        self.processing_task = None
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self._run_event_loop,daemon=True).start()

    def _run_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()


    def start_processing(self):
        if not self.processing_task:
            self.processing_task = asyncio.run_coroutine_threadsafe(self._process_messages(), self.loop)

    async def _process_messages(self):
        while True:
            username, message = await self.message_queue.get()
            try:
                resultado = await self.agregarMensage(username, message)
                if resultado:
                    self.emit_callback('evaluacion',resultado,self.sala)
            except Exception as e:
                print(f"Error procesando mensaje: {e}")
            finally:
                self.message_queue.task_done()

    def enqueue_message(self, username: str, message: str):
        """Permite encolar mensajes desde hilos externos (por ejemplo, el socket)."""
        asyncio.run_coroutine_threadsafe(
            self.message_queue.put((username, message)),
            self.loop
        )
        
    def get_timer_state(self):
        """Devuelve el estado actual del timer, o valores iniciales si aún no se ha iniciado."""
        try:
            state = self.timer.get_state()
            if not state or state["fase_actual"] == 0:
                # Estado inicial por defecto
                return {
                    "fase_actual": 1,
                    "elapsed_phase": 0,
                    "remaining_phase": 0,
                    "remaining_total": 0,
                    "elapsed_total": 0,
                }
            return state
        except Exception as e:
            print(f"Error al obtener estado del timer: {e}")
            return {
                "fase_actual": 1,
                "elapsed_phase": 0,
                "remaining_phase": 0,
                "remaining_total": 0,
                "elapsed_total": 0,
            }


    async def agregarMensage(self, userName:str, message:str) -> list[dict] | None:
        """
        Este es el punto en que entra cada mensaje al pipeline de agentes. 
        Primero que todo se comprueba si el mensaje contiene la fras @orientador.
        Ya que el sistema responde si es que alguien lo llama. 
        Luego se analiza el mensaje por dos agentes, el puntuador y el clasificador. 
        De aca se desprenden dos maneras en que se activará la respuesta del curador 
        - A traves del cumplimiento del tamaño de la ventana.
        - Cuando el puntaje para un mensaje es demasiado bajo. 
        """
        curador_invocado = False
        if self.contiene_mencion_orientador(message):
            respuesta = await self.pipeLine.reactiveResponse(userName,message)
            id_room_session = get_active_room_session_id(self.sala)
            # respuesta es una lista → tomamos el primer elemento
            if isinstance(respuesta, list) and len(respuesta) > 0:
                contenido = respuesta[0].get("respuesta", "")
            else:
                contenido = str(respuesta)
            insert_message(
                room_session_id=id_room_session,
                user_id=None,
                agent_name="Orientador",
                sender_type=SenderType.agent,
                content=contenido
            )
            self.emit_callback('evaluacion',respuesta,self.sala)
            return

        resultado = await self.pipeLine.entrar_mensaje_a_la_sala(username=userName,mensaje=message)
        if resultado:
            print(f"Enviando score_update a monitor_{self.sala}")
            self.emit_callback('score_update',resultado,f"monitor_{self.sala}")
            score = int(resultado["score"])
            curador_invocado=await self.evaluacion_score(score,'mensaje')
  
        self.numeroMensajesTotales += 1 
        print(self.numeroMensajesTotales)
        #Verificamos si el evento ventana se invoca o no. 
        if (self.numeroMensajesTotales == self.tamañoVentana and not curador_invocado):
            result = await self.pipeLine.evento_ventana()
            self.numeroMensajesTotales = 0
            return result
        elif self.numeroMensajesTotales == self.tamañoVentana:
            self.numeroMensajesTotales=0
    
    async def start_session(self,topic:str,usuarios_sala:list)->None:
        respuesta = await self.pipeLine.start_session(topic,usuarios_sala)
        id_room_session = get_active_room_session_id(self.sala)
        # respuesta es una lista → tomamos el primer elemento
        if isinstance(respuesta, list) and len(respuesta) > 0:
            contenido = respuesta[0].get("respuesta", "")
        else:
            contenido = str(respuesta)
        insert_message(
            room_session_id=id_room_session,
            user_id=None,
            agent_name="Orientador",
            sender_type=SenderType.agent,
            content=contenido
        )
        self.emit_callback('evaluacion',respuesta,self.sala)

    async def stop_session(self):
        await self.pipeLine.stop_session()

    async def anunciar_entrada_participante(self,userName:str) -> None:
        await self.pipeLine.anunciar_entrada_participante(userName)

    async def anunciar_salida_participante(self,userName:str) -> None:
        await self.pipeLine.anunciar_salida_participante(userName)
    
    def start_timer(self, phases: list[int], update_interval: int):
        self.timer.start(phases)
        self.timer.start_periodic(update_interval)

    async def callback(self, fase_actual, remaining_phase, elapsed_phase, remaining_total, elapsed_total):
        """
        callback que se ejecuta cada vez que el timer avisa el tiempo que ha durado la sala. 
        La informacion respecto al tiempo es emitida a la sala, mientras que el score producido por el agente 
        es analizado con self.evaluacion_score()
        """
        respuesta_puntuador = await self.pipeLine.avisar_tiempo(fase_actual, remaining_phase, elapsed_phase, remaining_total, elapsed_total)
        dataToSala = {
            "fase_actual":fase_actual,
            "elapsed_phase":elapsed_phase,
            "remaining_phase":remaining_phase
        }
        if respuesta_puntuador == None: 
            self.emit_callback('timer_user_update',dataToSala,self.sala)
            return
        data = {
            "fase_actual":fase_actual,
            "remaining_phase":remaining_phase,
            "elapsed_phase":elapsed_phase,
            "remaining_total": remaining_total,
            "elapsed_total": elapsed_total,
            "score": respuesta_puntuador["score"],
            "diagnostico": respuesta_puntuador["diagnostico"]
        }
        self.emit_callback('timer_user_update',dataToSala,self.sala)
        self.emit_callback('timer_update',data,f"monitor_{self.sala}")

        score = int(respuesta_puntuador["score"])
        await self.evaluacion_score(score,'timer')
                
    def contiene_mencion_orientador(self,mensaje:str) -> bool:
        """
        Detecta si un mensaje contiene la mencion @orientador o similares
        """
        if not isinstance(mensaje,str):
            return False
        patron = r'@orientador\b'
        return re.search(patron,mensaje,re.IGNORECASE) is not None
    
    async def evaluacion_score(self, score:int, origen:str):
        """
        Evalua si el curador debe dar su opinión respecto a intervenir o no en la conversación. 
        Esta funcion será llamada cuando ocurra un evento de baja puntuacion. a su vez la puntuacion será 
        hecha debido a un evento de mensaje, que es cuando el puntuador puntua un mensaje con bajo score 
        y cuando puntua bajo debido a un mensaje del timer. 
        - origen: "mensaje", " timer" . mensaje hace referencia a si 
        """
        umbral = 30 
        if score >= umbral:
            return False
        if origen == 'timer':
            respuesta = await self.pipeLine.evento_timer(score)
            if respuesta:
                self.emit_callback('evaluacion',respuesta,self.sala)
                return True
        if origen == 'mensaje':
            respuesta=await self.pipeLine.evento_lowScoreMessage(score)
            if respuesta:
                self.emit_callback('evaluacion',respuesta,self.sala)
                return True
            
        # Normalizamos: puede ser una lista o un solo objeto
        respuestas = respuesta if isinstance(respuesta, list) else [respuesta]
        id_room_session = get_active_room_session_id(self.sala)
        for r in respuestas:
            # Extraemos rol y contenido según formato
            rol = getattr(r, "role", None) or getattr(r, "agente", None) or "Orientador"
            content = getattr(r, "content", None)
            
            # Guardamos solo si el mensaje es del Orientador
            if rol.lower() == "orientador" and content:
                insert_message(
                    room_session_id=id_room_session,
                    user_id=None,
                    agent_name="Orientador",
                    sender_type=SenderType.agent,
                    content=content
                )
                self.emit_callback("evaluacion", r, self.sala)
                return True
        return False