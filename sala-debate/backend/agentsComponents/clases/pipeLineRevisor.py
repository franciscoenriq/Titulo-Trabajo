import json
import asyncio
from .factory_agents import ReActAgentFactory
from agentscope.message import Msg
from models.models import get_current_prompts
factory = ReActAgentFactory()

prompt_revisor = """
Eres un agente llamado **Revisor**, experto en el análisis de performance de sistemas multiagente.
Tu tarea es evaluar el desempeño que tuvo cada agente según su rol.

Contexto:
- Este sistema multiagente se utiliza en una sala de chat donde estudiantes debaten temas éticos.
- El objetivo de la sesión es fomentar argumentación clara, colaborativa y bien estructurada.
- Los agentes (Validador, Puntuador, Curador y Orientador) guían y evalúan el debate.

Analiza:
1. Si cada agente cumplió su propósito descrito en su prompt.
2. Cómo fue su comportamiento real (según el registro de mensajes o logs).
3. Si hubo redundancias, errores o intervenciones inadecuadas.
4. Qué podrías mejorar en la coordinación del sistema multiagente.

Tu respuesta debe incluir:
- Evaluación por agente.
- Observaciones generales.
- Sugerencias de mejora.
"""
class PipelineRevisor:
    def __init__(self):
        self.agente_revisor = factory.create_agent(
            name="Revisor",
            sys_prompt=prompt_revisor
        )


    async def evaluar_sesion(self):
        """
        Evalúa la sesión multiagente correspondiente a una sala.
        Recupera prompts, mensajes y genera un informe de performance.
        """
        try:
            #Obtener prompts actuales de cada agente
            prompts = get_current_prompts()
            msg_prompts = Msg(
                name='system',
                role='system',
                content=f"Prompts de los agentes:\n{json.dumps(prompts, indent=2)}")
            await self.agente_revisor.observe(msg_prompts)
            ruta = "../../../logs/conversacion_Discusión sobre cómo la bicicleta puede ayudar a reducir emisiones de carbono._20251106_232711.json"
            with open(ruta, "r", encoding="utf-8") as f:
                log_sesion = json.load(f)
            await self.agente_revisor.observe(Msg(name='system',role='system', content=f"Registro de mensajes de la sesión:\n{json.dumps(log_sesion, indent=2)}"))

            msg = Msg(name='user', role='system',content="Por favor, genera un informe detallado evaluando el desempeño de cada agente según su rol y comportamiento durante la sesión.")
            respuesta = await self.agente_revisor(msg)

            print(respuesta.content)

        except Exception as e:
            print(f"[❌ Error en PipelineRevisor]: {e}")
            return {"error": str(e)}
        


if __name__ == "__main__":
    pipeline_revisor = PipelineRevisor()

    asyncio.run(pipeline_revisor.evaluar_sesion())