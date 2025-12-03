import asyncio
import logging
import json
from abc import ABC, abstractmethod
from agentscope.message import Msg
from datetime import datetime
logger = logging.getLogger("base_pipeline")


class BasePipeline(ABC):
    """
    Clase base abstracta para pipelines con agentes.
    Encapsula:
    - Locks
    - Timeout
    - Métodos protegidos de llamado, observe y broadcast
    """

    def __init__(self, timeout: int = 15):
        self._timeout = timeout

        # Locks independientes
        self._lock_call = asyncio.Lock()
        self._lock_observe = asyncio.Lock()
        self._lock_broadcast = asyncio.Lock()

        # Hub (puede inicializarse en la clase hija)
        self.hub = None

    # -----------------------------------------------------------------------
    # MÉTODO PROTEGIDO: CALL AGENT
    # -----------------------------------------------------------------------
    async def _call_agent(self, agent, msg: Msg | None = None):
        try:
            async with self._lock_call:
                return await asyncio.wait_for(
                    agent(msg) if msg else agent(),
                    timeout=self._timeout
                )
        except asyncio.TimeoutError:
            logger.warning(f"[Timeout] agente={agent.name}")
            return None
        except Exception as e:
            logger.error(f"[Error LLM] agente={agent.name} err={e}")
            return None

    # -----------------------------------------------------------------------
    # MÉTODO PROTEGIDO: OBSERVE
    # -----------------------------------------------------------------------
    async def _observe_agent(self, agent, msg: Msg) -> bool:
        if not agent:
            logger.warning("[Observe] agente None")
            return False

        try:
            async with self._lock_observe:
                await asyncio.wait_for(agent.observe(msg), timeout=self._timeout)
            return True

        except asyncio.TimeoutError:
            logger.warning(f"[Observe timeout] agente={agent.name}")
            return False

        except Exception as e:
            logger.error(f"[Observe error] agente={agent.name} err={e}")
            return False

    # -----------------------------------------------------------------------
    # MÉTODO PROTEGIDO: BROADCAST
    # -----------------------------------------------------------------------
    async def _broadcast(self, msg: Msg) -> bool:
        if not self.hub:
            logger.warning("[Broadcast] Hub no inicializado")
            return False

        try:
            async with self._lock_broadcast:
                await self.hub.broadcast(msg)
            return True

        except Exception as e:
            logger.error(f"[Broadcast error]: {e}")
            return False
    
    async def show_memory(self) -> dict:
        """
        Retorna la memoria de los agentes como texto legible, estructurando los mensajes para análisis de un nuevo agente.
        """
        def serialize_msg_content(msg):
            """
            Convierte el contenido de un mensaje a texto legible.
            """
            content_texts = []
            if isinstance(msg.content, str):
                content_texts.append(msg.content)
            elif isinstance(msg.content, list):
                # lista de tool_use/tool_result
                for block in msg.content:
                    if isinstance(block, dict):
                        if block.get("type") == "tool_use":
                            response = block.get("input", {}).get("response")
                            if response:
                                content_texts.append(f"[TOOL_USE]\n{response}")
                        elif block.get("type") == "tool_result":
                            output_blocks = block.get("output", [])
                            for ob in output_blocks:
                                if ob.get("type") == "text":
                                    content_texts.append(f"[TOOL_RESULT]\n{ob.get('text')}")
            else:
                try:
                    # Intentamos serializar JSON si es BaseModel o dict
                    content_texts.append(json.dumps(msg.content, indent=2, ensure_ascii=False))
                except:
                    content_texts.append(str(msg.content))
            return "\n".join(content_texts)

        memoria_total = {}
        for agente in self.agentes:
            memoria_agente = []
            mensajes_historial = await agente.memory.get_memory()
            for idx, msg in enumerate(mensajes_historial, start=1):
                timestamp = getattr(msg, "timestamp", "")
                role = getattr(msg, "role", "unknown")
                author = getattr(msg, "author", agente.name)
                content = serialize_msg_content(msg)
                memoria_agente.append(
                    f"--- Mensaje {idx} ---\n"
                    f"Timestamp: {timestamp}\n"
                    f"Rol: {role}\n"
                    f"Autor: {author}\n"
                    f"Contenido:\n{content}\n"
                )
            memoria_total[agente.name] = memoria_agente
        return memoria_total
    

    async def exportar_conversacion_completa(self) -> dict:
        """
        Devuelve la conversación completa (mensajes humanos + agentes)
        en formato estructurado y cronológico
        """
        if not self.hub:
            raise RuntimeError("No hay sesión activa para exportar.")

        registro = {
            "tema": getattr(self, "tema_sala", ""),
            "timestamp_exportacion": datetime.now().isoformat(),
            "mensajes": []
        }

        #  Recuperar los mensajes históricos del hub (orden cronológico real)
        if hasattr(self.hub, "history"):
            for msg in self.hub.history:
                registro["mensajes"].append({
                    "timestamp": getattr(msg, "timestamp", None),
                    "autor": getattr(msg, "name", "Desconocido"),
                    "rol": getattr(msg, "role", "unknown"),
                    "contenido": str(msg.content),
                    "tipo": "hub_message"
                })

        #  Agregar la memoria interna de los agentes
        memoria = await self.show_memory()
        for agente, mensajes in memoria.items():
            for idx, msg_texto in enumerate(mensajes, start=1):
                registro["mensajes"].append({
                    "timestamp": None,
                    "autor": agente,
                    "rol": "agent_memory",
                    "contenido": msg_texto,
                    "tipo": "memoria_agente",
                    "orden_memoria": idx
                })

        #  Ordenar por timestamp si existe
        registro["mensajes"].sort(key=lambda m: m.get("timestamp") or "", reverse=False)

        return registro

    async def guardar_conversacion_json(self, ruta_archivo: str) -> str:
        """
        Guarda la conversación exportada como archivo JSON ordenado.
        """
        datos = await self.exportar_conversacion_completa()
        with open(ruta_archivo, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        return ruta_archivo
