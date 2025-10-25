import asyncio
import os

from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.model import DashScopeChatModel
from agentscope.plan import PlanNotebook, SubTask
from factory_agents import ReActAgentFactory
from agentscope.message import Msg
# 1. Crear el PlanNotebook
plan_notebook = PlanNotebook()

# 2. Definir un plan manualmente
async def create_article_plan():
    await plan_notebook.create_plan(
        name="Escribir artículo de IA",
        description="Preparar un artículo corto sobre aplicaciones de la inteligencia artificial.",
        expected_outcome="Un artículo en formato Markdown con tres secciones: introducción, aplicaciones y conclusión.",
        subtasks=[
            SubTask(
                name="Investigar aplicaciones recientes",
                description="Buscar información sobre aplicaciones de IA en medicina, educación y arte.",
                expected_outcome="Lista de ejemplos recientes en Markdown.",
            ),
            SubTask(
                name="Redactar introducción y aplicaciones",
                description="Escribir una introducción breve y describir las aplicaciones encontradas.",
                expected_outcome="Texto en Markdown con la introducción y aplicaciones.",
            ),
            SubTask(
                name="Escribir conclusión",
                description="Redactar una conclusión sobre el futuro de la IA.",
                expected_outcome="Un párrafo de conclusión en Markdown.",
            ),
        ],
    )

    # Mostrar el plan generado
    msg = await plan_notebook.get_current_hint()

    print(f"{msg.name}: {msg.content}")



async def main():
    factory = ReActAgentFactory()
    await create_article_plan()

    agente = factory.create_agent_with_plan("Frida","Eres un asistem muy servicial llamado Frida",plan_notebook)
    # Crear un mensaje inicial del usuario
    user_msg = Msg("user", "Hola Frida, empecemos con el plan","user")
    respuesta = await agente(user_msg)


factory = ReActAgentFactory()
async def ejecutar_plan(plan_notebook):
    await create_article_plan()
    agente = factory.create_agent_with_plan("Frida","Eres un asistem muy servicial llamado Frida",plan_notebook)
    for idx, subtask in enumerate(plan_notebook.current_plan.subtasks):
        print(f"Ejecutando subtarea: {subtask.name}")
        await plan_notebook.update_subtask_state(subtask_idx=idx, state="in_progress")

        # Aquí decides: o el agente realmente investiga, o simulas
        resultado = await agente(Msg("user", f"Por favor, completa la subtarea: {subtask.description}","system"))
        texto = resultado.get_text_content()
        print("Resultado:\n", resultado.get_text_content())

        await plan_notebook.finish_subtask(
            subtask_idx=idx,
            subtask_outcome=texto)

    # Cuando termines todas:
    await plan_notebook.finish_plan(
        state="finished",
        outcome="Artículo completo generado en Markdown con todas las secciones."
    )
    print("✅ Plan finalizado")


asyncio.run(ejecutar_plan(plan_notebook))