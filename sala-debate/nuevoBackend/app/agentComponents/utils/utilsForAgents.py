import re
import json
import re
from typing import Sequence


def select_next_one(agents: Sequence, rnd: int) -> Sequence:
    """
    Select next agent.
    """
    return agents[rnd % len(agents)]


def filter_agents(string: str, agents: Sequence) -> Sequence:
    if len(agents) == 0:
        return []

    # Crear un diccionario de lookup normalizando nombres a minúsculas
    agent_dict = {agent.name.lower(): agent for agent in agents}

    # Regex: @nombre seguido opcionalmente de ':' o espacio, case-insensitive
    pattern = r"@(" + "|".join(re.escape(agent.name.lower()) for agent in agents) + r")\b"
    matches = re.findall(pattern, string, flags=re.IGNORECASE)

    # Devolver objetos de agente correspondientes
    ordered_agents = [agent_dict[name.lower()] for name in matches if name.lower() in agent_dict]

    return ordered_agents


def sanitize_name(raw: str) -> str:
    if not isinstance(raw, str) or not raw:
        return "user"
    cleaned = re.sub(r'[<|\\/>]', '', raw)      # quitar caracteres prohibidos
    cleaned = re.sub(r'\s+', '_', cleaned)      # espacios -> _
    if cleaned == '':
        cleaned = "user"
    return cleaned



def safe_parse_json(text: str, model_class=None):
    """
    Intenta parsear un texto como JSON robustamente.
    Si model_class se pasa, intenta validarlo con Pydantic.
    """
    if not text or not isinstance(text, str):
        return None

    # 1️⃣ Limpieza inicial
    text = text.strip()

    # 2️⃣ Si es JSON limpio, intenta directamente
    try:
        data = json.loads(text)
        if model_class:
            return model_class.model_validate(data)
        return data
    except json.JSONDecodeError:
        pass

    # 3️⃣ Busca un bloque JSON dentro del texto
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            candidate = match.group()
            data = json.loads(candidate)
            if model_class:
                return model_class.model_validate(data)
            return data
        except Exception:
            pass

    # 4️⃣ Corrige comillas simples → dobles y reintenta
    text_fixed = text.replace("'", '"')
    try:
        data = json.loads(text_fixed)
        if model_class:
            return model_class.model_validate(data)
        return data
    except Exception:
        return None
    

def formato_tiempo(segundos: int) -> str:
        minutos = segundos // 60
        segs = segundos % 60
        partes = []
        if minutos > 0:
            partes.append(f"{minutos} minuto{'s' if minutos != 1 else ''}")
        if segs > 0:
            partes.append(f"{segs} segundo{'s' if segs != 1 else ''}")
        return " y ".join(partes) if partes else "0 segundos"
