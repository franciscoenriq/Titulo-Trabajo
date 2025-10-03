import asyncio
import json
from pydantic import BaseModel, Field
from factory_agents import ReActAgentFactory
from agentscope.message import Msg
from typing import Literal

class ToulminModel(BaseModel):
    claim:Literal["Sí","No"] = Field(
        description="La afirmación o conclusión principal que el usuario o grupo defiende."
    )
    data: Literal["Sí","No"] = Field(
        description="Las pruebas, hechos o evidencias que apoyan la afirmación."
    )
    warrant: Literal["Sí","No"] = Field(
        description="La conexión lógica o razonamiento que une los datos con la afirmación."
    ) 
    backing: Literal["Sí","No"] = Field(
        description="El soporte adicional, como teorías, fuentes o principios, que refuerzan la garantía."
    ) 
    qualifier: Literal["Sí","No"] = Field(
        description="El grado de certeza o la fuerza con la que se sostiene la afirmación (ej. probablemente, en la mayoría de los casos)."
    ) 
    reservation: Literal["Sí","No"] = Field(
        description="Las excepciones, limitaciones o posibles contraargumentos que matizan la afirmación."
    )
    coherencia_grupal: Literal["Sí","No"] = Field(
        description="Nivel de coherencia o alineación entre el mensaje evaluado y su relación con el resto de argumentos dentro de la sala (ej. alto, medio, bajo)."
    )
    intervencion_requerida: Literal["Sí","No"] = Field(
        description="Si es necesario que un moderador o facilitador intervenga para resolver contradicciones, falta de claridad o conflictos."
    )

    # en base a que mensaje/s interviene 

query_msg_1 = Msg(
    "user",
    "El cambio climatico es perjudicial para el medio ambiente porque produce aumento en la temperatura de la tierra afectando a todos los ecosistemas que no estan acostumbrados a un cambio brusco de la temperatura.",
    "user",
)

prompt1 = """
Eres un analista de argumentos. Tu tarea es identificar los componentes del modelo de Toulmin presentes mensajes de usuarios que están discutiendo un tema ético.
Para cada uno de estos puntos debes responder 'Sí' o 'No' dependiendo si es que se encuentra la categoria en el mensaje analizado.
El modelo de Toulmin se compone de:
Afirmación (Claim): la conclusión o idea principal.
Datos (Grounds): evidencia o hechos que apoyan la afirmación.
Garantía (Warrant): el razonamiento que conecta los datos con la afirmación.
Respaldo (Backing): justificación adicional, fuentes o principios que refuerzan la garantía.
Calificador (Qualifier): nivel de certeza o fuerza de la afirmación.
Refutación (Rebuttal): excepciones, limitaciones o posibles contraargumentos.
Instrucciones específicas:
1. Analiza el mensaje del usuario.
2. Para cada componente del modelo de toulmin identifica si existe o no ese componente.
3. Si algún componente no aparece, escribe: “No”.
4. No interpretes los argumentos mas allá de lo que dicen.
"""


prompt="""
Eres un analista de argumentos. 
Tu tarea es identificar los componentes del modelo de Toulmin en un mensaje proporcionado por el usuario.

El modelo de Toulmin se compone de:
- Afirmación (Claim): la conclusión o idea principal.
- Datos (Grounds): evidencia o hechos que apoyan la afirmación.
- Garantía (Warrant): el razonamiento que conecta los datos con la afirmación.
- Respaldo (Backing): justificación adicional, fuentes o principios que refuerzan la garantía.
- Calificador (Qualifier): nivel de certeza o fuerza de la afirmación.
- Refutación (Rebuttal): excepciones, limitaciones o posibles contraargumentos.

Instrucciones estrictas:
1. Analiza únicamente el mensaje proporcionado, sin agregar información externa ni inventar detalles.
2. Si un componente no está presente explícitamente en el mensaje, escribe exactamente "No".
3. No interpretes más allá de lo que está dicho; usa solo el contenido del mensaje.

"""


async def main() -> None:
    factory = ReActAgentFactory()
    agente = factory.create_agent(name="evaluador",sys_prompt=prompt1)
    res = await agente(query_msg_1,structured_model=ToulminModel)
    print(
        "Structured Output 2:\n"
        "```\n"
        f"{res.content}\n"
        f"{json.dumps(res.metadata, indent=4, ensure_ascii=False)}\n"
        "```",
    )

asyncio.run(main())