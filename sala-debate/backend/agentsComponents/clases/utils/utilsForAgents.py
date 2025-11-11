import re
import json

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
