import re
from .factory_agents import ReActAgentFactory
from .pipeLine_Nuevo import Pipeline
from .timer1 import Timer

import asyncio
factory = ReActAgentFactory()
import threading
class Intermediario:
    def __init__(self,
                 tamañoVentana:int,
                 prompt_agenteClasificador:str,
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
                                    prompt_agenteClasificador=prompt_agenteClasificador,
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

    async def agregarMensage(self, userName:str, message:str) -> list[dict] | None:
        if self.contiene_mencion_orientador(message):
            respuesta = await self.pipeLine.reactiveResponse(userName,message)
            self.emit_callback('evaluacion',respuesta,self.sala)
            return

        resultado = await self.pipeLine.analizar_mensaje(userName,message)
        if resultado:
            print(f"Enviando score_update a monitor_{self.sala}")
            self.emit_callback('score_update',resultado,f"monitor_{self.sala}")


        self.numeroMensajesTotales += 1 
        print(self.numeroMensajesTotales)
        if (self.numeroMensajesTotales == self.tamañoVentana):
            result = await self.pipeLine.analizar_argumento_cascada()
            self.numeroMensajesTotales = 0
            return result
        else: 
            return 
    
    async def start_session(self,topic:str)->None:
        await self.pipeLine.start_session(topic)

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
        if score < 30:
            respuesta = await  self.pipeLine.timerResponse(score)
            self.emit_callback('evaluacion',respuesta,self.sala)
    def contiene_mencion_orientador(self,mensaje:str) -> bool:
        """
        Detecta si un mensaje contiene la mencion @orientador o similares
        """
        if not isinstance(mensaje,str):
            return False
        patron = r'@orientador\b'
        return re.search(patron,mensaje,re.IGNORECASE) is not None