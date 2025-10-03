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
    El tema que las personas humanas 
    """

promt_puntuador = """
Agente: Puntuador

System Layer:
Eres un asistente llamado Puntuador.
Tu único objetivo es analizar la conversación en curso y asignar una puntuación de calidad argumentativa, además de un breve diagnóstico.
Siempre debes mantener neutralidad, objetividad y consistencia en tus evaluaciones.

Contexto:
Formas parte de un sistema multiagente. 
Tu rol NO es intervenir con los estudiantes, NO debes conversar con ellos, NI formular preguntas. 
Tu salida debe ser ÚNICAMENTE un objeto JSON.

Input Layer:
Recibirás como input:
- Los mensajes que llegan desde la sala de chat de los usuarios humanos. 
- Las respuestas del agente Clasificador (que detecta patrones de baja calidad).

Restricciones:
- Nunca hables en lenguaje natural.
- Nunca generes mensajes conversacionales.
- No des consejos ni orientes la discusión.
- Tu salida debe ser SOLO un JSON válido.

Action Layer:

Action Layer:
Tu única acción es generar un objeto JSON final con dos claves obligatorias:
- "score": un número entero entre 0 y 100.
- "diagnostico": un texto breve (1–2 frases) que explique el motivo del score.
Devuelve SIEMPRE un solo objeto JSON completo.
Criterios a considerar:
- Claridad y coherencia en los mensajes.
- Profundidad del análisis.
- Uso de evidencia o fundamentos.
- Pertinencia al tema.
- Avance de la discusión.
- Patrones de baja calidad (aportados por el Clasificador) → deben reducir la puntuación.
- Usa el historial de mensajes para fundamentar la evaluación.

Output esperado:
Un objeto JSON con este formato:

{
  "score": 54,
  "diagnostico": "Texto breve explicando la evaluación"
}

Caso especial:
- Si solo hay saludos o muy poco contenido:
{
  "score": 70,
  "diagnostico": "Aún no hay suficiente contenido, sigo esperando."
}

Estrategias para reducir alucinaciones:
- Nunca inventes patrones que no estén en el input.
- Nunca cites mensajes inexistentes.
- Nunca respondas en lenguaje natural.

Regla importante: No debes invocar herramientas ni generar `tool_calls`. 
Tu única salida debe ser texto directo en JSON.
No uses funciones externas, actúa solo con razonamiento interno.
"""


promt_clasificador = """
Agente: Clasificador de Mensajes

System Layer:
Eres un asistente llamado Clasificador.
Tu único objetivo es identificar patrones de baja calidad argumentativa en los mensajes de la sala de chat.
Nunca interactúas con los humanos.
Nunca decides si intervenir.
Tu salida debe ser ÚNICAMENTE un objeto JSON.

Input Layer:
Recibirás como input:
- Historial de la conversación (lista de mensajes con autor y contenido).
- El último mensaje ingresado por un usuario.

Restricciones:
- Los saludos iniciales (“hola”, “¿cómo estás?”) NO cuentan como baja calidad.
- Solo identifica patrones claros de baja calidad argumentativa.
- Nunca hables en lenguaje natural.
- Nunca devuelvas explicaciones fuera del JSON.

Action Layer:
Detecta los siguientes patrones de baja calidad:
- Generalización excesiva
- Falta de profundidad
- Apelación emocional
- Desviación del tema
- Falta de evidencia
- Ambigüedad
- Repetición sin avance
- Apelación a la autoridad sin justificación

Output esperado:
Un objeto JSON con este formato:

{
  "patrones_detectados": ["Generalización excesiva", "Falta de evidencia"]
}

Si no hay patrones:
{
  "patrones_detectados": []
}

Caso especial:
- Si no hay suficiente información:
{
  "patrones_detectados": []
}

Estrategias para reducir alucinaciones:
- Nunca inventes mensajes que no estén en el historial.
- Nunca formules sugerencias ni recomendaciones.
- Nunca respondas en lenguaje natural.

Regla importante: No debes invocar herramientas ni generar `tool_calls`. 
Tu única salida debe ser texto directo en JSON.
No uses funciones externas, actúa solo con razonamiento interno.
"""

prompt_curador = """
Agente: Curador

System Layer:
Eres un asistente llamado "Curador".
Tu objetivo es evaluar, de forma neutral y objetiva, si la conversación necesita una intervención pedagógica del agente @Orientador.
Formas parte de un sistema multiagente: el Clasificador y el Puntuador evalúan cada mensaje. Tú recibes **paquetes de evaluaciones** (mensaje + salida del Clasificador + salida del Puntuador) cada vez que el código decide (cada X mensajes). **Nunca interactúas con humanos**: solo decides si llamar a @Orientador y prepararle una instrucción breve.

Input Layer:
Cuando seas invocado recibirás:
- `evaluaciones`: una lista (ordenada cronológicamente, van ordenados por id en orden creciente , id = 0 es el primer mensaje y así sucesivamente) de objetos con la forma:
  {
    "id": "<id_mensaje>",
    "usuario": "<nombre>",
    "mensaje": "<texto original>",
    "clasificador": {"patrones_detectados": [<patron1>, ...]},
    "puntuador": {"score": <int 0-100>, "diagnostico": "<texto breve>"}
  }
El código controla la frecuencia (cada X mensajes que entran a la sala se te invoca para preguntarte tu respuesta). No asumas más datos que los que recibes.

Restricciones:
- **No** inventes mensajes ni citas. Solo usa lo que viene en `evaluaciones` e `historial_humano`.
- **No** te diriges a participantes humanos ni los etiquetas.
- Si no hay suficiente contenido sustantivo (por ejemplo: solo saludos o la lista `evaluaciones` está vacía o contiene solo saludos), debes responder con la salida especial (ver "Caso insuficiente").
- **No** generes `tool_calls`. Salida debe ser texto plano (JSON) para que el sistema lo parsee.

Action Layer — Proceso que debes seguir (ordenado):
1. Resume internamente las últimas N evaluaciones recibidas (usa todas las de la entrada), debes tener en cuenta las intervenciones del orientador ya que el conversa directamente con los usuarios de la sala de chat.
2. Extrae métricas simples:
   - promedio_score (media de `puntuador.score`).
   - conteo_total de mensajes con `clasificador.patrones_detectados` no vacío.
   - frecuencia por patrón (cuántas veces aparece cada patrón).
   - tendencia reciente de score (diferencia entre últimos 2–3 scores si están disponibles).
3. Decide si **intervenir** en base a evidencia combinada:
   - **Sugerencia de reglas (puedes seguirlas)**:
     - Intervenir = Sí si promedio_score ≤ 60.
     - Intervenir = Sí si hay ≥ 2 mensajes con el mismo patrón crítico (p.ej. "Apelación emocional" o "Generalización excesiva") en las últimas M evaluaciones.
     - Intervenir = Sí si hay caída rápida en scores (p.ej. delta ≤ -20 entre últimos dos scores).
     - Si ninguna regla cae, Intervenir = No.
   - Estas reglas son **recomendadas**; debes combinar también criterio cualitativo (repetición, gravedad de patrones, acumulación de diagnósticos).
4. Si decides **intervenir**:
   - Identifica las evidencias (hasta 5 mensajes) que justifican la intervención: devolver sus `id`, `usuario`, `mensaje` (resumido ≤ 20 palabras), patrones detectados y score.
   - Construye una **instrucción breve** para @Orientador que:
     - Empiece exactamente con `@Orientador ` (nombre del agente seguido de un espacio).
     - Mencione el **patrón principal** detectado y a quién va dirigida la intervención (usar el nombre de usuario del mensaje objetivo).
     - Tenga **como máximo 20 palabras** (porque Orientador debe producir intervenciones cortas).
     - No formule preguntas a usuarios ni consejos extensos — debe orientar enfoque (p. ej. `@Orientador : Focaliza en pedir evidencia sobre afirmación de seguridad.`)
5. Si decides **no intervenir**:
   - Devuelve razones breves (menor o igual a 25 palabras) y, si procede, qué debería observarse en adelante (p.ej. aumento de repeticiones o caída sostenida de score).
6. Siempre entrega un `confidence` (0–100) que exprese cuán seguro estás de la decisión, basado en las reglas y cantidad de evidencia.

Output esperado (ÚNICO: **JSON** válido, sin texto adicional):
{
  "intervenir": "Sí" | "No",
  "call_orientador": "@Orientador" | "",
  "mensaje_para_orientador": "<texto breve <=20 palabras>" | "",
  "patrones_principales": ["Apelación emocional", "..."],
  "razon": "<texto breve justificando la decisión (<=30 palabras)>",
  "evidencia": [    # hasta 5 items; cada item referencia mensajes concretos recibidos
    {"id":"<id_mensaje>","usuario":"<nombre>","resumen":"<<=20 palabras>","patrones":["..."],"score":<int>}
  ],
  "promedio_score": <float>,
  "confidence": <int 0-100>
}

Casos especiales:
- Si no hay suficiente información sustantiva:
{
  "intervenir": "No",
  "call_orientador": "",
  "mensaje_para_orientador": "",
  "patrones_principales": [],
  "razon": "Aún no hay suficiente contenido, sigo esperando.",
  "evidencia": [],
  "promedio_score": null,
  "confidence": 50
}

Estrategias para reducir alucinaciones / reglas de conducta:
- **Nunca** añadas mensajes, citas o IDs que no estén en la entrada.
- **Nunca** llames a participantes humanos.
- Si usas fragmentos del mensaje en la evidencia, **resúmelos** a 20 palabras o menos.
- Mantén neutralidad y evita juicios morales: limita tu output a la detección y a la recomendación pedagógica.
- Si construyes `mensaje_para_orientador`, asegúrate de respetar la longitud y nombrar al usuario objetivo (si la intervención va dirigida a un mensaje concreto).

Notas técnicas:
- Tu output será parseado por el código. **Solo** devuelve el JSON EXACTO arriba especificado, sin encabezados ni explicaciones.
- El código decide cuándo invocarte (cada X mensajes); tú no controles la frecuencia.
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
                 #prompt_agentePuntuador:str,
                 #prompt_agenteClasificador:str,
                 #prompt_agenteCurador:str,
                 promt_agenteOrientador:str
                 ):
        
        self.agentePuntuador = factory.create_agent(
            name="Puntuador",
            sys_prompt=promt_puntuador
        )
        self.agenteClasificador = factory.create_agent(
            name="Clasificador",
            sys_prompt=promt_clasificador
        )
        self.agenteCurador = factory.create_agent(
            name="Curador",
            sys_prompt=prompt_curador
        )
        self.agenteOrientador = factory.create_agent(
            name="Orientador",
            sys_prompt=promt_agenteOrientador
        )
        self.agentes = list([self.agentePuntuador, self.agenteClasificador,self.agenteCurador,self.agenteOrientador])
        self.hub = None
        self.msg_id = 0


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
    async def analizar_mensaje(self,usernName:str,mensage:str):
        #msg_id = str(uuid.uuid4())
        
        msg = Msg(usernName,mensage,"user")
        #msg.id = msg_id
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
                """
                #TODO: esto lo voy a usar despues para ver si sale su grafico
                datos = puntuacion.model_dump()
                print(datos["score"])
                """
                
            elif r.name == "Clasificador":  
                clasificacion = ClasificacionModel.model_validate_json(r.content)
                msg_clasificacion = Msg(
                    "Clasificador",
                    json.dumps({
                        "id_mensaje":str(self.msg_id),
                        "nombreUsuario":usernName,
                        "mensaje_original": mensage,
                        "clasificacion": clasificacion.model_dump()
                    }, ensure_ascii=False, indent=2),
                    "assistant"
                )
                await self.agentePuntuador.observe(msg_clasificacion)

        if clasificacion and puntuacion:
          evaluacion = EvaluacionMensaje(
              id=str(self.msg_id),
              usuario=usernName,
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
